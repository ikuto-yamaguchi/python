from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


@dataclass(frozen=True)
class TimelineTrace:
    """An utterance followed by a short sequence of raw entity-local sensors."""

    utterance: str
    entity: str
    value: str
    snapshots: tuple[Mapping[str, str], ...]


@dataclass(frozen=True)
class EffectCandidate:
    cell: str
    lag: int


@dataclass(frozen=True)
class EffectEvidence:
    template: str
    entity: str
    value: str
    candidates: tuple[EffectCandidate, ...]


@dataclass(frozen=True)
class PartitionModel:
    partition: tuple[tuple[int, ...], ...]
    templates: tuple[str, ...]
    lags: Mapping[int, int]
    assignments: Mapping[tuple[int, str], str]
    train_errors: int
    description_bits: int
    validation_correct: int
    validation_total: int
    objective: int

    @property
    def validation_accuracy(self) -> float:
        return self.validation_correct / self.validation_total


def normalize_surface(text: str) -> str:
    return text.strip().replace("。", "").replace("へ", "に")


def abstract_template(text: str, entity: str, value: str) -> str:
    return normalize_surface(text).replace(value, "{V}").replace(entity, "{K}")


def infer_effect_candidates(
    trace: TimelineTrace,
    entity_cells: Mapping[str, tuple[str, ...]],
) -> EffectEvidence:
    """Return first matching change per cell without relation or field labels."""

    baseline = trace.snapshots[0]
    candidates: list[EffectCandidate] = []
    for cell in entity_cells[trace.entity]:
        for lag, snapshot in enumerate(trace.snapshots[1:], start=1):
            if (
                cell in snapshot
                and snapshot.get(cell) != baseline.get(cell)
                and snapshot.get(cell) == trace.value
            ):
                candidates.append(EffectCandidate(cell, lag))
                break
    return EffectEvidence(
        abstract_template(trace.utterance, trace.entity, trace.value),
        trace.entity,
        trace.value,
        tuple(candidates),
    )


def _partitions(items: tuple[int, ...]):
    if not items:
        yield tuple()
        return
    first = items[0]
    for rest in _partitions(items[1:]):
        yield ((first,),) + rest
        for index in range(len(rest)):
            merged = tuple(sorted(rest[index] + (first,)))
            candidate = rest[:index] + (merged,) + rest[index + 1 :]
            yield tuple(sorted(candidate, key=lambda block: block[0]))


def enumerate_partitions(
    count: int,
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    seen: set[tuple[tuple[int, ...], ...]] = set()
    ordered: list[tuple[tuple[int, ...], ...]] = []
    for candidate in _partitions(tuple(range(count))):
        canonical = tuple(
            sorted(
                (tuple(sorted(block)) for block in candidate),
                key=lambda block: block[0],
            )
        )
        if canonical in seen:
            continue
        seen.add(canonical)
        ordered.append(canonical)
    return tuple(ordered)


def bell_number(n: int) -> int:
    bell = [[0] * (n + 1) for _ in range(n + 1)]
    bell[0][0] = 1
    for row in range(1, n + 1):
        bell[row][0] = bell[row - 1][row - 1]
        for column in range(1, row + 1):
            bell[row][column] = (
                bell[row - 1][column - 1] + bell[row][column - 1]
            )
    return bell[n][0]


def _cluster_fit(
    block: tuple[int, ...],
    template_to_index: Mapping[str, int],
    evidence: Sequence[EffectEvidence],
    entity_cells: Mapping[str, tuple[str, ...]],
    max_lag: int,
) -> tuple[int, int, dict[str, str]]:
    cluster_evidence = [
        item
        for item in evidence
        if template_to_index[item.template] in block
    ]
    best_matches = -1
    best_lag = 1
    best_assignments: dict[str, str] = {}
    for lag in range(1, max_lag + 1):
        assignments: dict[str, str] = {}
        matches = 0
        for entity, cells in entity_cells.items():
            entity_evidence = [
                item for item in cluster_evidence if item.entity == entity
            ]
            if not entity_evidence:
                continue
            scores = {
                cell: sum(
                    any(
                        candidate.cell == cell and candidate.lag == lag
                        for candidate in item.candidates
                    )
                    for item in entity_evidence
                )
                for cell in cells
            }
            selected_cell = max(scores, key=scores.get)
            assignments[entity] = selected_cell
            matches += scores[selected_cell]
        if matches > best_matches:
            best_matches = matches
            best_lag = lag
            best_assignments = assignments
    return len(cluster_evidence) - best_matches, best_lag, best_assignments


def fit_partition(
    partition: tuple[tuple[int, ...], ...],
    templates: tuple[str, ...],
    evidence: Sequence[EffectEvidence],
    entity_cells: Mapping[str, tuple[str, ...]],
    calibration: Sequence[EffectEvidence],
    validation: Sequence[EffectEvidence],
    *,
    max_lag: int = 4,
    train_error_bits: int = 512,
    validation_error_bits: int = 1024,
) -> PartitionModel:
    template_to_index = {
        template: index for index, template in enumerate(templates)
    }
    template_to_cluster = {
        template_index: cluster_index
        for cluster_index, block in enumerate(partition)
        for template_index in block
    }
    lags: dict[int, int] = {}
    assignments: dict[tuple[int, str], str] = {}
    train_errors = 0
    for cluster_index, block in enumerate(partition):
        errors, lag, per_entity = _cluster_fit(
            block,
            template_to_index,
            evidence,
            entity_cells,
            max_lag,
        )
        train_errors += errors
        lags[cluster_index] = lag
        for entity, cell in per_entity.items():
            assignments[(cluster_index, entity)] = cell

    adapted: dict[tuple[int, str], str] = {}
    for item in calibration:
        cluster_index = template_to_cluster[
            template_to_index[item.template]
        ]
        matching = [
            candidate
            for candidate in item.candidates
            if candidate.lag == lags[cluster_index]
        ]
        if len(matching) == 1:
            adapted[(cluster_index, item.entity)] = matching[0].cell

    validation_correct = 0
    for item in validation:
        cluster_index = template_to_cluster[
            template_to_index[item.template]
        ]
        predicted_cell = adapted.get((cluster_index, item.entity))
        if predicted_cell is None:
            continue
        if any(
            candidate.cell == predicted_cell
            and candidate.lag == lags[cluster_index]
            for candidate in item.candidates
        ):
            validation_correct += 1

    cluster_count = len(partition)
    template_assignment_bits = len(templates) * max(
        1,
        math.ceil(math.log2(cluster_count)),
    )
    cell_assignment_bits = len(entity_cells) * cluster_count
    description_bits = (
        cluster_count * 27
        + template_assignment_bits
        + cell_assignment_bits
    )
    validation_errors = len(validation) - validation_correct
    objective = (
        description_bits
        + train_errors * train_error_bits
        + validation_errors * validation_error_bits
    )
    return PartitionModel(
        partition,
        templates,
        lags,
        assignments,
        train_errors,
        description_bits,
        validation_correct,
        len(validation),
        objective,
    )


def search_partitions(
    templates: tuple[str, ...],
    evidence: Sequence[EffectEvidence],
    entity_cells: Mapping[str, tuple[str, ...]],
    calibration: Sequence[EffectEvidence],
    validation: Sequence[EffectEvidence],
    *,
    max_lag: int = 4,
) -> tuple[PartitionModel, ...]:
    models = [
        fit_partition(
            partition,
            templates,
            evidence,
            entity_cells,
            calibration,
            validation,
            max_lag=max_lag,
        )
        for partition in enumerate_partitions(len(templates))
    ]
    return tuple(sorted(models, key=lambda model: model.objective))
