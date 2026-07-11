from __future__ import annotations

import json
from pathlib import Path

from .latent_relation_partition import (
    EffectCandidate,
    TimelineTrace,
    bell_number,
    infer_effect_candidates,
    search_partitions,
)


TEMPLATES = (
    "{K}を{V}に移動",
    "{K}の場所を{V}にする",
    "{K}を{V}に渡す",
    "{K}の担当を{V}にする",
)
HIDDEN_RELATION = {
    TEMPLATES[0]: "location",
    TEMPLATES[1]: "location",
    TEMPLATES[2]: "owner",
    TEMPLATES[3]: "owner",
}
HIDDEN_LAG = {"location": 2, "owner": 1}


def _make_trace(
    entity: str,
    value: str,
    template: str,
    target_cell: str,
    lag: int,
    cells: tuple[str, ...],
    *,
    ambiguous_noise: bool = False,
) -> TimelineTrace:
    baseline = {cells[0]: "old0", cells[1]: "old1"}
    snapshots = [dict(baseline)]
    for step in range(1, 5):
        snapshot = dict(snapshots[-1])
        if ambiguous_noise and step == 1:
            other = cells[1] if target_cell == cells[0] else cells[0]
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


def _training() -> tuple[
    list[TimelineTrace],
    dict[str, tuple[str, ...]],
    dict[tuple[str, str], tuple[str, int]],
]:
    hidden_cells = {
        "箱A": {"location": "a0", "owner": "a1"},
        "箱B": {"location": "b1", "owner": "b0"},
        "箱C": {"location": "c0", "owner": "c1"},
        "箱D": {"location": "d1", "owner": "d0"},
    }
    entity_cells = {
        entity: tuple(sorted(assignments.values()))
        for entity, assignments in hidden_cells.items()
    }
    location_values = ("倉庫", "検査室", "棚B", "作業室")
    owner_values = ("佐藤", "田中", "山田", "鈴木")
    traces: list[TimelineTrace] = []
    hidden_targets: dict[tuple[str, str], tuple[str, int]] = {}
    for entity_index, entity in enumerate(hidden_cells):
        for template_index, template in enumerate(TEMPLATES):
            relation = HIDDEN_RELATION[template]
            values = (
                location_values if relation == "location" else owner_values
            )
            value = values[(entity_index + template_index) % len(values)]
            cell = hidden_cells[entity][relation]
            lag = HIDDEN_LAG[relation]
            traces.append(
                _make_trace(
                    entity,
                    value,
                    template,
                    cell,
                    lag,
                    entity_cells[entity],
                    ambiguous_noise=(entity == "箱D" and template_index == 0),
                )
            )
            hidden_targets[(entity, template)] = (cell, lag)
    return traces, entity_cells, hidden_targets


def _heldout() -> tuple[
    list[TimelineTrace],
    list[TimelineTrace],
    dict[str, tuple[str, ...]],
]:
    hidden_cells = {
        "箱E": {"location": "e1", "owner": "e0"},
        "箱F": {"location": "f0", "owner": "f1"},
    }
    entity_cells = {
        entity: tuple(sorted(assignments.values()))
        for entity, assignments in hidden_cells.items()
    }
    calibration: list[TimelineTrace] = []
    validation: list[TimelineTrace] = []
    for entity in hidden_cells:
        for template_index in (0, 2):
            template = TEMPLATES[template_index]
            relation = HIDDEN_RELATION[template]
            value = "保管庫" if relation == "location" else "高橋"
            calibration.append(
                _make_trace(
                    entity,
                    value,
                    template,
                    hidden_cells[entity][relation],
                    HIDDEN_LAG[relation],
                    entity_cells[entity],
                )
            )
        for template_index in (1, 3):
            template = TEMPLATES[template_index]
            relation = HIDDEN_RELATION[template]
            value = "実験台" if relation == "location" else "伊藤"
            validation.append(
                _make_trace(
                    entity,
                    value,
                    template,
                    hidden_cells[entity][relation],
                    HIDDEN_LAG[relation],
                    entity_cells[entity],
                )
            )
    return calibration, validation, entity_cells


def _canonical_partition(
    partition: tuple[tuple[int, ...], ...],
    templates: tuple[str, ...],
) -> set[frozenset[str]]:
    return {
        frozenset(templates[index] for index in block)
        for block in partition
    }


def _true_partition(templates: tuple[str, ...]) -> set[frozenset[str]]:
    grouped: dict[str, set[str]] = {}
    for template in templates:
        grouped.setdefault(HIDDEN_RELATION[template], set()).add(template)
    return {frozenset(items) for items in grouped.values()}


def _scaling_table() -> list[dict[str, int | float]]:
    rows = []
    relation_count = 2
    template_count = 32
    for entity_count in (8, 32, 128, 512):
        flat_bits = entity_count * template_count
        latent_bits = (
            entity_count * relation_count
            + template_count
            + relation_count * 27
        )
        rows.append(
            {
                "entities": entity_count,
                "templates": template_count,
                "flat_assignment_bits": flat_bits,
                "latent_partition_bits": latent_bits,
                "ratio": flat_bits / latent_bits,
            }
        )
    return rows


def run() -> dict[str, object]:
    training_traces, entity_cells, hidden_targets = _training()
    calibration_traces, validation_traces, heldout_cells = _heldout()
    evidence = [
        infer_effect_candidates(trace, entity_cells)
        for trace in training_traces
    ]
    calibration = [
        infer_effect_candidates(trace, heldout_cells)
        for trace in calibration_traces
    ]
    validation = [
        infer_effect_candidates(trace, heldout_cells)
        for trace in validation_traces
    ]
    templates = tuple(sorted({item.template for item in evidence}))
    models = search_partitions(
        templates,
        evidence,
        entity_cells,
        calibration,
        validation,
        max_lag=4,
    )
    selected = models[0]

    true_candidate_recall = 0
    ambiguous_count = 0
    ambiguous_resolved = False
    for item in evidence:
        target_cell, target_lag = hidden_targets[(item.entity, item.template)]
        if EffectCandidate(target_cell, target_lag) in item.candidates:
            true_candidate_recall += 1
        if len(item.candidates) > 1:
            ambiguous_count += 1
            template_index = templates.index(item.template)
            cluster_index = next(
                index
                for index, block in enumerate(selected.partition)
                if template_index in block
            )
            ambiguous_resolved = (
                selected.assignments[(cluster_index, item.entity)] == target_cell
                and selected.lags[cluster_index] == target_lag
            )

    partition_exact = (
        _canonical_partition(selected.partition, templates)
        == _true_partition(templates)
    )
    selected_relations = []
    for cluster_index, block in enumerate(selected.partition):
        relation_templates = [templates[index] for index in block]
        selected_relations.append(
            {
                "cluster": cluster_index,
                "templates": relation_templates,
                "lag": selected.lags[cluster_index],
            }
        )

    representative = {
        "selected_two_relation": selected,
        "merged_one_relation": next(
            model for model in models if len(model.partition) == 1
        ),
        "flat_four_relation": next(
            model for model in models if len(model.partition) == 4
        ),
        "best_three_relation": next(
            model for model in models if len(model.partition) == 3
        ),
    }

    return {
        "training_traces": len(training_traces),
        "templates": list(templates),
        "effect_candidate_recall": true_candidate_recall / len(evidence),
        "ambiguous_traces": ambiguous_count,
        "ambiguous_trace_resolved": ambiguous_resolved,
        "partition_search": {
            "evaluated_partitions": len(models),
            "selected_cluster_count": len(selected.partition),
            "selected_partition_exact": partition_exact,
            "selected_relations": selected_relations,
            "selected_train_errors": selected.train_errors,
            "new_entity_validation_accuracy": selected.validation_accuracy,
        },
        "representative_hypotheses": {
            name: {
                "partition": [list(block) for block in model.partition],
                "cluster_count": len(model.partition),
                "train_errors": model.train_errors,
                "description_bits": model.description_bits,
                "validation_accuracy": model.validation_accuracy,
                "objective": model.objective,
            }
            for name, model in representative.items()
        },
        "partition_search_scaling": [
            {"templates": count, "set_partitions": bell_number(count)}
            for count in (4, 6, 8, 10, 12)
        ],
        "representation_scaling": _scaling_table(),
        "limitations": [
            "entity-to-sensor-cell grouping is supplied by the interface",
            "the micro-world has exactly two deterministic relations per entity",
            "each latent relation has a fixed lag shared across entities",
            "the acted-on value is visible in both the utterance and sensor stream",
            "only four templates are searched exhaustively",
            "Bell-number partition growth makes the current search non-scalable",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    search = payload["partition_search"]
    hypotheses = payload["representative_hypotheses"]
    lines = [
        "# Phase 8d results: discovering relation partitions from anonymous sensor cells",
        "",
        "The learner is not given relation channels. It sees only entity-local anonymous sensor cells,",
        "utterances, values, and short post-action timelines.",
        "",
        f"- training traces: **{payload['training_traces']}**",
        f"- effect-candidate recall: **{payload['effect_candidate_recall']:.1%}**",
        f"- ambiguous traces: **{payload['ambiguous_traces']}**",
        f"- ambiguous trace resolved by shared structure: **{payload['ambiguous_trace_resolved']}**",
        f"- exhaustive partitions evaluated: **{search['evaluated_partitions']}**",
        f"- selected latent relations: **{search['selected_cluster_count']}**",
        f"- exact hidden partition recovery: **{search['selected_partition_exact']}**",
        f"- new-entity transfer after one calibration per relation: **{search['new_entity_validation_accuracy']:.1%}**",
        "",
        "## Hypothesis competition",
        "",
        "| hypothesis | clusters | train errors | bits | new-entity validation | objective |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in (
        "merged_one_relation",
        "best_three_relation",
        "flat_four_relation",
        "selected_two_relation",
    ):
        item = hypotheses[name]
        lines.append(
            f"| {name} | {item['cluster_count']} | {item['train_errors']} | "
            f"{item['description_bits']} | {item['validation_accuracy']:.1%} | "
            f"{item['objective']:,} |"
        )
    lines.extend(
        [
            "",
            "The two-relation partition groups the two location templates together and the two owner templates together.",
            "It recovers lag 2 for one cluster and lag 1 for the other without semantic relation labels.",
            "The four-cluster model memorizes each template separately, so one calibration template cannot transfer",
            "to its paraphrase on a new entity.",
            "",
            "## Exhaustive search growth",
            "",
            "| templates | set partitions |",
            "|---:|---:|",
        ]
    )
    for row in payload["partition_search_scaling"]:
        lines.append(f"| {row['templates']} | {row['set_partitions']:,} |")
    lines.extend(
        [
            "",
            "The current exhaustive oracle is useful only for tiny worlds. It is a measurement tool, not a scalable learner.",
            "",
            "## Representation scaling example",
            "",
            "For 32 surface templates generated by two latent relations:",
            "",
            "| entities | flat assignment bits | latent partition bits | ratio |",
            "|---:|---:|---:|---:|",
        ]
    )
    for row in payload["representation_scaling"]:
        lines.append(
            f"| {row['entities']} | {row['flat_assignment_bits']:,} | "
            f"{row['latent_partition_bits']:,} | {row['ratio']:.2f}x |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in payload["limitations"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase8d.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase8d.md").write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
