from __future__ import annotations

from dataclasses import dataclass
import itertools
import json
from typing import Iterable, Mapping


REFERENCE_SIGNALS = (
    "subject_continuity",
    "object_control",
    "subject_control",
    "possessive_link",
    "semantic_fit",
    "parallel_role",
    "recency",
)


def _description_bits(payload: object) -> int:
    return len(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ) * 8


@dataclass(frozen=True)
class ReferenceCandidate:
    candidate_id: str
    compatible: bool
    signals: tuple[tuple[str, int], ...]

    @classmethod
    def build(
        cls,
        candidate_id: str,
        *,
        compatible: bool = True,
        **signals: int,
    ) -> "ReferenceCandidate":
        unknown = set(signals) - set(REFERENCE_SIGNALS)
        if unknown:
            raise ValueError(f"unknown reference signals: {sorted(unknown)}")
        normalized = tuple(
            sorted(
                (name, int(value))
                for name, value in signals.items()
                if int(value) != 0
            )
        )
        if any(value not in (-1, 1) for _name, value in normalized):
            raise ValueError("reference signal values must be -1, 0, or 1")
        return cls(candidate_id, compatible, normalized)

    def signal_map(self) -> dict[str, int]:
        return dict(self.signals)


@dataclass(frozen=True)
class ReferenceSituation:
    candidates: tuple[ReferenceCandidate, ...]

    def __post_init__(self) -> None:
        if len(self.candidates) < 2:
            raise ValueError("reference resolution requires at least two candidates")
        identifiers = [candidate.candidate_id for candidate in self.candidates]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("candidate identifiers must be unique")


@dataclass(frozen=True)
class ReferenceObservation:
    situation: ReferenceSituation
    expected: str | None


@dataclass(frozen=True)
class ReferencePrediction:
    output: str | None
    scores: tuple[tuple[str, int | None], ...]
    operations: int
    compatible_candidates: int
    ambiguous: bool


@dataclass(frozen=True)
class InducedReferenceMachine:
    weights: tuple[tuple[str, int], ...]
    calibration_examples: int
    candidate_assignments_evaluated: int
    benchmark_task_name_branches: int = 0
    domain_specific_handlers: int = 0

    def weight_map(self) -> dict[str, int]:
        return dict(self.weights)

    def predict(self, situation: ReferenceSituation) -> ReferencePrediction:
        weights = self.weight_map()
        score_rows: list[tuple[str, int | None]] = []
        operations = 0
        for candidate in situation.candidates:
            if not candidate.compatible:
                score_rows.append((candidate.candidate_id, None))
                operations += 1
                continue
            score = 0
            for name, value in candidate.signals:
                score += weights.get(name, 0) * value
                operations += 1
            score_rows.append((candidate.candidate_id, score))
        compatible = [(name, score) for name, score in score_rows if score is not None]
        if not compatible:
            return ReferencePrediction(None, tuple(score_rows), operations, 0, True)
        best_score = max(int(score) for _name, score in compatible)
        winners = [name for name, score in compatible if score == best_score]
        if best_score <= 0 or len(winners) != 1:
            return ReferencePrediction(
                None,
                tuple(score_rows),
                operations,
                len(compatible),
                True,
            )
        return ReferencePrediction(
            winners[0],
            tuple(score_rows),
            operations,
            len(compatible),
            False,
        )

    def render(self) -> object:
        return {
            "weights": [list(row) for row in self.weights],
            "calibration_examples": self.calibration_examples,
            "candidate_assignments_evaluated": self.candidate_assignments_evaluated,
            "agreement": "hard compatibility filter",
            "decision": "unique positive maximum else ambiguous",
            "benchmark_task_name_branches": self.benchmark_task_name_branches,
            "domain_specific_handlers": self.domain_specific_handlers,
        }

    @property
    def description_bits(self) -> int:
        return _description_bits(self.render())


def reference_accuracy(
    machine: InducedReferenceMachine,
    observations: Iterable[ReferenceObservation],
) -> float:
    rows = tuple(observations)
    if not rows:
        return 0.0
    return sum(
        machine.predict(observation.situation).output == observation.expected
        for observation in rows
    ) / len(rows)


def induce_reference_machine(
    observations: Iterable[ReferenceObservation],
    *,
    maximum_weight: int = 4,
) -> InducedReferenceMachine:
    rows = tuple(observations)
    if not rows:
        raise ValueError("at least one reference observation is required")
    if maximum_weight < 1:
        raise ValueError("maximum_weight must be positive")

    evaluated = 0
    valid: list[InducedReferenceMachine] = []
    for assignment in itertools.product(
        range(maximum_weight + 1),
        repeat=len(REFERENCE_SIGNALS),
    ):
        evaluated += 1
        machine = InducedReferenceMachine(
            tuple(zip(REFERENCE_SIGNALS, assignment, strict=True)),
            len(rows),
            evaluated,
        )
        if reference_accuracy(machine, rows) == 1.0:
            valid.append(machine)
    if not valid:
        raise ValueError("no bounded reference weight assignment explains calibration")

    selected = min(
        valid,
        key=lambda machine: (
            sum(machine.weight_map().values()),
            max(machine.weight_map().values()),
            machine.description_bits,
            machine.weights,
        ),
    )
    return InducedReferenceMachine(
        selected.weights,
        len(rows),
        evaluated,
    )
