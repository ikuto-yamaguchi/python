from __future__ import annotations

import base64
import json
import math
import re
import zlib
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from .sparc_language import ReplyResult
from .sparc_units import SPARCHS7Model


def _normalise(text: str) -> str:
    text = text.strip().replace("?", "？").replace("!", "！")
    return re.sub(r"\s+", "", text)


def _split_sentences(text: str) -> tuple[str, ...]:
    pieces = re.split(r"(?<=[。！？])|\n+", text)
    return tuple(piece.strip() for piece in pieces if piece.strip())


_PUNCT_RE = re.compile(r"[。、！？「」『』（）()\[\]\s]")
_QUESTION_WORDS = (
    "どこ",
    "何",
    "誰",
    "いつ",
    "なぜ",
    "どうして",
    "どれ",
    "理由",
    "説明",
    "教えて",
)
_REVISION_MARKERS = ("訂正", "最新情報", "現在", "実は", "更新")


def _anchors(text: str) -> set[str]:
    compact = _PUNCT_RE.sub("", _normalise(text))
    anchors: set[str] = set()
    for size in (2, 3, 4, 5):
        for index in range(max(0, len(compact) - size + 1)):
            piece = compact[index : index + size]
            if not piece or piece.isdigit():
                continue
            anchors.add(piece)
    return anchors


def _strip_predicate_end(value: str) -> str:
    value = value.strip("。！？ ")
    return re.sub(
        r"(?:である|です|だ|だった|となった|になった|にある|にいる)$",
        "",
        value,
    )


@dataclass(frozen=True)
class ParsedClaim:
    subject: str
    relation: str
    value: str
    causal: bool = False

    @property
    def key(self) -> str:
        return f"{self.subject}\u241f{self.relation}"


def _parse_claim(sentence: str) -> ParsedClaim | None:
    clean = _normalise(sentence).strip("。！？")
    clean = re.sub(
        r"^(?:訂正[:：]?|最新情報[:：]?|現在[:：]?|実は[:：]?|更新[:：]?)",
        "",
        clean,
    )
    causal_patterns = (
        r"^(.{1,80}?)(?:のため|ため|なので|ので|によって|により)(.{1,100})$",
        r"^(.{1,80}?)は(.{1,80}?)(?:を引き起こす|を生じさせる|の原因になる)$",
    )
    for pattern in causal_patterns:
        match = re.match(pattern, clean)
        if match:
            return ParsedClaim(
                _strip_predicate_end(match.group(1)),
                "原因",
                _strip_predicate_end(match.group(2)),
                True,
            )

    match = re.match(r"^(.{1,50}?)の(.{1,24}?)は(.{1,120})$", clean)
    if match:
        return ParsedClaim(
            match.group(1),
            match.group(2),
            _strip_predicate_end(match.group(3)),
        )

    match = re.match(r"^(.{1,60}?)は(.{1,120})$", clean)
    if match:
        return ParsedClaim(
            match.group(1),
            "属性",
            _strip_predicate_end(match.group(2)),
        )
    return None


@dataclass
class Episode:
    source_id: str
    sentence: str
    timestamp: int
    active: bool = True
    revision: bool = False
    claim_key: str | None = None
    claim_value: str | None = None
    claim_subject: str | None = None
    claim_relation: str | None = None
    causal: bool = False


class SparseEpisodicRevisionMemory:
    """Bounded episodic memory with local inverted-index retrieval and revision.

    Global capacity and query activity are separated: adding episodes grows only
    postings and compressed records. A query reads a small number of rare-anchor
    postings and never scans the complete episode list.
    """

    def __init__(
        self,
        *,
        max_episodes: int = 250_000,
        max_candidates: int = 32,
        read_budget: int = 192,
        workspace_size: int = 32,
    ) -> None:
        self.max_episodes = max_episodes
        self.max_candidates = max_candidates
        self.read_budget = read_budget
        self.workspace_size = workspace_size
        self.episodes: list[Episode] = []
        self.postings: dict[str, set[int]] = defaultdict(set)
        self.claims: dict[str, list[int]] = defaultdict(list)
        self.causal_out: dict[str, set[int]] = defaultdict(set)
        self.causal_in: dict[str, set[int]] = defaultdict(set)
        self.workspace: deque[int] = deque(maxlen=workspace_size)
        self.focus_terms: deque[str] = deque(maxlen=8)
        self.last_candidates = 0
        self.last_anchor_reads = 0
        self.last_estimated_operations = 0
        self.last_scores: dict[int, float] = {}
        self.conflict_events = 0
        self.revision_events = 0

    def reset_workspace(self) -> None:
        self.workspace.clear()
        self.focus_terms.clear()

    def _register_episode(self, episode: Episode) -> int:
        if len(self.episodes) >= self.max_episodes:
            raise MemoryError("episodic capacity reached")
        episode_id = len(self.episodes)
        episode.timestamp = episode_id
        self.episodes.append(episode)
        for anchor in _anchors(episode.sentence):
            self.postings[anchor].add(episode_id)
        if episode.claim_key is not None:
            active_previous = [
                item
                for item in self.claims[episode.claim_key]
                if self.episodes[item].active
            ]
            conflicting = [
                item
                for item in active_previous
                if self.episodes[item].claim_value != episode.claim_value
            ]
            if conflicting:
                if episode.revision:
                    for item in conflicting:
                        self.episodes[item].active = False
                    self.revision_events += 1
                else:
                    self.conflict_events += 1
            self.claims[episode.claim_key].append(episode_id)
            if episode.causal and episode.claim_subject and episode.claim_value:
                self.causal_out[episode.claim_subject].add(episode_id)
                self.causal_in[episode.claim_value].add(episode_id)
        return episode_id

    def ingest(
        self,
        text: str,
        *,
        source_id: str,
        revision: bool = False,
    ) -> tuple[int, ...]:
        revision = revision or any(marker in text for marker in _REVISION_MARKERS)
        inserted: list[int] = []
        for sentence in _split_sentences(text):
            claim = _parse_claim(sentence)
            episode = Episode(
                source_id=str(source_id),
                sentence=sentence,
                timestamp=len(self.episodes),
                revision=revision,
                claim_key=claim.key if claim else None,
                claim_value=claim.value if claim else None,
                claim_subject=claim.subject if claim else None,
                claim_relation=claim.relation if claim else None,
                causal=claim.causal if claim else False,
            )
            inserted.append(self._register_episode(episode))
        return tuple(inserted)

    def revise(self, text: str, *, source_id: str) -> tuple[int, ...]:
        return self.ingest(text, source_id=source_id, revision=True)

    def _expanded_query(self, query: str) -> str:
        if re.search(r"(?:それ|そのこと|このこと|先ほどの内容)", query):
            if self.workspace:
                recent = self.episodes[self.workspace[-1]]
                focus = recent.claim_subject or ""
                value = recent.claim_value or recent.sentence
                return query + focus + value
            if self.focus_terms:
                return query + self.focus_terms[-1]
        return query

    def _candidate_ids(self, query: str) -> list[int]:
        query = self._expanded_query(query)
        query_anchors = _anchors(query)
        routes = sorted(
            (
                len(self.postings.get(anchor, ())),
                -len(anchor),
                anchor,
            )
            for anchor in query_anchors
            if self.postings.get(anchor)
        )
        votes: Counter[int] = Counter()
        reads = 0
        routes_used = 0
        for posting_size, negative_length, anchor in routes:
            if votes and posting_size > self.max_candidates * 8:
                break
            weight = (-negative_length) ** 2 / max(1, posting_size)
            for episode_id in self.postings[anchor]:
                votes[episode_id] += weight
                reads += 1
                if reads >= self.read_budget:
                    break
            routes_used += 1
            if (
                reads >= self.read_budget
                or routes_used >= 12
                or len(votes) >= self.max_candidates * 2
            ):
                break
        ranked = votes.most_common(self.max_candidates)
        self.last_scores = dict(ranked)
        self.last_candidates = len(ranked)
        self.last_anchor_reads = reads
        self.last_estimated_operations = (
            len(query_anchors) + reads + len(ranked) * 2
        )
        return [episode_id for episode_id, _score in ranked]

    def _active_claim_versions(self, key: str) -> list[int]:
        return [
            episode_id
            for episode_id in self.claims.get(key, ())
            if self.episodes[episode_id].active
        ]

    def _causal_chain(
        self,
        query: str,
        candidates: Sequence[int],
        *,
        max_hops: int = 4,
        max_nodes: int = 32,
    ) -> list[int]:
        seed_ids = [
            episode_id
            for episode_id in candidates
            if self.episodes[episode_id].causal
            and self.episodes[episode_id].active
        ]
        if not seed_ids:
            return []
        best_seed = max(
            seed_ids,
            key=lambda item: (
                self.last_scores.get(item, 0.0),
                self.episodes[item].timestamp,
            ),
        )
        chain = [best_seed]
        visited = {best_seed}
        current = self.episodes[best_seed]
        for _ in range(max_hops - 1):
            if not current.claim_subject:
                break
            previous = [
                item
                for item in self.causal_in.get(current.claim_subject, ())
                if self.episodes[item].active and item not in visited
            ]
            if not previous:
                break
            chosen = max(previous, key=lambda item: self.episodes[item].timestamp)
            chain.insert(0, chosen)
            visited.add(chosen)
            current = self.episodes[chosen]
            if len(visited) >= max_nodes:
                break
        return chain

    def answer(self, query: str) -> ReplyResult | None:
        candidates = self._candidate_ids(query)
        active = [
            episode_id
            for episode_id in candidates
            if self.episodes[episode_id].active
        ]
        if not active:
            return None
        active.sort(
            key=lambda item: (
                self.last_scores.get(item, 0.0),
                self.episodes[item].timestamp,
            ),
            reverse=True,
        )
        best_id = active[0]
        best = self.episodes[best_id]

        used: list[int]
        mechanism: str
        confidence: float
        if "なぜ" in query or "どうして" in query or "理由" in query:
            chain = self._causal_chain(query, active)
            if chain:
                used = chain
                evidence = " → ".join(
                    self.episodes[item].sentence for item in chain
                )
                sources = "、".join(
                    f"［{self.episodes[item].source_id}］" for item in chain
                )
                text = (
                    f"{evidence} したがって、この因果経路で説明できます。"
                    f"根拠: {sources}"
                )
                mechanism = "bounded-causal-episodic-chain"
                confidence = min(0.96, 0.70 + 0.06 * len(chain))
            else:
                used = active[: min(3, len(active))]
                text = " ".join(
                    self.episodes[item].sentence for item in reversed(used)
                )
                text += " 根拠: " + "、".join(
                    f"［{self.episodes[item].source_id}］" for item in used
                )
                mechanism = "sparse-episodic-retrieval"
                confidence = 0.68
        elif best.claim_key is not None:
            versions = self._active_claim_versions(best.claim_key)
            values = {self.episodes[item].claim_value for item in versions}
            if len(values) > 1:
                used = versions[-4:]
                descriptions = "、".join(
                    f"{self.episodes[item].claim_value}"
                    f"（{self.episodes[item].source_id}）"
                    for item in used
                )
                text = (
                    "資料間に未解決の矛盾があります。"
                    f"現在有効な記述は{descriptions}です。"
                )
                mechanism = "episodic-conflict-detection"
                confidence = 0.50
            else:
                used = [best_id]
                if any(word in query for word in _QUESTION_WORDS):
                    text = (
                        f"{best.claim_value}です。"
                        f"根拠: {best.sentence}［{best.source_id}］"
                    )
                else:
                    text = f"{best.sentence} 出典: ［{best.source_id}］"
                mechanism = "sparse-episodic-claim"
                confidence = min(
                    0.98,
                    0.70
                    + 0.04 * math.log2(1 + max(1, len(versions)))
                    + (0.05 if best.revision else 0.0),
                )
        else:
            used = active[: min(3, len(active))]
            text = " ".join(
                self.episodes[item].sentence for item in reversed(used)
            )
            text += " 出典: " + "、".join(
                f"［{self.episodes[item].source_id}］" for item in used
            )
            mechanism = "sparse-episodic-retrieval"
            confidence = 0.65

        self.workspace.extend(used)
        for episode_id in used:
            episode = self.episodes[episode_id]
            if episode.claim_subject:
                self.focus_terms.append(episode.claim_subject)
        return ReplyResult(
            text=text,
            confidence=confidence,
            mechanism=mechanism,
            candidates_inspected=self.last_candidates,
            active_bits=len(used),
            estimated_sparse_operations=self.last_estimated_operations
            + len(used),
        )

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-episodic-hs8",
            "max_episodes": self.max_episodes,
            "max_candidates": self.max_candidates,
            "read_budget": self.read_budget,
            "workspace_size": self.workspace_size,
            "episodes": [asdict(episode) for episode in self.episodes],
            "conflict_events": self.conflict_events,
            "revision_events": self.revision_events,
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseEpisodicRevisionMemory":
        payload = json.loads(zlib.decompress(data))
        memory = cls(
            max_episodes=int(payload["max_episodes"]),
            max_candidates=int(payload["max_candidates"]),
            read_budget=int(payload["read_budget"]),
            workspace_size=int(payload["workspace_size"]),
        )
        for row in payload["episodes"]:
            memory._register_episode(
                Episode(
                    source_id=str(row["source_id"]),
                    sentence=str(row["sentence"]),
                    timestamp=int(row["timestamp"]),
                    active=bool(row["active"]),
                    revision=bool(row["revision"]),
                    claim_key=row["claim_key"],
                    claim_value=row["claim_value"],
                    claim_subject=row["claim_subject"],
                    claim_relation=row["claim_relation"],
                    causal=bool(row["causal"]),
                )
            )
        memory.conflict_events = int(payload["conflict_events"])
        memory.revision_events = int(payload["revision_events"])
        return memory

    def report(self) -> dict[str, int | bool]:
        posting_edges = sum(len(items) for items in self.postings.values())
        active_claims = sum(
            1
            for episode in self.episodes
            if episode.active and episode.claim_key is not None
        )
        return {
            "episodes": len(self.episodes),
            "posting_edges": posting_edges,
            "claim_keys": len(self.claims),
            "active_claims": active_claims,
            "conflict_events": self.conflict_events,
            "revision_events": self.revision_events,
            "serialized_bytes": len(self.to_bytes()),
            "last_candidates": self.last_candidates,
            "last_anchor_reads": self.last_anchor_reads,
            "last_estimated_operations": self.last_estimated_operations,
            "full_history_scan_used": False,
            "growing_kv_cache_used": False,
            "softmax_attention_used": False,
        }


class SPARCHS8Model:
    def __init__(self, base: SPARCHS7Model | None = None) -> None:
        self.base = base or SPARCHS7Model()
        self.episodic = SparseEpisodicRevisionMemory()

    def ingest(
        self,
        text: str,
        *,
        source_id: str,
        revision: bool = False,
    ) -> tuple[int, ...]:
        return self.episodic.ingest(
            text,
            source_id=source_id,
            revision=revision,
        )

    def revise(self, text: str, *, source_id: str) -> tuple[int, ...]:
        return self.episodic.revise(text, source_id=source_id)

    def reset_workspace(self) -> None:
        self.episodic.reset_workspace()

    def reply(self, text: str) -> ReplyResult:
        result = self.episodic.answer(text)
        if result is not None and result.confidence >= 0.48:
            return result
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs8",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "episodic": base64.b85encode(self.episodic.to_bytes()).decode("ascii"),
        }
        raw = json.dumps(
            payload,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS8Model":
        payload = json.loads(zlib.decompress(data))
        model = cls(
            SPARCHS7Model.from_bytes(base64.b85decode(payload["base"]))
        )
        model.episodic = SparseEpisodicRevisionMemory.from_bytes(
            base64.b85decode(payload["episodic"])
        )
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS8Model":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "stage": "SPARC-HS8",
            "base": self.base.report(),
            "episodic": self.episodic.report(),
            "serialized_bytes": len(self.to_bytes()),
            "full_history_attention_used": False,
            "growing_kv_cache_used": False,
        }
