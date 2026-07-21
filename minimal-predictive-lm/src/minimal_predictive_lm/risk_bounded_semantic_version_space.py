from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

Signature = tuple[tuple[int, ...], ...]


@dataclass(frozen=True, slots=True)
class Operation:
    name: str
    signature: Signature
    risk: float


@dataclass(frozen=True, slots=True)
class Probe:
    name: str
    outcomes: tuple[int, ...]
    cost: float


class RiskBoundedSemanticVersionSpace:
    """Actively identify an unknown form without unsafe speculative execution.

    Unknown utterances begin as a version space over grounded operations. A
    diagnostic probe is selected by expected remaining ambiguity, worst-case
    ambiguity, probe cost and unresolved risk. The mechanism is non-neural and
    does not use lexical similarity, task names, answer labels, RAG or response
    candidates.
    """

    def __init__(
        self,
        operations: Iterable[Operation],
        probes: Iterable[Probe],
        *,
        risk_budget: float = 0.25,
        max_candidates: int = 256,
    ) -> None:
        self.operations = tuple(operations)
        self.probes = tuple(probes)
        self.risk_budget = float(risk_budget)
        self.max_candidates = int(max_candidates)
        self.bindings: dict[str, int] = {}
        self.version_spaces: dict[str, tuple[int, ...]] = {}
        self.reads = 0
        self.probe_reads = 0

    def begin(self, utterance: str) -> tuple[int, ...]:
        if utterance in self.bindings:
            return (self.bindings[utterance],)
        candidates = tuple(range(min(len(self.operations), self.max_candidates)))
        self.version_spaces[utterance] = candidates
        return candidates

    def _partition(self, candidates: tuple[int, ...], probe: Probe) -> dict[int, list[int]]:
        parts: dict[int, list[int]] = {}
        for index in candidates:
            self.probe_reads += 1
            parts.setdefault(probe.outcomes[index], []).append(index)
        return parts

    def choose_probe(self, utterance: str, used: frozenset[str] = frozenset()) -> Probe | None:
        candidates = self.version_spaces.get(utterance) or self.begin(utterance)
        if len(candidates) <= 1:
            return None
        best: Probe | None = None
        best_key: tuple[float, int, float, str] | None = None
        for probe in self.probes:
            if probe.name in used:
                continue
            parts = self._partition(candidates, probe)
            sizes = [len(group) for group in parts.values()]
            expected = sum(size * size for size in sizes) / len(candidates)
            worst = max(sizes)
            unresolved_risk = sum(
                max(self.operations[index].risk for index in group)
                for group in parts.values()
                if len(group) > 1
            )
            key = (expected + probe.cost + 2.0 * unresolved_risk, worst, probe.cost, probe.name)
            if best_key is None or key < best_key:
                best_key, best = key, probe
        return best

    def observe_probe(self, utterance: str, probe: Probe, outcome: int) -> tuple[int, ...]:
        candidates = self.version_spaces.get(utterance) or self.begin(utterance)
        kept = tuple(index for index in candidates if probe.outcomes[index] == outcome)
        self.reads += len(candidates)
        self.version_spaces[utterance] = kept
        if len(kept) == 1:
            self.bindings[utterance] = kept[0]
        return kept

    def safe_decision(self, utterance: str) -> tuple[str, int | None]:
        if utterance in self.bindings:
            index = self.bindings[utterance]
            action = "execute" if self.operations[index].risk <= self.risk_budget else "confirm"
            return action, index
        candidates = self.version_spaces.get(utterance) or self.begin(utterance)
        if not candidates:
            return "reject", None
        if len(candidates) == 1:
            index = candidates[0]
            action = "execute" if self.operations[index].risk <= self.risk_budget else "confirm"
            return action, index
        return "probe", None

    def serialized_bytes(self) -> int:
        payload = {
            "format": "risk-bounded-semantic-version-space-v1",
            "risk_budget": self.risk_budget,
            "operations": [(item.name, item.signature, item.risk) for item in self.operations],
            "probes": [(item.name, item.outcomes, item.cost) for item in self.probes],
            "bindings": self.bindings,
            "version_spaces": self.version_spaces,
        }
        return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
