from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import re
import unicodedata
from typing import Iterable

from .wordnet_ontology import OntologyDecision, WordNetNounOntology


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    words = [word for word in text.split() if word not in {"a", "an", "the"}]
    normalized = [_singular(word) for word in words]
    return "_".join(normalized)


def _singular(word: str) -> str:
    if word.endswith("ies") and len(word) > 3:
        return word[:-3] + "y"
    if word.endswith("ves") and len(word) > 3:
        return word[:-3] + "f"
    if word.endswith(("ches", "shes", "sses", "xes", "zes")) and len(word) > 2:
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 1:
        return word[:-1]
    return word


def _bits(payload: object) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ) * 8


@dataclass(frozen=True)
class DocumentObservation:
    source_id: str
    text: str
    source_uri: str = ""
    reliability: float = 1.0


@dataclass(frozen=True)
class ConceptEdge:
    child: str
    parent: str
    positive: bool
    source_id: str
    source_uri: str
    evidence: str
    reliability: float

    def render(self) -> object:
        return {
            "child": self.child,
            "parent": self.parent,
            "positive": self.positive,
            "source_id": self.source_id,
            "source_uri": self.source_uri,
            "evidence": self.evidence,
            "reliability": self.reliability,
        }


@dataclass(frozen=True)
class GraphDecision:
    item: str
    concept: str
    value: bool | None
    proof: tuple[ConceptEdge, ...]
    reason: str


@dataclass(frozen=True)
class OverlayDecision:
    item: str
    concept: str
    value: bool | None
    item_candidates: tuple[str, ...]
    concept_candidates: tuple[str, ...]
    proof_offsets: tuple[int, ...] = ()
    reason: str = ""
    graph_proof: tuple[ConceptEdge, ...] = ()
    wordnet_decision: OntologyDecision | None = None


class ProvenanceConceptGraph:
    def __init__(self, edges: Iterable[ConceptEdge]) -> None:
        unique = {
            (
                edge.child,
                edge.parent,
                edge.positive,
                edge.source_id,
                edge.source_uri,
                edge.evidence,
                edge.reliability,
            ): edge
            for edge in edges
        }
        self.edges = tuple(sorted(unique.values(), key=lambda edge: repr(edge.render())))
        self._positive: dict[str, list[ConceptEdge]] = {}
        self._negative: dict[tuple[str, str], list[ConceptEdge]] = {}
        for edge in self.edges:
            if edge.positive:
                self._positive.setdefault(edge.child, []).append(edge)
            else:
                self._negative.setdefault((edge.child, edge.parent), []).append(edge)

    def query(self, item: str, concept: str) -> GraphDecision:
        child = _normalize(item)
        parent = _normalize(concept)
        negative = tuple(self._negative.get((child, parent), ()))
        positive_path = self._positive_path(child, parent)
        if positive_path is not None and negative:
            return GraphDecision(item, concept, None, positive_path + negative, "conflicting-evidence")
        if positive_path is not None:
            return GraphDecision(item, concept, True, positive_path, "positive-provenance-path")
        if negative:
            return GraphDecision(item, concept, False, negative, "explicit-negative-evidence")
        return GraphDecision(item, concept, None, (), "no-document-evidence")

    def _positive_path(self, child: str, parent: str) -> tuple[ConceptEdge, ...] | None:
        if child == parent:
            return ()
        queue: deque[str] = deque([child])
        predecessor: dict[str, tuple[str, ConceptEdge] | None] = {child: None}
        while queue:
            node = queue.popleft()
            for edge in self._positive.get(node, ()):  # child -> parent
                if edge.parent in predecessor:
                    continue
                predecessor[edge.parent] = (node, edge)
                if edge.parent == parent:
                    path: list[ConceptEdge] = []
                    current = parent
                    while predecessor[current] is not None:
                        previous, used = predecessor[current]
                        path.append(used)
                        current = previous
                    return tuple(reversed(path))
                queue.append(edge.parent)
        return None

    def render(self) -> object:
        return [edge.render() for edge in self.edges]

    @property
    def description_bits(self) -> int:
        return _bits(self.render())


class ProvenanceOverlayOntology:
    def __init__(
        self,
        base: WordNetNounOntology,
        graph: ProvenanceConceptGraph,
    ) -> None:
        self.base = base
        self.graph = graph
        self._cache: dict[tuple[str, str], OverlayDecision] = {}
        self.queries = 0
        self.cache_hits = 0

    def is_a(self, item: str, concept: str) -> OverlayDecision:
        key = (_normalize(item), _normalize(concept))
        self.queries += 1
        cached = self._cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            return cached

        graph_decision = self.graph.query(item, concept)
        wordnet = self.base.is_a(item, concept)
        if graph_decision.value is not None:
            decision = OverlayDecision(
                item=item,
                concept=concept,
                value=graph_decision.value,
                item_candidates=wordnet.item_candidates,
                concept_candidates=wordnet.concept_candidates,
                proof_offsets=wordnet.proof_offsets if wordnet.value is graph_decision.value else (),
                reason=(
                    graph_decision.reason
                    if wordnet.value in {graph_decision.value, None}
                    else "document-evidence-overrides-wordnet-open-world-absence"
                ),
                graph_proof=graph_decision.proof,
                wordnet_decision=wordnet,
            )
        elif graph_decision.reason == "conflicting-evidence":
            decision = OverlayDecision(
                item=item,
                concept=concept,
                value=None,
                item_candidates=wordnet.item_candidates,
                concept_candidates=wordnet.concept_candidates,
                reason="conflicting-document-evidence",
                graph_proof=graph_decision.proof,
                wordnet_decision=wordnet,
            )
        else:
            decision = OverlayDecision(
                item=item,
                concept=concept,
                value=wordnet.value,
                item_candidates=wordnet.item_candidates,
                concept_candidates=wordnet.concept_candidates,
                proof_offsets=wordnet.proof_offsets,
                reason=f"wordnet:{wordnet.reason}",
                wordnet_decision=wordnet,
            )
        self._cache[key] = decision
        return decision

    def proof_lemmas(self, decision: OverlayDecision) -> tuple[tuple[str, ...], ...]:
        if decision.proof_offsets:
            return tuple(self.base.synsets[offset].lemmas for offset in decision.proof_offsets)
        return ()

    def cache_payload(self) -> object:
        return [
            {
                "item": decision.item,
                "concept": decision.concept,
                "value": decision.value,
                "reason": decision.reason,
                "wordnet_proof": [
                    list(self.base.synsets[offset].lemmas) for offset in decision.proof_offsets
                ],
                "document_proof": [edge.render() for edge in decision.graph_proof],
            }
            for _, decision in sorted(self._cache.items())
        ]

    @property
    def cache_bits(self) -> int:
        return _bits(self.cache_payload())


_INCLUDE_RE = re.compile(r"^(.+?)\s+includes?\s+(.+)$", re.IGNORECASE)
_POSITIVE_RE = re.compile(
    r"^(?:every\s+)?(.+?)\s+(?:are|is\s+(?:a|an)|is\s+a\s+kind\s+of)\s+(.+)$",
    re.IGNORECASE,
)
_NEGATIVE_RE = re.compile(
    r"^(.+?)\s+(?:are\s+not|is\s+not\s+(?:a|an))\s+(.+)$",
    re.IGNORECASE,
)


def _split_members(text: str) -> tuple[str, ...]:
    normalized = re.sub(r"\s*,?\s+and\s+", ",", text, flags=re.IGNORECASE)
    return tuple(value.strip() for value in normalized.split(",") if value.strip())


def extract_edges(document: DocumentObservation) -> tuple[ConceptEdge, ...]:
    edges: list[ConceptEdge] = []
    sentences = [segment.strip() for segment in re.split(r"[.!?]+", document.text) if segment.strip()]
    for sentence in sentences:
        negative = _NEGATIVE_RE.match(sentence)
        if negative:
            edges.append(
                ConceptEdge(
                    _normalize(negative.group(1)),
                    _normalize(negative.group(2)),
                    False,
                    document.source_id,
                    document.source_uri,
                    sentence,
                    document.reliability,
                )
            )
            continue
        include = _INCLUDE_RE.match(sentence)
        if include:
            concept = _normalize(include.group(1))
            for member in _split_members(include.group(2)):
                edges.append(
                    ConceptEdge(
                        _normalize(member),
                        concept,
                        True,
                        document.source_id,
                        document.source_uri,
                        sentence,
                        document.reliability,
                    )
                )
            continue
        positive = _POSITIVE_RE.match(sentence)
        if positive:
            edges.append(
                ConceptEdge(
                    _normalize(positive.group(1)),
                    _normalize(positive.group(2)),
                    True,
                    document.source_id,
                    document.source_uri,
                    sentence,
                    document.reliability,
                )
            )
    return tuple(edges)


def induce_provenance_graph(
    documents: Iterable[DocumentObservation],
) -> ProvenanceConceptGraph:
    edges: list[ConceptEdge] = []
    for document in documents:
        if not document.source_id.strip() or not document.text.strip():
            raise ValueError("document source_id and text are required")
        if not 0.0 < document.reliability <= 1.0:
            raise ValueError("document reliability must be in (0, 1]")
        edges.extend(extract_edges(document))
    if not edges:
        raise ValueError("no concept edges were extracted")
    return ProvenanceConceptGraph(edges)
