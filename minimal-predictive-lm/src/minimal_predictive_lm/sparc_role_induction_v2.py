from __future__ import annotations

import base64
import json
import math
import zlib
from pathlib import Path

from .sparc_discourse import SPARCHS9Model, SparseDiscourseGraph, _sentences
from .sparc_role_induction import (
    ROLES,
    InducedDiscourseGraph,
    SPARCHS10Model,
    SparseRoleInducer,
    _features,
)


class SparseRoleInducerV2(SparseRoleInducer):
    """Correct score-directed Viterbi decoding for the HS10 sparse prototypes."""

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
        start_total = sum(self.starts.values())
        first_scores: dict[str, float] = {}
        for role in ROLES:
            start = math.log(
                (self.starts[role] + 0.25)
                / (start_total + 0.25 * len(ROLES))
            )
            first_scores[role] = self._local_score(role, feature_rows[0]) + start
        scores.append(first_scores)
        back.append({role: None for role in ROLES})

        for position in range(1, len(sentences)):
            current_scores: dict[str, float] = {}
            current_back: dict[str, str | None] = {}
            for role in ROLES:
                local = self._local_score(role, feature_rows[position])
                previous, value = max(
                    (
                        (
                            previous_role,
                            scores[-1][previous_role]
                            + self._transition_score(previous_role, role)
                            + local,
                        )
                        for previous_role in ROLES
                    ),
                    key=lambda row: row[1],
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


class InducedDiscourseGraphV2(InducedDiscourseGraph):
    def __init__(
        self,
        inducer: SparseRoleInducerV2 | None = None,
        *,
        max_documents: int = 100_000,
        max_candidates: int = 24,
        read_budget: int = 192,
        workspace_documents: int = 8,
    ) -> None:
        super().__init__(
            inducer or SparseRoleInducerV2(),
            max_documents=max_documents,
            max_candidates=max_candidates,
            read_budget=read_budget,
            workspace_documents=workspace_documents,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "InducedDiscourseGraphV2":
        payload = json.loads(zlib.decompress(data))
        base = SparseDiscourseGraph.from_bytes(base64.b85decode(payload["graph"]))
        inducer = SparseRoleInducerV2.from_bytes(
            base64.b85decode(payload["inducer"])
        )
        graph = cls(
            inducer,
            max_documents=base.max_documents,
            max_candidates=base.max_candidates,
            read_budget=base.read_budget,
            workspace_documents=base.workspace.maxlen or 8,
        )
        graph.documents = base.documents
        graph.nodes = base.nodes
        graph.edges = base.edges
        graph.postings = base.postings
        graph.incoming_edges = base.incoming_edges
        graph.outgoing_edges = base.outgoing_edges
        graph.role_nodes = base.role_nodes
        graph.workspace = base.workspace
        return graph


class SPARCHS10ModelV2(SPARCHS10Model):
    def __init__(self, base: SPARCHS9Model | None = None) -> None:
        self.base = base or SPARCHS9Model()
        self.learned_discourse = InducedDiscourseGraphV2()

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS10ModelV2":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS9Model.from_bytes(base64.b85decode(payload["base"])))
        model.learned_discourse = InducedDiscourseGraphV2.from_bytes(
            base64.b85decode(payload["learned"])
        )
        return model

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS10ModelV2":
        return cls.from_bytes(Path(path).read_bytes())
