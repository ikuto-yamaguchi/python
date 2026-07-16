from __future__ import annotations

import base64
import hashlib
import json
import re
import zlib
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

from .sparc_discourse import (
    DiscourseDocument,
    DiscourseNode,
    SparseDiscourseGraph,
    _anchors,
    _role,
    _sentences,
)
from .sparc_episodic import SPARCHS8Model
from .sparc_language import ReplyResult


def _normalise_title(text: str) -> str:
    return re.sub(r"[\s。、！？「」『』（）()]", "", text)


def _stable_rank(value: str) -> int:
    return int.from_bytes(
        hashlib.blake2b(value.encode("utf-8"), digest_size=8).digest(),
        "little",
    )


def _routing_anchors(
    title: str,
    source_id: str,
    text: str,
    *,
    limit: int = 96,
) -> set[str]:
    preferred = _anchors(title + source_id)
    role_priority: list[str] = []
    remaining: list[str] = []
    for sentence in _sentences(text):
        if _role(sentence) in {"claim", "conclusion", "evidence", "counter"}:
            role_priority.append(sentence)
        else:
            remaining.append(sentence)
    ranked: list[str] = []
    seen: set[str] = set()
    for group in (preferred, _anchors("".join(role_priority)), _anchors("".join(remaining))):
        for anchor in sorted(group, key=lambda item: (-len(item), _stable_rank(item))):
            if anchor in seen:
                continue
            seen.add(anchor)
            ranked.append(anchor)
            if len(ranked) >= limit:
                return set(ranked)
    return set(ranked)


class CompactSparseDiscourseGraph(SparseDiscourseGraph):
    """HS9 graph with exact-title routing and a bounded sparse anchor index."""

    def __init__(
        self,
        *,
        max_documents: int = 100_000,
        max_candidates: int = 24,
        read_budget: int = 192,
        workspace_documents: int = 8,
        anchors_per_document: int = 96,
    ) -> None:
        super().__init__(
            max_documents=max_documents,
            max_candidates=max_candidates,
            read_budget=read_budget,
            workspace_documents=workspace_documents,
        )
        self.anchors_per_document = anchors_per_document
        self.title_lookup: dict[str, set[int]] = defaultdict(set)
        self.max_title_length = 0

    def _index_document(self, document_id: int, text: str) -> None:
        document = self.documents[document_id]
        title = _normalise_title(document.title)
        if title:
            self.title_lookup[title].add(document_id)
            self.max_title_length = max(self.max_title_length, len(title))
        for anchor in _routing_anchors(
            document.title,
            document.source_id,
            text,
            limit=self.anchors_per_document,
        ):
            self.postings[anchor].add(document_id)

    def ingest(self, text: str, *, source_id: str, title: str = "") -> int:
        if len(self.documents) >= self.max_documents:
            raise MemoryError("discourse document capacity reached")
        document_id = len(self.documents)
        title = title or source_id
        node_ids: list[int] = []
        last_claim: int | None = None
        recent_support: list[int] = []
        for position, sentence in enumerate(_sentences(text)):
            role = _role(sentence)
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
        self._index_document(document_id, text)
        self.workspace.append(document_id)
        return document_id

    def _exact_title_documents(self, query: str) -> list[int]:
        compact = _normalise_title(query)
        if not compact or not self.title_lookup:
            return []
        matches: list[tuple[int, int, int, str]] = []
        upper = min(self.max_title_length, len(compact))
        for length in range(upper, 3, -1):
            for start in range(0, len(compact) - length + 1):
                piece = compact[start : start + length]
                document_ids = self.title_lookup.get(piece)
                if not document_ids:
                    continue
                for document_id in document_ids:
                    matches.append((length, start, document_id, piece))
        selected: list[tuple[int, int]] = []
        output: list[int] = []
        for length, start, document_id, _piece in sorted(
            matches,
            key=lambda item: (-item[0], item[1], item[2]),
        ):
            end = start + length
            if any(start >= old_start and end <= old_end for old_start, old_end in selected):
                continue
            selected.append((start, end))
            if document_id not in output:
                output.append(document_id)
                if len(output) >= self.max_candidates:
                    break
        return output

    def _candidate_documents(self, query: str) -> list[int]:
        exact = self._exact_title_documents(query)
        if exact:
            self.last_scores = {
                document_id: float(len(exact) - rank + 1) * 1000.0
                for rank, document_id in enumerate(exact)
            }
            self.last_candidates = len(exact)
            self.last_anchor_reads = 0
            return exact

        generic = any(
            marker in query
            for marker in (
                "この文章",
                "この資料",
                "筆者",
                "要約",
                "要旨",
                "主張",
                "結論",
                "根拠",
                "理由",
                "反論",
                "反対意見",
            )
        )
        routes = sorted(
            (
                len(self.postings.get(anchor, ())),
                -len(anchor),
                anchor,
            )
            for anchor in _anchors(query)
            if self.postings.get(anchor)
        )
        votes: Counter[int] = Counter()
        reads = 0
        routes_used = 0
        for posting_size, negative_length, anchor in routes:
            if votes and posting_size > self.max_candidates * 8:
                break
            weight = (-negative_length) ** 2 / max(1, posting_size)
            for document_id in self.postings[anchor]:
                votes[document_id] += weight
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
        if not votes and generic and self.workspace:
            votes[self.workspace[-1]] = 1.0
        ranked = votes.most_common(self.max_candidates)
        self.last_scores = dict(ranked)
        self.last_candidates = len(ranked)
        self.last_anchor_reads = reads
        return [document_id for document_id, _score in ranked]

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-discourse-hs9-compact",
            "max_documents": self.max_documents,
            "max_candidates": self.max_candidates,
            "read_budget": self.read_budget,
            "anchors_per_document": self.anchors_per_document,
            "documents": [asdict(document) for document in self.documents],
            "nodes": [asdict(node) for node in self.nodes],
            "edges": [asdict(edge) for edge in self.edges],
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
    def from_bytes(cls, data: bytes) -> "CompactSparseDiscourseGraph":
        from .sparc_discourse import DiscourseEdge

        payload = json.loads(zlib.decompress(data))
        graph = cls(
            max_documents=int(payload["max_documents"]),
            max_candidates=int(payload["max_candidates"]),
            read_budget=int(payload["read_budget"]),
            anchors_per_document=int(payload["anchors_per_document"]),
        )
        graph.nodes = [
            DiscourseNode(
                int(row["document_id"]),
                str(row["source_id"]),
                int(row["position"]),
                str(row["text"]),
                str(row["role"]),
            )
            for row in payload["nodes"]
        ]
        graph.documents = [
            DiscourseDocument(
                str(row["source_id"]),
                str(row["title"]),
                tuple(int(item) for item in row["node_ids"]),
            )
            for row in payload["documents"]
        ]
        for document_id, document in enumerate(graph.documents):
            text = "".join(graph.nodes[node_id].text for node_id in document.node_ids)
            graph._index_document(document_id, text)
            for node_id in document.node_ids:
                graph.role_nodes[document_id][graph.nodes[node_id].role].append(node_id)
        for row in payload["edges"]:
            edge = DiscourseEdge(
                int(row["source_node"]),
                int(row["target_node"]),
                str(row["kind"]),
            )
            graph._add_edge(edge.source_node, edge.target_node, edge.kind)
        return graph

    def report(self) -> dict[str, int | bool]:
        report = super().report()
        report.update(
            {
                "anchors_per_document": self.anchors_per_document,
                "exact_title_entries": len(self.title_lookup),
                "selective_anchor_index": True,
            }
        )
        return report


class SPARCHS9CompactModel:
    def __init__(self, base: SPARCHS8Model | None = None) -> None:
        self.base = base or SPARCHS8Model()
        self.discourse = CompactSparseDiscourseGraph()

    def ingest_discourse(self, text: str, *, source_id: str, title: str = "") -> int:
        return self.discourse.ingest(text, source_id=source_id, title=title)

    def reply(self, text: str) -> ReplyResult:
        discourse = self.discourse.answer(text)
        if discourse is not None and discourse.confidence >= 0.35:
            return discourse
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs9-compact",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "discourse": base64.b85encode(self.discourse.to_bytes()).decode("ascii"),
        }
        return zlib.compress(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS9CompactModel":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS8Model.from_bytes(base64.b85decode(payload["base"])))
        model.discourse = CompactSparseDiscourseGraph.from_bytes(
            base64.b85decode(payload["discourse"])
        )
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS9CompactModel":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "stage": "SPARC-HS9-COMPACT",
            "base": self.base.report(),
            "discourse": self.discourse.report(),
            "serialized_bytes": len(self.to_bytes()),
            "global_edge_scan_used": False,
            "growing_kv_cache_used": False,
        }
