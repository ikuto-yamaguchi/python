from __future__ import annotations

import base64
import json
import math
import re
import zlib
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from .sparc_episodic import SPARCHS8Model, _anchors, _split_sentences
from .sparc_language import ReplyResult


@dataclass(frozen=True)
class ParagraphFrame:
    source_id: str
    paragraph_id: str
    text: str
    episode_ids: tuple[int, ...]


@dataclass(frozen=True)
class ArgumentFrame:
    source_id: str
    claim: str
    reason: str
    evidence: str


def _clean_marker(sentence: str, markers: tuple[str, ...]) -> str | None:
    clean = sentence.strip().strip("。！？")
    for marker in markers:
        if clean.startswith(marker):
            value = clean[len(marker) :].lstrip("は:：、 ")
            return value or None
    return None


def _argument_frame(text: str, source_id: str) -> ArgumentFrame | None:
    claim = reason = evidence = None
    for sentence in _split_sentences(text):
        claim = claim or _clean_marker(sentence, ("主張", "結論"))
        reason = reason or _clean_marker(sentence, ("理由", "なぜなら"))
        evidence = evidence or _clean_marker(sentence, ("根拠", "証拠"))
    if claim and reason and evidence:
        return ArgumentFrame(source_id, claim, reason, evidence)
    return None


class SparseAbstractionMemory:
    """Local paragraph retrieval plus repeated-relation abstraction nodes."""

    def __init__(
        self,
        *,
        max_paragraphs: int = 150_000,
        max_candidates: int = 16,
        read_budget: int = 128,
    ) -> None:
        self.max_paragraphs = max_paragraphs
        self.max_candidates = max_candidates
        self.read_budget = read_budget
        self.paragraphs: list[ParagraphFrame] = []
        self.postings: dict[str, set[int]] = defaultdict(set)
        self.subject_claims: dict[str, list[int]] = defaultdict(list)
        self.abstraction_episodes: dict[str, list[int]] = defaultdict(list)
        self.arguments: dict[str, list[ArgumentFrame]] = defaultdict(list)
        self.last_candidates = 0
        self.last_anchor_reads = 0
        self.last_estimated_operations = 0
        self.last_scores: dict[int, float] = {}

    def register_paragraph(
        self,
        *,
        source_id: str,
        paragraph_id: str,
        text: str,
        episode_ids: tuple[int, ...],
        base: SPARCHS8Model,
    ) -> int:
        if len(self.paragraphs) >= self.max_paragraphs:
            raise MemoryError("paragraph abstraction capacity reached")
        frame_id = len(self.paragraphs)
        frame = ParagraphFrame(str(source_id), str(paragraph_id), text, episode_ids)
        self.paragraphs.append(frame)
        for anchor in _anchors(text):
            self.postings[anchor].add(frame_id)
        for episode_id in episode_ids:
            episode = base.episodic.episodes[episode_id]
            if episode.claim_subject:
                self.subject_claims[episode.claim_subject].append(episode_id)
            if episode.claim_relation and episode.claim_value:
                key = f"{episode.claim_relation}\u241f{episode.claim_value}"
                self.abstraction_episodes[key].append(episode_id)
        argument = _argument_frame(text, str(source_id))
        if argument is not None:
            self.arguments[str(source_id)].append(argument)
        return frame_id

    def _candidate_ids(self, topic: str) -> list[int]:
        routes = sorted(
            (
                len(self.postings.get(anchor, ())),
                -len(anchor),
                anchor,
            )
            for anchor in _anchors(topic)
            if self.postings.get(anchor)
        )
        votes: Counter[int] = Counter()
        reads = 0
        used = 0
        for posting_size, negative_length, anchor in routes:
            if votes and posting_size > self.max_candidates * 8:
                break
            weight = (-negative_length) ** 2 / max(1, posting_size)
            for paragraph_id in self.postings[anchor]:
                votes[paragraph_id] += weight
                reads += 1
                if reads >= self.read_budget:
                    break
            used += 1
            if reads >= self.read_budget or used >= 10 or len(votes) >= self.max_candidates * 2:
                break
        ranked = votes.most_common(self.max_candidates)
        self.last_scores = dict(ranked)
        self.last_candidates = len(ranked)
        self.last_anchor_reads = reads
        self.last_estimated_operations = len(_anchors(topic)) + reads + 2 * len(ranked)
        return [paragraph_id for paragraph_id, _score in ranked]

    @staticmethod
    def _active_episode_ids(base: SPARCHS8Model, episode_ids: list[int]) -> list[int]:
        return [
            episode_id
            for episode_id in episode_ids
            if episode_id < len(base.episodic.episodes)
            and base.episodic.episodes[episode_id].active
        ]

    def summarize(self, topic: str, *, base: SPARCHS8Model) -> ReplyResult | None:
        paragraph_ids = self._candidate_ids(topic)
        if not paragraph_ids:
            return None
        episode_ids: list[int] = []
        source_ids: list[str] = []
        for paragraph_id in paragraph_ids:
            frame = self.paragraphs[paragraph_id]
            episode_ids.extend(frame.episode_ids)
            if frame.source_id not in source_ids:
                source_ids.append(frame.source_id)
        active = self._active_episode_ids(base, episode_ids)
        if not active:
            return None

        selected_texts: list[str] = []
        used_ids: list[int] = []
        relevant_keys: Counter[str] = Counter()
        for episode_id in active:
            episode = base.episodic.episodes[episode_id]
            if episode.claim_relation and episode.claim_value:
                relevant_keys[f"{episode.claim_relation}\u241f{episode.claim_value}"] += 1

        for key, _local_support in relevant_keys.most_common():
            global_ids = self._active_episode_ids(base, self.abstraction_episodes[key])
            subjects: list[str] = []
            for episode_id in global_ids:
                subject = base.episodic.episodes[episode_id].claim_subject
                if subject and subject not in subjects:
                    subjects.append(subject)
                if len(subjects) >= 4:
                    break
            if len(subjects) < 2:
                continue
            relation, value = key.split("\u241f", 1)
            if relation == "属性":
                selected_texts.append(f"{'・'.join(subjects)}は共通して{value}。")
            else:
                selected_texts.append(
                    f"{'・'.join(subjects)}では、{relation}が共通して{value}。"
                )
            used_ids.extend(global_ids[: min(4, len(global_ids))])
            if len(selected_texts) >= 2:
                break

        if len(selected_texts) < 3:
            ranked = sorted(
                active,
                key=lambda episode_id: (
                    topic in base.episodic.episodes[episode_id].sentence,
                    base.episodic.episodes[episode_id].causal,
                    base.episodic.episodes[episode_id].revision,
                    base.episodic.episodes[episode_id].timestamp,
                ),
                reverse=True,
            )
            for episode_id in ranked:
                sentence = base.episodic.episodes[episode_id].sentence
                if sentence in selected_texts:
                    continue
                selected_texts.append(sentence)
                used_ids.append(episode_id)
                if len(selected_texts) >= 3:
                    break

        sources = "、".join(f"［{source}］" for source in source_ids[:6])
        text = f"{topic}の要約: " + " ".join(selected_texts) + f" 根拠: {sources}"
        return ReplyResult(
            text=text,
            confidence=min(0.94, 0.68 + 0.04 * len(selected_texts)),
            mechanism="sparse-relational-abstraction-summary",
            candidates_inspected=self.last_candidates,
            active_bits=min(len(set(used_ids)), 16),
            estimated_sparse_operations=self.last_estimated_operations + len(active),
        )

    def _relation_map(self, subject: str, *, base: SPARCHS8Model) -> dict[str, set[str]]:
        mapping: dict[str, set[str]] = defaultdict(set)
        for episode_id in self.subject_claims.get(subject, ()):
            episode = base.episodic.episodes[episode_id]
            if episode.active and episode.claim_relation and episode.claim_value:
                mapping[episode.claim_relation].add(episode.claim_value)
        return mapping

    def compare(self, left: str, right: str, *, base: SPARCHS8Model) -> ReplyResult | None:
        left_map = self._relation_map(left, base=base)
        right_map = self._relation_map(right, base=base)
        if not left_map or not right_map:
            return None
        common: list[str] = []
        differences: list[str] = []
        for relation in sorted(set(left_map) | set(right_map)):
            left_values = left_map.get(relation, set())
            right_values = right_map.get(relation, set())
            shared = sorted(left_values & right_values)
            if shared:
                common.append(f"{relation}={','.join(shared)}")
            if left_values != right_values:
                differences.append(
                    f"{relation}: {left}={','.join(sorted(left_values)) or '記述なし'}、"
                    f"{right}={','.join(sorted(right_values)) or '記述なし'}"
                )
        source_ids: list[str] = []
        local_ids = list(self.subject_claims.get(left, ())) + list(self.subject_claims.get(right, ()))
        for episode_id in local_ids:
            source = base.episodic.episodes[episode_id].source_id
            if source not in source_ids:
                source_ids.append(source)
        text = (
            f"{left}と{right}の比較。共通点: "
            + ("；".join(common) if common else "明示された共通属性はありません")
            + "。相違点: "
            + ("；".join(differences) if differences else "明示された相違はありません")
            + "。根拠: "
            + "、".join(f"［{source}］" for source in source_ids[:8])
        )
        operations = len(local_ids) + len(left_map) + len(right_map)
        self.last_candidates = min(2, self.max_candidates)
        self.last_anchor_reads = 0
        self.last_estimated_operations = operations
        return ReplyResult(
            text=text,
            confidence=0.82,
            mechanism="local-relation-alignment-comparison",
            candidates_inspected=self.last_candidates,
            active_bits=min(operations, 16),
            estimated_sparse_operations=operations,
        )

    def argument(self, source_id: str) -> ReplyResult | None:
        frames = self.arguments.get(source_id, ())
        if not frames:
            return None
        frame = frames[-1]
        text = (
            f"［{source_id}］の主張は「{frame.claim}」、理由は「{frame.reason}」、"
            f"根拠は「{frame.evidence}」です。"
        )
        self.last_candidates = 1
        self.last_anchor_reads = 0
        self.last_estimated_operations = 3
        return ReplyResult(
            text=text,
            confidence=0.90,
            mechanism="explicit-argument-frame",
            candidates_inspected=1,
            active_bits=3,
            estimated_sparse_operations=3,
        )

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-abstraction-hs9",
            "max_paragraphs": self.max_paragraphs,
            "max_candidates": self.max_candidates,
            "read_budget": self.read_budget,
            "paragraphs": [asdict(frame) for frame in self.paragraphs],
            "arguments": {
                source: [asdict(frame) for frame in frames]
                for source, frames in self.arguments.items()
            },
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        *,
        base: SPARCHS8Model,
    ) -> "SparseAbstractionMemory":
        payload = json.loads(zlib.decompress(data))
        memory = cls(
            max_paragraphs=int(payload["max_paragraphs"]),
            max_candidates=int(payload["max_candidates"]),
            read_budget=int(payload["read_budget"]),
        )
        for row in payload["paragraphs"]:
            memory.register_paragraph(
                source_id=str(row["source_id"]),
                paragraph_id=str(row["paragraph_id"]),
                text=str(row["text"]),
                episode_ids=tuple(int(item) for item in row["episode_ids"]),
                base=base,
            )
        return memory

    def report(self) -> dict[str, int | bool]:
        return {
            "paragraphs": len(self.paragraphs),
            "posting_edges": sum(len(items) for items in self.postings.values()),
            "subjects": len(self.subject_claims),
            "abstraction_nodes": len(self.abstraction_episodes),
            "argument_frames": sum(len(items) for items in self.arguments.values()),
            "serialized_bytes": len(self.to_bytes()),
            "last_candidates": self.last_candidates,
            "last_anchor_reads": self.last_anchor_reads,
            "last_estimated_operations": self.last_estimated_operations,
            "full_history_scan_used": False,
            "softmax_attention_used": False,
        }


class SPARCHS9Model:
    def __init__(self, base: SPARCHS8Model | None = None) -> None:
        self.base = base or SPARCHS8Model()
        self.abstraction = SparseAbstractionMemory()

    def ingest_document(self, text: str, *, source_id: str) -> tuple[int, ...]:
        paragraphs = tuple(
            piece.strip()
            for piece in re.split(r"\n\s*\n+", text)
            if piece.strip()
        ) or (text.strip(),)
        inserted: list[int] = []
        for index, paragraph in enumerate(paragraphs):
            episode_ids = self.base.ingest(paragraph, source_id=source_id)
            inserted.append(
                self.abstraction.register_paragraph(
                    source_id=source_id,
                    paragraph_id=f"{source_id}:{index}",
                    text=paragraph,
                    episode_ids=episode_ids,
                    base=self.base,
                )
            )
        return tuple(inserted)

    def revise(self, text: str, *, source_id: str) -> tuple[int, ...]:
        episode_ids = self.base.revise(text, source_id=source_id)
        self.abstraction.register_paragraph(
            source_id=source_id,
            paragraph_id=f"{source_id}:revision:{len(self.abstraction.paragraphs)}",
            text=text,
            episode_ids=episode_ids,
            base=self.base,
        )
        return episode_ids

    def reply(self, text: str) -> ReplyResult:
        compare = re.search(
            r"(.{1,40}?)と(.{1,40}?)(?:を比較|の比較|の共通点|の違い)",
            text,
        )
        if compare:
            result = self.abstraction.compare(
                compare.group(1).strip("「」『』 、"),
                compare.group(2).strip("「」『』 、を"),
                base=self.base,
            )
            if result is not None:
                return result
        summary = re.search(r"(.{1,60}?)(?:について要約|を要約|についてまとめ|をまとめ)", text)
        if summary:
            result = self.abstraction.summarize(
                summary.group(1).strip("「」『』 、"),
                base=self.base,
            )
            if result is not None:
                return result
        argument = re.search(r"(.{1,60}?)(?:の主張と根拠|の論旨)", text)
        if argument:
            result = self.abstraction.argument(argument.group(1).strip("「」『』 、"))
            if result is not None:
                return result
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs9",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "abstraction": base64.b85encode(self.abstraction.to_bytes()).decode("ascii"),
        }
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS9Model":
        payload = json.loads(zlib.decompress(data))
        base = SPARCHS8Model.from_bytes(base64.b85decode(payload["base"]))
        model = cls(base)
        model.abstraction = SparseAbstractionMemory.from_bytes(
            base64.b85decode(payload["abstraction"]),
            base=base,
        )
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS9Model":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "stage": "SPARC-HS9",
            "base": self.base.report(),
            "abstraction": self.abstraction.report(),
            "serialized_bytes": len(self.to_bytes()),
            "full_history_attention_used": False,
            "growing_kv_cache_used": False,
        }
