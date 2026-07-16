from __future__ import annotations

import base64
import json
import math
import zlib
from pathlib import Path

from .sparc_discourse import (
    DiscourseDocument,
    DiscourseNode,
    SPARCHS9Model,
    SparseDiscourseGraph,
    _anchors,
    _normalise,
    _sentences,
)
from .sparc_role_induction import (
    ROLES,
    InducedDiscourseGraph,
    SPARCHS10Model,
    SparseRoleInducer,
    _features,
)


class SparseRoleInducerV2(SparseRoleInducer):
    """Correct score-directed Viterbi decoding for sparse role prototypes."""

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
        self.exact_titles: dict[str, int] = {}

    @staticmethod
    def _selected_anchors(title: str, source_id: str, text: str) -> set[str]:
        essential = _anchors(title + source_id)
        content = sorted(_anchors(text), key=lambda value: (-len(value), value))[:96]
        return essential | set(content)

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
        self.exact_titles[_normalise(title)] = document_id
        for anchor in self._selected_anchors(title, str(source_id), text):
            self.postings[anchor].add(document_id)
        self.workspace.append(document_id)
        return document_id

    def _candidate_documents(self, query: str) -> list[int]:
        compact = _normalise(query)
        exact = [
            (len(title), document_id)
            for title, document_id in self.exact_titles.items()
            if title and title in compact
        ]
        if exact:
            length, document_id = max(exact)
            self.last_scores = {document_id: float(length)}
            self.last_candidates = 1
            self.last_anchor_reads = 0
            return [document_id]
        return super()._candidate_documents(query)

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
        graph.incoming_edges = base.incoming_edges
        graph.outgoing_edges = base.outgoing_edges
        graph.role_nodes = base.role_nodes
        graph.workspace = base.workspace
        for document_id, document in enumerate(graph.documents):
            graph.exact_titles[_normalise(document.title)] = document_id
            text = "".join(graph.nodes[node_id].text for node_id in document.node_ids)
            for anchor in graph._selected_anchors(
                document.title, document.source_id, text
            ):
                graph.postings[anchor].add(document_id)
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
