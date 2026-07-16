from __future__ import annotations

import base64
import json
import math
import re
import zlib
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .sparc_episodic import SPARCHS8Model
from .sparc_language import ReplyResult


def _normalise(text: str) -> str:
    return re.sub(
        r"\s+",
        "",
        text.strip().replace("?", "？").replace("!", "！"),
    )


def _sentences(text: str) -> tuple[str, ...]:
    return tuple(
        piece.strip()
        for piece in re.split(r"(?<=[。！？])|\n+", text)
        if piece.strip()
    )


_PUNCT_RE = re.compile(r"[。、！？「」『』（）()\[\]\s]")
_GENERIC_QUERY = (
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


def _anchors(text: str) -> set[str]:
    compact = _PUNCT_RE.sub("", _normalise(text))
    output: set[str] = set()
    for size in (3, 4, 5, 6):
        for index in range(max(0, len(compact) - size + 1)):
            output.add(compact[index : index + size])
    return output


def _role(sentence: str) -> str:
    text = _normalise(sentence).lstrip("「『")
    if text.startswith(("したがって", "以上から", "よって", "結論として", "ゆえに")):
        return "conclusion"
    if text.startswith(("なぜなら", "その理由は", "理由は", "根拠として")):
        return "evidence"
    if text.startswith(("例えば", "具体的には", "一例として")):
        return "example"
    if text.startswith(("しかし", "一方で", "一方", "これに対して", "反対に", "ただし")):
        return "counter"
    if text.startswith(("確かに", "もちろん")):
        return "concession"
    if any(
        marker in text
        for marker in (
            "と考える",
            "と主張する",
            "べきである",
            "べきだ",
            "必要である",
            "重要である",
            "不可欠である",
        )
    ):
        return "claim"
    return "detail"


@dataclass(frozen=True)
class DiscourseNode:
    document_id: int
    source_id: str
    position: int
    text: str
    role: str


@dataclass(frozen=True)
class DiscourseEdge:
    source_node: int
    target_node: int
    kind: str


@dataclass(frozen=True)
class DiscourseDocument:
    source_id: str
    title: str
    node_ids: tuple[int, ...]


class SparseDiscourseGraph:
    """Sparse claim/evidence graph with per-target reverse edge routing."""

    def __init__(
        self,
        *,
        max_documents: int = 100_000,
        max_candidates: int = 24,
        read_budget: int = 192,
        workspace_documents: int = 8,
    ) -> None:
        self.max_documents = max_documents
        self.max_candidates = max_candidates
        self.read_budget = read_budget
        self.documents: list[DiscourseDocument] = []
        self.nodes: list[DiscourseNode] = []
        self.edges: list[DiscourseEdge] = []
        self.postings: dict[str, set[int]] = defaultdict(set)
        self.incoming_edges: dict[int, list[int]] = defaultdict(list)
        self.outgoing_edges: dict[int, list[int]] = defaultdict(list)
        self.role_nodes: dict[int, dict[str, list[int]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.workspace: deque[int] = deque(maxlen=workspace_documents)
        self.last_candidates = 0
        self.last_anchor_reads = 0
        self.last_edge_reads = 0
        self.last_estimated_operations = 0
        self.last_scores: dict[int, float] = {}

    def _add_edge(self, source_node: int, target_node: int, kind: str) -> int:
        edge_id = len(self.edges)
        self.edges.append(DiscourseEdge(source_node, target_node, kind))
        self.incoming_edges[target_node].append(edge_id)
        self.outgoing_edges[source_node].append(edge_id)
        return edge_id

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
                kind = "supports" if role == "evidence" else "exemplifies"
                self._add_edge(node_id, last_claim, kind)
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

        document = DiscourseDocument(str(source_id), title, tuple(node_ids))
        self.documents.append(document)
        indexed_text = title + source_id + text
        for anchor in _anchors(indexed_text):
            self.postings[anchor].add(document_id)
        self.workspace.append(document_id)
        return document_id

    def _candidate_documents(self, query: str) -> list[int]:
        generic = any(marker in query for marker in _GENERIC_QUERY)
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

    def _main_claim(self, document_id: int) -> int | None:
        conclusions = self.role_nodes[document_id].get("conclusion", ())
        if conclusions:
            return conclusions[-1]
        claims = self.role_nodes[document_id].get("claim", ())
        if claims:
            return max(
                claims,
                key=lambda node_id: len(self.incoming_edges.get(node_id, ())),
            )
        nodes = self.documents[document_id].node_ids
        return nodes[0] if nodes else None

    def _incoming(
        self,
        node_id: int,
        kinds: set[str],
        *,
        limit: int = 4,
    ) -> list[DiscourseEdge]:
        selected: list[DiscourseEdge] = []
        reads = 0
        for edge_id in self.incoming_edges.get(node_id, ()):
            reads += 1
            edge = self.edges[edge_id]
            if edge.kind in kinds:
                selected.append(edge)
                if len(selected) >= limit:
                    break
        self.last_edge_reads += reads
        return selected

    def _supports(self, claim_id: int, *, limit: int = 3) -> list[int]:
        edges = self._incoming(
            claim_id,
            {"supports", "exemplifies", "develops", "elaborates"},
            limit=limit,
        )
        return [edge.source_node for edge in edges]

    def _counters(self, document_id: int, claim_id: int, *, limit: int = 3) -> list[int]:
        direct = self._incoming(claim_id, {"opposes", "qualifies"}, limit=limit)
        output = [edge.source_node for edge in direct]
        if len(output) < limit:
            for node_id in self.role_nodes[document_id].get("counter", ()):
                if node_id not in output:
                    output.append(node_id)
                    if len(output) >= limit:
                        break
        return output

    def _render_summary(self, document_id: int) -> tuple[str, list[int], str, float]:
        claim_id = self._main_claim(document_id)
        if claim_id is None:
            raise ValueError("document has no nodes")
        supports = self._supports(claim_id, limit=3)
        claim = self.nodes[claim_id]
        if supports:
            evidence = " ".join(self.nodes[node_id].text for node_id in supports)
            text = (
                f"筆者の中心的な主張は「{claim.text}」です。"
                f"主な根拠は、{evidence}"
                f" 出典: ［{claim.source_id}］"
            )
        else:
            text = f"要旨は「{claim.text}」です。出典: ［{claim.source_id}］"
        return text, [claim_id, *supports], "sparse-discourse-summary", 0.82

    def _render_evidence(self, document_id: int) -> tuple[str, list[int], str, float]:
        claim_id = self._main_claim(document_id)
        if claim_id is None:
            raise ValueError("document has no nodes")
        supports = self._supports(claim_id, limit=4)
        if not supports:
            return (
                "明示された根拠は見つかりませんでした。",
                [claim_id],
                "calibrated-discourse-unknown",
                0.35,
            )
        text = "根拠は、" + " ".join(self.nodes[node_id].text for node_id in supports)
        text += f" 出典: ［{self.nodes[claim_id].source_id}］"
        return text, [claim_id, *supports], "reverse-indexed-evidence", 0.86

    def _render_counter(self, document_id: int) -> tuple[str, list[int], str, float]:
        claim_id = self._main_claim(document_id)
        if claim_id is None:
            raise ValueError("document has no nodes")
        counters = self._counters(document_id, claim_id, limit=3)
        if not counters:
            return (
                "この資料には明示的な反対意見がありません。",
                [claim_id],
                "calibrated-discourse-unknown",
                0.40,
            )
        text = "反対意見・留保は、" + " ".join(
            self.nodes[node_id].text for node_id in counters
        )
        text += f" 出典: ［{self.nodes[claim_id].source_id}］"
        return text, [claim_id, *counters], "local-counterargument-retrieval", 0.82

    def _render_comparison(self, document_ids: list[int]) -> tuple[str, list[int], str, float]:
        if len(document_ids) < 2:
            raise ValueError("comparison needs two documents")
        selected = document_ids[:2]
        claim_ids = [self._main_claim(document_id) for document_id in selected]
        if any(claim_id is None for claim_id in claim_ids):
            raise ValueError("comparison document has no claim")
        left_id, right_id = claim_ids  # type: ignore[misc]
        left = self.nodes[left_id]
        right = self.nodes[right_id]
        text = (
            f"［{left.source_id}］は「{left.text}」と主張します。"
            f"一方、［{right.source_id}］は「{right.text}」と主張します。"
            "違いは、中心的に重視する結論が異なる点です。"
        )
        return text, [left_id, right_id], "bounded-two-document-comparison", 0.78

    def answer(self, query: str) -> ReplyResult | None:
        document_ids = self._candidate_documents(query)
        if not document_ids:
            return None
        self.last_edge_reads = 0
        try:
            if any(marker in query for marker in ("比較", "違い", "共通点")):
                text, used, mechanism, confidence = self._render_comparison(document_ids)
            else:
                document_id = document_ids[0]
                if any(marker in query for marker in ("反論", "反対意見", "異論", "留保")):
                    text, used, mechanism, confidence = self._render_counter(document_id)
                elif any(marker in query for marker in ("根拠", "理由", "なぜ")):
                    text, used, mechanism, confidence = self._render_evidence(document_id)
                else:
                    text, used, mechanism, confidence = self._render_summary(document_id)
                self.workspace.append(document_id)
        except ValueError:
            return None
        operations = (
            len(_anchors(query))
            + self.last_anchor_reads
            + len(document_ids) * 2
            + self.last_edge_reads
            + len(used)
        )
        self.last_estimated_operations = operations
        return ReplyResult(
            text=text,
            confidence=confidence,
            mechanism=mechanism,
            candidates_inspected=self.last_candidates,
            active_bits=len(used),
            estimated_sparse_operations=operations,
        )

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-discourse-hs9",
            "max_documents": self.max_documents,
            "max_candidates": self.max_candidates,
            "read_budget": self.read_budget,
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
    def from_bytes(cls, data: bytes) -> "SparseDiscourseGraph":
        payload = json.loads(zlib.decompress(data))
        graph = cls(
            max_documents=int(payload["max_documents"]),
            max_candidates=int(payload["max_candidates"]),
            read_budget=int(payload["read_budget"]),
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
            indexed_text = document.title + document.source_id + "".join(
                graph.nodes[node_id].text for node_id in document.node_ids
            )
            for anchor in _anchors(indexed_text):
                graph.postings[anchor].add(document_id)
            for node_id in document.node_ids:
                graph.role_nodes[document_id][graph.nodes[node_id].role].append(node_id)
        for row in payload["edges"]:
            graph._add_edge(
                int(row["source_node"]),
                int(row["target_node"]),
                str(row["kind"]),
            )
        return graph

    def report(self) -> dict[str, int | bool]:
        return {
            "documents": len(self.documents),
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "posting_edges": sum(len(items) for items in self.postings.values()),
            "serialized_bytes": len(self.to_bytes()),
            "last_candidates": self.last_candidates,
            "last_anchor_reads": self.last_anchor_reads,
            "last_edge_reads": self.last_edge_reads,
            "last_estimated_operations": self.last_estimated_operations,
            "global_edge_scan_used": False,
            "full_history_scan_used": False,
            "softmax_attention_used": False,
        }


class SPARCHS9Model:
    def __init__(self, base: SPARCHS8Model | None = None) -> None:
        self.base = base or SPARCHS8Model()
        self.discourse = SparseDiscourseGraph()

    def ingest_discourse(self, text: str, *, source_id: str, title: str = "") -> int:
        return self.discourse.ingest(text, source_id=source_id, title=title)

    def reply(self, text: str) -> ReplyResult:
        discourse = self.discourse.answer(text)
        if discourse is not None and discourse.confidence >= 0.35:
            return discourse
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs9",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "discourse": base64.b85encode(self.discourse.to_bytes()).decode("ascii"),
        }
        return zlib.compress(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS9Model":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS8Model.from_bytes(base64.b85decode(payload["base"])))
        model.discourse = SparseDiscourseGraph.from_bytes(
            base64.b85decode(payload["discourse"])
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
            "discourse": self.discourse.report(),
            "serialized_bytes": len(self.to_bytes()),
            "global_edge_scan_used": False,
            "growing_kv_cache_used": False,
        }
