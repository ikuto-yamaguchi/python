from __future__ import annotations

import json
import zlib
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Hashable, Iterable, Sequence

SparseCode = tuple[int, ...]


@dataclass
class SPARCNode:
    code: SparseCode
    payloads: Counter[str] = field(default_factory=Counter)
    transitions: Counter[int] = field(default_factory=Counter)
    visits: int = 0
    surprise_writes: int = 0

    @property
    def payload(self) -> str | None:
        if not self.payloads:
            return None
        return self.payloads.most_common(1)[0][0]

    @property
    def next_node(self) -> int | None:
        if not self.transitions:
            return None
        return self.transitions.most_common(1)[0][0]


@dataclass(frozen=True)
class SPARCStep:
    node_id: int
    familiar: bool
    similarity: float
    predicted_payload: str | None
    predicted_next_node: int | None
    payload_correct: bool
    transition_correct: bool | None
    surprise: bool
    wrote: bool
    candidates_inspected: int


@dataclass(frozen=True)
class SPARCReport:
    code_space: int
    active_bits: int
    nodes: int
    directed_edges: int
    observations: int
    surprise_writes: int
    write_fraction: float
    mean_candidates_inspected: float
    max_candidates_inspected: int
    serialized_bytes: int
    estimated_sparse_entries: int


def canonical_code(bits: Iterable[int], *, code_space: int, active_bits: int) -> SparseCode:
    code = tuple(sorted({int(bit) % code_space for bit in bits}))
    if len(code) != active_bits:
        raise ValueError(f"code must contain exactly {active_bits} distinct bits")
    return code


class SurprisePropagatedGraph:
    """Sparse event-indexed predictive graph with local surprise updates.

    Retrieval uses an inverted index over active bits. Routine events only read
    the matching node and compare its local prediction. Node payloads and edges
    are updated only when the current prediction is wrong or the event is new.
    No operation scans the complete history or complete node set.
    """

    def __init__(
        self,
        *,
        code_space: int = 4096,
        active_bits: int = 16,
        familiarity_threshold: float = 0.55,
        max_degree: int = 8,
    ) -> None:
        if code_space <= active_bits:
            raise ValueError("code_space must exceed active_bits")
        if not 0.0 < familiarity_threshold <= 1.0:
            raise ValueError("familiarity_threshold must be in (0, 1]")
        if max_degree < 1:
            raise ValueError("max_degree must be positive")
        self.code_space = code_space
        self.active_bits = active_bits
        self.familiarity_threshold = familiarity_threshold
        self.max_degree = max_degree
        self.nodes: list[SPARCNode] = []
        self.postings: dict[int, set[int]] = defaultdict(set)
        self.previous_node: int | None = None
        self.observations = 0
        self.surprise_writes = 0
        self.candidate_inspections = 0
        self.max_candidates_inspected = 0

    def reset_working_state(self) -> None:
        self.previous_node = None

    def _candidates(self, code: SparseCode) -> Counter[int]:
        votes: Counter[int] = Counter()
        for bit in code:
            votes.update(self.postings.get(bit, ()))
        self.candidate_inspections += len(votes)
        self.max_candidates_inspected = max(self.max_candidates_inspected, len(votes))
        return votes

    def match(self, code: Sequence[int]) -> tuple[int | None, float, int]:
        normalized = canonical_code(
            code,
            code_space=self.code_space,
            active_bits=self.active_bits,
        )
        votes = self._candidates(normalized)
        if not votes:
            return None, 0.0, 0
        node_id, overlap = max(votes.items(), key=lambda item: (item[1], -item[0]))
        similarity = overlap / self.active_bits
        if similarity < self.familiarity_threshold:
            return None, similarity, len(votes)
        return node_id, similarity, len(votes)

    def _allocate(self, code: SparseCode) -> int:
        node_id = len(self.nodes)
        self.nodes.append(SPARCNode(code))
        for bit in code:
            self.postings[bit].add(node_id)
        return node_id

    def _bounded_transition_update(self, source: int, target: int) -> None:
        transitions = self.nodes[source].transitions
        transitions[target] += 1
        if len(transitions) > self.max_degree:
            victim = min(transitions, key=lambda node: (transitions[node], node))
            del transitions[victim]

    def observe(self, code: Sequence[int], payload: Hashable) -> SPARCStep:
        normalized = canonical_code(
            code,
            code_space=self.code_space,
            active_bits=self.active_bits,
        )
        self.observations += 1
        matched, similarity, candidates = self.match(normalized)
        familiar = matched is not None
        if matched is None:
            matched = self._allocate(normalized)

        node = self.nodes[matched]
        payload_text = str(payload)
        predicted_payload = node.payload
        predicted_next = (
            self.nodes[self.previous_node].next_node
            if self.previous_node is not None
            else None
        )
        payload_correct = predicted_payload == payload_text
        transition_correct = (
            None
            if self.previous_node is None or predicted_next is None
            else predicted_next == matched
        )
        transition_surprise = (
            self.previous_node is not None
            and (predicted_next is None or predicted_next != matched)
        )
        surprise = (not familiar) or (not payload_correct) or transition_surprise
        wrote = False
        if surprise:
            wrote = True
            self.surprise_writes += 1
            node.surprise_writes += 1
            if not payload_correct:
                node.payloads[payload_text] += 1
            if self.previous_node is not None and transition_surprise:
                self._bounded_transition_update(self.previous_node, matched)
        node.visits += 1
        self.previous_node = matched
        return SPARCStep(
            node_id=matched,
            familiar=familiar,
            similarity=similarity,
            predicted_payload=predicted_payload,
            predicted_next_node=predicted_next,
            payload_correct=payload_correct,
            transition_correct=transition_correct,
            surprise=surprise,
            wrote=wrote,
            candidates_inspected=candidates,
        )

    def recall(self, code: Sequence[int]) -> tuple[str | None, float, int]:
        node_id, similarity, candidates = self.match(code)
        if node_id is None:
            return None, similarity, candidates
        return self.nodes[node_id].payload, similarity, candidates

    def simulate(self, code: Sequence[int], steps: int) -> tuple[int, ...]:
        node_id, _similarity, _candidates = self.match(code)
        if node_id is None or steps <= 0:
            return ()
        path: list[int] = [node_id]
        current = node_id
        for _ in range(steps - 1):
            next_node = self.nodes[current].next_node
            if next_node is None:
                break
            path.append(next_node)
            current = next_node
        return tuple(path)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-001",
            "code_space": self.code_space,
            "active_bits": self.active_bits,
            "familiarity_threshold": self.familiarity_threshold,
            "max_degree": self.max_degree,
            "nodes": [
                {
                    "code": node.code,
                    "payloads": dict(node.payloads),
                    "transitions": {str(key): value for key, value in node.transitions.items()},
                    "visits": node.visits,
                    "surprise_writes": node.surprise_writes,
                }
                for node in self.nodes
            ],
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return zlib.compress(raw, level=9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SurprisePropagatedGraph":
        payload = json.loads(zlib.decompress(data))
        graph = cls(
            code_space=int(payload["code_space"]),
            active_bits=int(payload["active_bits"]),
            familiarity_threshold=float(payload["familiarity_threshold"]),
            max_degree=int(payload["max_degree"]),
        )
        for row in payload["nodes"]:
            node_id = graph._allocate(tuple(int(bit) for bit in row["code"]))
            node = graph.nodes[node_id]
            node.payloads.update({str(key): int(value) for key, value in row["payloads"].items()})
            node.transitions.update({int(key): int(value) for key, value in row["transitions"].items()})
            node.visits = int(row["visits"])
            node.surprise_writes = int(row["surprise_writes"])
        return graph

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SurprisePropagatedGraph":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> SPARCReport:
        edges = sum(len(node.transitions) for node in self.nodes)
        sparse_entries = len(self.nodes) * self.active_bits + edges * 2
        return SPARCReport(
            code_space=self.code_space,
            active_bits=self.active_bits,
            nodes=len(self.nodes),
            directed_edges=edges,
            observations=self.observations,
            surprise_writes=self.surprise_writes,
            write_fraction=(self.surprise_writes / self.observations if self.observations else 0.0),
            mean_candidates_inspected=(self.candidate_inspections / self.observations if self.observations else 0.0),
            max_candidates_inspected=self.max_candidates_inspected,
            serialized_bytes=len(self.to_bytes()),
            estimated_sparse_entries=sparse_entries,
        )
