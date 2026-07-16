from __future__ import annotations

import base64
import json
import math
import re
import zlib
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Sequence

from .sparc_discourse import (
    DiscourseDocument,
    DiscourseNode,
    SPARCHS9Model,
    SparseDiscourseGraph,
    _anchors,
    _normalise,
    _role,
    _sentences,
)
from .sparc_language import ReplyResult

ROLES = (
    "claim",
    "evidence",
    "example",
    "counter",
    "concession",
    "conclusion",
    "detail",
)

_BOOTSTRAP_PREFIXES = (
    "したがって",
    "以上から",
    "よって",
    "結論として",
    "ゆえに",
    "なぜなら",
    "その理由は",
    "理由は",
    "根拠として",
    "例えば",
    "具体的には",
    "一例として",
    "しかし",
    "一方で",
    "一方",
    "これに対して",
    "反対に",
    "ただし",
    "確かに",
    "もちろん",
)
_BOOTSTRAP_SUFFIXES = (
    "と考える",
    "と主張する",
)


def _remove_bootstrap_cues(sentence: str) -> str:
    text = _normalise(sentence).lstrip("「『")
    changed = True
    while changed:
        changed = False
        for prefix in _BOOTSTRAP_PREFIXES:
            if text.startswith(prefix):
                text = text[len(prefix) :].lstrip("、。:：")
                changed = True
                break
    for suffix in _BOOTSTRAP_SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
    return text or _normalise(sentence)


def _features(sentence: str, position: int, total: int) -> tuple[str, ...]:
    text = _remove_bootstrap_cues(sentence).strip("。！？")
    output: set[str] = set()
    for size in (2, 3):
        for index in range(max(0, len(text) - size + 1)):
            piece = text[index : index + size]
            if piece and not piece.isdigit():
                output.add(f"N{size}:{piece}")
    for size in (2, 3, 4, 5, 6):
        if len(text) >= size:
            output.add(f"S{size}:{text[-size:]}")
    output.add(f"L:{min(12, len(text) // 8)}")
    output.add("P:first" if position == 0 else "P:not-first")
    output.add("P:last" if position == total - 1 else "P:not-last")
    if total > 1:
        output.add(f"P:q{min(3, int(position * 4 / total))}")
    output.add(f"T:{min(8, total)}")
    if "が" in text:
        output.add("G:ga")
    if "を" in text:
        output.add("G:wo")
    if "べき" in text or "必要" in text or "重要" in text:
        output.add("G:normative")
    if "懸念" in text or "問題" in text or "反対" in text:
        output.add("G:risk")
    if "調査" in text or "観測" in text or "データ" in text:
        output.add("G:empirical")
    return tuple(sorted(output))


class SparseRoleInducer:
    """Weakly supervised sparse role prototypes plus learned transition structure."""

    def __init__(self) -> None:
        self.role_features: dict[str, Counter[str]] = {
            role: Counter() for role in ROLES
        }
        self.role_counts: Counter[str] = Counter()
        self.feature_roles: dict[str, set[str]] = defaultdict(set)
        self.transitions: dict[str, Counter[str]] = {
            role: Counter() for role in ROLES
        }
        self.starts: Counter[str] = Counter()
        self.ends: Counter[str] = Counter()
        self.documents_seen = 0
        self.last_role_candidates = 0
        self.last_feature_reads = 0
        self.last_transition_reads = 0

    def fit_document(self, text: str) -> tuple[str, ...]:
        sentences = _sentences(text)
        labels = tuple(_role(sentence) for sentence in sentences)
        if not sentences:
            return ()
        self.documents_seen += 1
        self.starts[labels[0]] += 1
        self.ends[labels[-1]] += 1
        previous: str | None = None
        for position, (sentence, label) in enumerate(zip(sentences, labels)):
            self.role_counts[label] += 1
            for feature in _features(sentence, position, len(sentences)):
                self.role_features[label][feature] += 1
                self.feature_roles[feature].add(label)
            if previous is not None:
                self.transitions[previous][label] += 1
            previous = label
        return labels

    def fit(self, documents: Iterable[str]) -> int:
        count = 0
        for document in documents:
            if self.fit_document(document):
                count += 1
        return count

    def _local_score(self, role: str, features: Sequence[str]) -> float:
        prior = math.log1p(self.role_counts[role])
        score = 0.35 * prior
        counts = self.role_features[role]
        for feature in features:
            value = counts.get(feature, 0)
            if value:
                inverse_roles = 1.0 / max(1, len(self.feature_roles[feature]))
                score += math.log1p(value) * inverse_roles
        return score

    def _transition_score(self, previous: str, current: str) -> float:
        row = self.transitions[previous]
        total = sum(row.values())
        return math.log((row[current] + 0.25) / (total + 0.25 * len(ROLES)))

    def predict(self, text: str) -> tuple[str, ...]:
        sentences = _sentences(text)
        if not sentences:
            return ()
        feature_rows = [
            _features(sentence, position, len(sentences))
            for position, sentence in enumerate(sentences)
        ]
        self.last_role_candidates = len(ROLES)
        self.last_feature_reads = sum(len(row) * len(ROLES) for row in feature_rows)
        self.last_transition_reads = max(0, len(sentences) - 1) * len(ROLES) ** 2

        scores: list[dict[str, float]] = []
        back: list[dict[str, str | None]] = []
        first_scores: dict[str, float] = {}
        first_back: dict[str, str | None] = {}
        start_total = sum(self.starts.values())
        for role in ROLES:
            start = math.log(
                (self.starts[role] + 0.25)
                / (start_total + 0.25 * len(ROLES))
            )
            first_scores[role] = self._local_score(role, feature_rows[0]) + start
            first_back[role] = None
        scores.append(first_scores)
        back.append(first_back)

        for position in range(1, len(sentences)):
            current_scores: dict[str, float] = {}
            current_back: dict[str, str | None] = {}
            for role in ROLES:
                local = self._local_score(role, feature_rows[position])
                previous, value = max(
                    (
                        previous,
                        scores[-1][previous]
                        + self._transition_score(previous, role)
                        + local,
                    )
                    for previous in ROLES
                )
                current_scores[role] = value
                current_back[role] = previous
            scores.append(current_scores)
            back.append(current_back)

        end_total = sum(self.ends.values())
        final_role = max(
            ROLES,
            key=lambda role: scores[-1][role]
            + math.log(
                (self.ends[role] + 0.25)
                / (end_total + 0.25 * len(ROLES))
            ),
        )
        output = [final_role]
        for position in range(len(sentences) - 1, 0, -1):
            previous = back[position][output[-1]]
            assert previous is not None
            output.append(previous)
        output.reverse()
        return tuple(output)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-role-inducer-hs10",
            "role_features": {
                role: dict(counts) for role, counts in self.role_features.items()
            },
            "role_counts": dict(self.role_counts),
            "transitions": {
                role: dict(counts) for role, counts in self.transitions.items()
            },
            "starts": dict(self.starts),
            "ends": dict(self.ends),
            "documents_seen": self.documents_seen,
        }
        return zlib.compress(
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseRoleInducer":
        payload = json.loads(zlib.decompress(data))
        model = cls()
        model.role_counts.update(payload["role_counts"])
        model.starts.update(payload["starts"])
        model.ends.update(payload["ends"])
        model.documents_seen = int(payload["documents_seen"])
        for role, rows in payload["role_features"].items():
            model.role_features[role].update(rows)
            for feature in rows:
                model.feature_roles[feature].add(role)
        for role, rows in payload["transitions"].items():
            model.transitions[role].update(rows)
        return model

    def report(self) -> dict[str, int | bool]:
        return {
            "documents_seen": self.documents_seen,
            "stored_feature_weights": sum(
                len(counts) for counts in self.role_features.values()
            ),
            "stored_transition_weights": sum(
                len(counts) for counts in self.transitions.values()
            ),
            "serialized_bytes": len(self.to_bytes()),
            "last_role_candidates": self.last_role_candidates,
            "last_feature_reads": self.last_feature_reads,
            "last_transition_reads": self.last_transition_reads,
            "cue_words_removed_before_learning": True,
            "corpus_scan_used_at_inference": False,
        }


class InducedDiscourseGraph(SparseDiscourseGraph):
    def __init__(
        self,
        inducer: SparseRoleInducer | None = None,
        *,
        max_documents: int = 100_000,
        max_candidates: int = 24,
        read_budget: int = 192,
        workspace_documents: int = 8,
    ) -> None:
        super().__init__(
            max_documents=max_documents,
            max_candidates=max_candidates,
            read_budget=read_budget,
            workspace_documents=workspace_documents,
        )
        self.inducer = inducer or SparseRoleInducer()

    def ingest_induced(self, text: str, *, source_id: str, title: str = "") -> int:
        if len(self.documents) >= self.max_documents:
            raise MemoryError("discourse document capacity reached")
        sentences = _sentences(text)
        roles = self.inducer.predict(text)
        if len(sentences) != len(roles):
            raise ValueError("role induction length mismatch")
        document_id = len(self.documents)
        title = title or source_id
        node_ids: list[int] = []
        last_claim: int | None = None
        recent_support: list[int] = []
        for position, (sentence, role) in enumerate(zip(sentences, roles)):
            node_id = len(self.nodes)
            self.nodes.append(
                DiscourseNode(document_id, str(source_id), position, sentence, role)
            )
            node_ids.append(node_id)
            self.role_nodes[document_id][role].append(node_id)
            if role == "claim":
                last_claim = node_id
                recent_support.clear()
            elif role in {"evidence", "example"} and last_claim is not None:
                self._add_edge(
                    node_id,
                    last_claim,
                    "supports" if role == "evidence" else "exemplifies",
                )
                recent_support.append(node_id)
            elif role == "counter" and last_claim is not None:
                self._add_edge(node_id, last_claim, "opposes")
            elif role == "concession" and last_claim is not None:
                self._add_edge(node_id, last_claim, "qualifies")
            elif role == "detail" and last_claim is not None:
                self._add_edge(node_id, last_claim, "elaborates")
            elif role == "conclusion":
                if last_claim is not None:
                    self._add_edge(last_claim, node_id, "develops")
                for support in recent_support[-4:]:
                    self._add_edge(support, node_id, "supports")
                last_claim = node_id
                recent_support.clear()
        self.documents.append(
            DiscourseDocument(str(source_id), title, tuple(node_ids))
        )
        for anchor in _anchors(title + source_id + text):
            self.postings[anchor].add(document_id)
        self.workspace.append(document_id)
        return document_id

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-induced-discourse-hs10",
            "graph": base64.b85encode(super().to_bytes()).decode("ascii"),
            "inducer": base64.b85encode(self.inducer.to_bytes()).decode("ascii"),
        }
        return zlib.compress(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "InducedDiscourseGraph":
        payload = json.loads(zlib.decompress(data))
        base = SparseDiscourseGraph.from_bytes(base64.b85decode(payload["graph"]))
        graph = cls(
            SparseRoleInducer.from_bytes(base64.b85decode(payload["inducer"])),
            max_documents=base.max_documents,
            max_candidates=base.max_candidates,
            read_budget=base.read_budget,
            workspace_documents=base.workspace.maxlen or 8,
        )
        graph.__dict__.update(base.__dict__)
        graph.inducer = SparseRoleInducer.from_bytes(
            base64.b85decode(payload["inducer"])
        )
        return graph


class SPARCHS10Model:
    def __init__(self, base: SPARCHS9Model | None = None) -> None:
        self.base = base or SPARCHS9Model()
        self.learned_discourse = InducedDiscourseGraph()

    def fit_role_documents(self, documents: Iterable[str]) -> int:
        return self.learned_discourse.inducer.fit(documents)

    def ingest_learned_discourse(
        self, text: str, *, source_id: str, title: str = ""
    ) -> int:
        return self.learned_discourse.ingest_induced(
            text, source_id=source_id, title=title
        )

    def reply(self, text: str) -> ReplyResult:
        learned = self.learned_discourse.answer(text)
        if learned is not None and learned.confidence >= 0.35:
            return learned
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs10",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "learned": base64.b85encode(self.learned_discourse.to_bytes()).decode(
                "ascii"
            ),
        }
        return zlib.compress(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS10Model":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS9Model.from_bytes(base64.b85decode(payload["base"])))
        model.learned_discourse = InducedDiscourseGraph.from_bytes(
            base64.b85decode(payload["learned"])
        )
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS10Model":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "stage": "SPARC-HS10",
            "base": self.base.report(),
            "learned_discourse": self.learned_discourse.report(),
            "role_inducer": self.learned_discourse.inducer.report(),
            "serialized_bytes": len(self.to_bytes()),
            "transformer_used": False,
            "growing_kv_cache_used": False,
        }
