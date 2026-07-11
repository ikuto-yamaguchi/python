from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .latent_relation_partition import (
    EffectEvidence,
    PartitionModel,
    fit_partition,
)


Partition = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class ResidualSearchResult:
    selected: PartitionModel
    models: tuple[PartitionModel, ...]
    evaluated_partitions: int
    proposed_partitions: int
    fit_candidate_checks: int
    rounds: int
    beam_width: int


def canonical_partition(blocks: Sequence[Sequence[int]]) -> Partition:
    return tuple(
        sorted(
            (tuple(sorted(block)) for block in blocks if block),
            key=lambda block: block[0],
        )
    )


def _template_signature(
    template: str,
    evidence: Sequence[EffectEvidence],
    entity_cells: Mapping[str, tuple[str, ...]],
    max_lag: int,
) -> tuple[int, tuple[int, ...]]:
    """Return the smallest sufficient observed effect signature for one template.

    Cell labels are entity-local and therefore cannot be compared directly.  The
    signature stores the rank of the best cell inside each entity's canonical
    local cell ordering, together with the best shared lag.
    """

    items = [item for item in evidence if item.template == template]
    entities = tuple(sorted(entity_cells))
    best_score = -1
    best_lag = 1
    best_ranks: tuple[int, ...] = tuple(-1 for _ in entities)
    for lag in range(1, max_lag + 1):
        ranks: list[int] = []
        matches = 0
        for entity in entities:
            entity_items = [item for item in items if item.entity == entity]
            cells = entity_cells[entity]
            if not entity_items:
                ranks.append(-1)
                continue
            scores = [
                sum(
                    any(
                        candidate.cell == cell and candidate.lag == lag
                        for candidate in item.candidates
                    )
                    for item in entity_items
                )
                for cell in cells
            ]
            top = max(scores)
            ranks.append(next(index for index, score in enumerate(scores) if score == top))
            matches += top
        rank_tuple = tuple(ranks)
        if matches > best_score or (
            matches == best_score and (lag, rank_tuple) < (best_lag, best_ranks)
        ):
            best_score = matches
            best_lag = lag
            best_ranks = rank_tuple
    return best_lag, best_ranks


def _split_block(
    partition: Partition,
    block_index: int,
    groups: Mapping[object, list[int]],
) -> Partition | None:
    if len(groups) <= 1:
        return None
    remaining = [
        block for index, block in enumerate(partition) if index != block_index
    ]
    remaining.extend(tuple(items) for items in groups.values())
    return canonical_partition(remaining)


def _signature_splits(
    partition: Partition,
    signatures: Mapping[int, tuple[int, tuple[int, ...]]],
) -> set[Partition]:
    proposals: set[Partition] = set()
    for block_index, block in enumerate(partition):
        if len(block) <= 1:
            continue
        for mode in ("lag", "cells", "full"):
            groups: dict[object, list[int]] = {}
            for template_index in block:
                lag, cell_ranks = signatures[template_index]
                if mode == "lag":
                    key: object = lag
                elif mode == "cells":
                    key = cell_ranks
                else:
                    key = (lag, cell_ranks)
                groups.setdefault(key, []).append(template_index)
            candidate = _split_block(partition, block_index, groups)
            if candidate is not None:
                proposals.add(candidate)
    return proposals


def _residual_isolations(
    partition: Partition,
    model: PartitionModel,
    templates: tuple[str, ...],
    evidence: Sequence[EffectEvidence],
    *,
    per_block_limit: int = 2,
) -> set[Partition]:
    template_to_index = {
        template: index for index, template in enumerate(templates)
    }
    proposals: set[Partition] = set()
    for cluster_index, block in enumerate(partition):
        if len(block) <= 1:
            continue
        scored: list[tuple[int, int]] = []
        for template_index in block:
            errors = 0
            for item in evidence:
                if template_to_index[item.template] != template_index:
                    continue
                predicted_cell = model.assignments.get((cluster_index, item.entity))
                predicted_lag = model.lags[cluster_index]
                if predicted_cell is None or not any(
                    candidate.cell == predicted_cell
                    and candidate.lag == predicted_lag
                    for candidate in item.candidates
                ):
                    errors += 1
            if errors:
                scored.append((errors, template_index))
        for _errors, template_index in sorted(scored, reverse=True)[:per_block_limit]:
            rest = tuple(item for item in block if item != template_index)
            blocks = [
                current
                for index, current in enumerate(partition)
                if index != cluster_index
            ]
            blocks.extend((rest, (template_index,)))
            proposals.add(canonical_partition(blocks))
    return proposals


def _merge_proposals(partition: Partition) -> set[Partition]:
    proposals: set[Partition] = set()
    for left in range(len(partition)):
        for right in range(left + 1, len(partition)):
            merged = tuple(sorted(partition[left] + partition[right]))
            blocks = [
                block
                for index, block in enumerate(partition)
                if index not in (left, right)
            ]
            blocks.append(merged)
            proposals.add(canonical_partition(blocks))
    return proposals


def estimate_fit_candidate_checks(
    partition: Partition,
    templates: tuple[str, ...],
    evidence: Sequence[EffectEvidence],
    entity_cells: Mapping[str, tuple[str, ...]],
    calibration: Sequence[EffectEvidence],
    validation: Sequence[EffectEvidence],
    max_lag: int,
) -> int:
    """Conservative count of effect-candidate comparisons made by one fit."""

    template_to_index = {
        template: index for index, template in enumerate(templates)
    }
    checks = 0
    for block in partition:
        cluster_items = [
            item
            for item in evidence
            if template_to_index[item.template] in block
        ]
        for _lag in range(1, max_lag + 1):
            for entity, cells in entity_cells.items():
                entity_items = [
                    item for item in cluster_items if item.entity == entity
                ]
                for _cell in cells:
                    checks += sum(len(item.candidates) for item in entity_items)
    checks += sum(len(item.candidates) for item in calibration)
    checks += sum(len(item.candidates) for item in validation)
    return checks


def residual_beam_search(
    templates: tuple[str, ...],
    evidence: Sequence[EffectEvidence],
    entity_cells: Mapping[str, tuple[str, ...]],
    calibration: Sequence[EffectEvidence],
    validation: Sequence[EffectEvidence],
    *,
    max_lag: int = 4,
    beam_width: int = 8,
    max_rounds: int = 8,
) -> ResidualSearchResult:
    """Search only partitions suggested by observed prediction collisions.

    This is not a guarantee of the global optimum.  Tiny worlds must still be
    compared with the exhaustive oracle.  The beam and merge moves prevent the
    learner from committing permanently to the first locally attractive split.
    """

    signatures = {
        index: _template_signature(
            template,
            evidence,
            entity_cells,
            max_lag,
        )
        for index, template in enumerate(templates)
    }
    start: Partition = (tuple(range(len(templates))),)
    frontier: list[Partition] = [start]
    evaluated: dict[Partition, PartitionModel] = {}
    proposed: set[Partition] = {start}
    fit_checks = 0
    rounds = 0

    def evaluate(partition: Partition) -> PartitionModel:
        nonlocal fit_checks
        if partition not in evaluated:
            evaluated[partition] = fit_partition(
                partition,
                templates,
                evidence,
                entity_cells,
                calibration,
                validation,
                max_lag=max_lag,
            )
            fit_checks += estimate_fit_candidate_checks(
                partition,
                templates,
                evidence,
                entity_cells,
                calibration,
                validation,
                max_lag,
            )
        return evaluated[partition]

    for round_index in range(max_rounds):
        rounds = round_index + 1
        candidates: set[Partition] = set(frontier)
        for partition in frontier:
            model = evaluate(partition)
            candidates.update(_signature_splits(partition, signatures))
            candidates.update(
                _residual_isolations(
                    partition,
                    model,
                    templates,
                    evidence,
                )
            )
            candidates.update(_merge_proposals(partition))
        proposed.update(candidates)
        ranked = sorted(
            candidates,
            key=lambda partition: (
                evaluate(partition).objective,
                len(partition),
                partition,
            ),
        )[:beam_width]
        if set(ranked) == set(frontier):
            frontier = ranked
            break
        frontier = ranked

    models = tuple(
        sorted(
            evaluated.values(),
            key=lambda model: (
                model.objective,
                len(model.partition),
                model.partition,
            ),
        )
    )
    return ResidualSearchResult(
        selected=models[0],
        models=models,
        evaluated_partitions=len(evaluated),
        proposed_partitions=len(proposed),
        fit_candidate_checks=fit_checks,
        rounds=rounds,
        beam_width=beam_width,
    )
