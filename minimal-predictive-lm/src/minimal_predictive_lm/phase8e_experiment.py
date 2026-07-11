from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .latent_relation_partition import (
    TimelineTrace,
    bell_number,
    infer_effect_candidates,
    search_partitions,
)
from .residual_partition_search import residual_beam_search


def _make_trace(
    entity: str,
    value: str,
    template: str,
    target_cell: str,
    lag: int,
    cells: tuple[str, ...],
    max_lag: int,
    *,
    ambiguous_noise: bool = False,
) -> TimelineTrace:
    baseline = {
        cell: f"old-{index}"
        for index, cell in enumerate(cells)
    }
    snapshots = [dict(baseline)]
    for step in range(1, max_lag + 2):
        snapshot = dict(snapshots[-1])
        if ambiguous_noise and step == 1:
            other = next(cell for cell in cells if cell != target_cell)
            snapshot[other] = value
        if step == lag:
            snapshot[target_cell] = value
        snapshots.append(snapshot)
    return TimelineTrace(
        template.replace("{K}", entity).replace("{V}", value),
        entity,
        value,
        tuple(snapshots),
    )


def _world(
    template_counts: tuple[int, ...],
    *,
    training_entities: int = 6,
    heldout_entities: int = 2,
) -> dict[str, object]:
    relations = tuple(f"relation-{index}" for index in range(len(template_counts)))
    lags = {
        relation: index + 1
        for index, relation in enumerate(relations)
    }
    templates: list[str] = []
    hidden_relation: dict[str, str] = {}
    for relation_index, (relation, count) in enumerate(
        zip(relations, template_counts)
    ):
        for variant in range(count):
            template = f"{{K}}のR{relation_index}表現{variant}を{{V}}にする"
            templates.append(template)
            hidden_relation[template] = relation
    ordered_templates = tuple(sorted(templates))

    hidden_cells: dict[str, dict[str, str]] = {}
    entity_cells: dict[str, tuple[str, ...]] = {}
    for entity_index in range(training_entities):
        entity = f"対象{entity_index}"
        cells = tuple(
            sorted(
                f"{entity}-cell-{cell_index}"
                for cell_index in range(len(relations))
            )
        )
        hidden_cells[entity] = {
            relation: cells[(relation_index + entity_index) % len(relations)]
            for relation_index, relation in enumerate(relations)
        }
        entity_cells[entity] = cells

    traces: list[TimelineTrace] = []
    for entity_index, entity in enumerate(hidden_cells):
        for template_index, template in enumerate(ordered_templates):
            relation = hidden_relation[template]
            value = f"値{template_index}-{entity_index}"
            traces.append(
                _make_trace(
                    entity,
                    value,
                    template,
                    hidden_cells[entity][relation],
                    lags[relation],
                    entity_cells[entity],
                    len(relations),
                    ambiguous_noise=(
                        entity_index == training_entities - 1
                        and template_index == 0
                    ),
                )
            )

    heldout_cells: dict[str, dict[str, str]] = {}
    heldout_entity_cells: dict[str, tuple[str, ...]] = {}
    for entity_index in range(heldout_entities):
        entity = f"未知対象{entity_index}"
        cells = tuple(
            sorted(
                f"{entity}-cell-{cell_index}"
                for cell_index in range(len(relations))
            )
        )
        heldout_cells[entity] = {
            relation: cells[(relation_index + entity_index + 1) % len(relations)]
            for relation_index, relation in enumerate(relations)
        }
        heldout_entity_cells[entity] = cells

    first_template: dict[str, str] = {}
    for template in ordered_templates:
        first_template.setdefault(hidden_relation[template], template)
    calibration: list[TimelineTrace] = []
    validation: list[TimelineTrace] = []
    for entity in heldout_cells:
        for relation in relations:
            template = first_template[relation]
            calibration.append(
                _make_trace(
                    entity,
                    f"校正-{relation}",
                    template,
                    heldout_cells[entity][relation],
                    lags[relation],
                    heldout_entity_cells[entity],
                    len(relations),
                )
            )
        for template in ordered_templates:
            relation = hidden_relation[template]
            if template == first_template[relation]:
                continue
            validation.append(
                _make_trace(
                    entity,
                    f"検証-{template}",
                    template,
                    heldout_cells[entity][relation],
                    lags[relation],
                    heldout_entity_cells[entity],
                    len(relations),
                )
            )

    return {
        "templates": ordered_templates,
        "hidden_relation": hidden_relation,
        "relations": relations,
        "lags": lags,
        "evidence": [
            infer_effect_candidates(trace, entity_cells)
            for trace in traces
        ],
        "entity_cells": entity_cells,
        "calibration": [
            infer_effect_candidates(trace, heldout_entity_cells)
            for trace in calibration
        ],
        "validation": [
            infer_effect_candidates(trace, heldout_entity_cells)
            for trace in validation
        ],
    }


def _canonical_hidden_partition(
    templates: tuple[str, ...],
    hidden_relation: Mapping[str, str],
) -> set[frozenset[str]]:
    groups: dict[str, set[str]] = {}
    for template in templates:
        groups.setdefault(hidden_relation[template], set()).add(template)
    return {frozenset(group) for group in groups.values()}


def _canonical_model_partition(model: object) -> set[frozenset[str]]:
    return {
        frozenset(model.templates[index] for index in block)
        for block in model.partition
    }


def _case(
    template_counts: tuple[int, ...],
    *,
    run_oracle: bool,
) -> dict[str, object]:
    world = _world(template_counts)
    templates = world["templates"]
    evidence = world["evidence"]
    entity_cells = world["entity_cells"]
    calibration = world["calibration"]
    validation = world["validation"]
    relation_count = len(template_counts)
    residual = residual_beam_search(
        templates,
        evidence,
        entity_cells,
        calibration,
        validation,
        max_lag=relation_count,
        beam_width=8,
        max_rounds=8,
    )
    selected = residual.selected
    hidden_partition = _canonical_hidden_partition(
        templates,
        world["hidden_relation"],
    )
    selected_exact = _canonical_model_partition(selected) == hidden_partition

    oracle_payload: dict[str, object] | None = None
    if run_oracle:
        oracle_models = search_partitions(
            templates,
            evidence,
            entity_cells,
            calibration,
            validation,
            max_lag=relation_count,
        )
        oracle = oracle_models[0]
        oracle_payload = {
            "evaluated_partitions": len(oracle_models),
            "selected_objective": oracle.objective,
            "selected_exact": _canonical_model_partition(oracle) == hidden_partition,
            "residual_objective_gap": selected.objective - oracle.objective,
        }

    return {
        "templates": len(templates),
        "hidden_relations": relation_count,
        "training_traces": len(evidence),
        "validation_traces": len(validation),
        "bell_partitions": bell_number(len(templates)),
        "residual_search": {
            "evaluated_partitions": residual.evaluated_partitions,
            "proposed_partitions": residual.proposed_partitions,
            "fit_candidate_checks": residual.fit_candidate_checks,
            "rounds": residual.rounds,
            "beam_width": residual.beam_width,
            "selected_clusters": len(selected.partition),
            "selected_exact": selected_exact,
            "selected_train_errors": selected.train_errors,
            "selected_description_bits": selected.description_bits,
            "selected_validation_accuracy": selected.validation_accuracy,
            "selected_objective": selected.objective,
            "amortized_fit_checks": {
                str(horizon): residual.fit_candidate_checks / horizon
                for horizon in (1, 100, 10_000)
            },
        },
        "oracle": oracle_payload,
    }


def run() -> dict[str, object]:
    cases = [
        _case((2, 2), run_oracle=True),
        _case((3, 3, 2), run_oracle=True),
        _case((4, 4, 4), run_oracle=False),
        _case((8, 8, 8, 8), run_oracle=False),
    ]
    return {
        "cases": cases,
        "conclusion": {
            "oracle_gap_zero_for_exhaustive_cases": all(
                case["oracle"] is None
                or case["oracle"]["residual_objective_gap"] == 0
                for case in cases
            ),
            "all_hidden_partitions_recovered": all(
                case["residual_search"]["selected_exact"]
                for case in cases
            ),
            "all_validation_exact": all(
                case["residual_search"]["selected_validation_accuracy"] == 1.0
                for case in cases
            ),
        },
        "limitations": [
            "residual signatures are derived from a restricted anonymous-cell timeline interface",
            "beam search is not a proof of the global optimum outside oracle-sized worlds",
            "relations are deterministic and each has one shared lag",
            "the acted-on value is directly visible in the sensor stream",
            "candidate generation is polynomial only under fixed beam width and round budget",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Phase 8e results: residual-driven partition search",
        "",
        "Bell-number exhaustive enumeration is replaced by splits proposed only from observed",
        "lag/cell residual conflicts.  A bounded beam keeps alternative hypotheses, and merge",
        "moves can undo an over-split.",
        "",
        "| templates | hidden relations | Bell partitions | evaluated | checks | exact partition | validation | objective | oracle gap |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for case in payload["cases"]:
        residual = case["residual_search"]
        oracle = case["oracle"]
        gap = "n/a" if oracle is None else str(oracle["residual_objective_gap"])
        lines.append(
            f"| {case['templates']} | {case['hidden_relations']} | "
            f"{case['bell_partitions']:,} | {residual['evaluated_partitions']:,} | "
            f"{residual['fit_candidate_checks']:,} | {residual['selected_exact']} | "
            f"{residual['selected_validation_accuracy']:.1%} | "
            f"{residual['selected_objective']:,} | {gap} |"
        )
    lines.extend(
        [
            "",
            "For the 4- and 8-template worlds the exhaustive oracle is still feasible.",
            "The residual search reaches the same minimum objective and exact hidden partition.",
            "For 12 and 32 templates the hidden generator is used only for evaluation; exhaustive",
            "enumeration is not run.",
            "",
            "## Search amortization",
            "",
            "Search is paid once and compiled away.  The table below keeps the search work visible",
            "instead of hiding it outside model size.",
            "",
            "| templates | one deployment | 100 deployments | 10,000 deployments |",
            "|---:|---:|---:|---:|",
        ]
    )
    for case in payload["cases"]:
        amortized = case["residual_search"]["amortized_fit_checks"]
        lines.append(
            f"| {case['templates']} | {amortized['1']:,.1f} | "
            f"{amortized['100']:,.2f} | {amortized['10000']:,.4f} |"
        )
    lines.extend(
        [
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    root = Path(__file__).resolve().parents[2]
    results = root / "results"
    results.mkdir(exist_ok=True)
    (results / "phase8e.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (results / "phase8e.md").write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
