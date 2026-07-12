from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from statistics import median
from typing import Iterable, Sequence

from .benchmark_harness import BenchmarkExample
from .mixed_task_learner import (
    Hypothesis,
    MixedInteraction,
    MixedTaskModel,
    RoutingRule,
    _candidate_features,
    _fit_hypothesis,
    _fit_string_hypothesis,
    _hypothesis_accuracy,
    lexical_features,
    parse_prompt,
)
from .phase12a_experiment import calibration_interactions, synthetic_examples
from .phase17a_resource_scaling import (
    consolidate_to_budget,
    evaluate_blind_suite,
    select_training_evidence,
    validation_interactions,
)


@dataclass(frozen=True)
class FactorialBudget:
    name: str
    varied_axis: str
    acquired_bits: int
    evidence_bits: int
    induction_evaluations: int
    inference_operations_per_item: int
    per_fit_ceiling: int = 20_000


SEEDS = (17, 29, 43)

# Every sweep holds the other three resources at the common anchor. This is a
# one-factor-at-a-time identification pilot, not yet a dense four-dimensional grid.
ANCHOR = FactorialBudget(
    "anchor",
    "anchor",
    8 * 1024 * 8,
    512 * 1024 * 8,
    100_000,
    256,
)
FACTORIAL_POINTS = (
    FactorialBudget(
        "size-128b",
        "acquired_bits",
        128 * 8,
        ANCHOR.evidence_bits,
        ANCHOR.induction_evaluations,
        ANCHOR.inference_operations_per_item,
    ),
    FactorialBudget(
        "size-512b",
        "acquired_bits",
        512 * 8,
        ANCHOR.evidence_bits,
        ANCHOR.induction_evaluations,
        ANCHOR.inference_operations_per_item,
    ),
    FactorialBudget(
        "evidence-4kib",
        "evidence_bits",
        ANCHOR.acquired_bits,
        4 * 1024 * 8,
        ANCHOR.induction_evaluations,
        ANCHOR.inference_operations_per_item,
    ),
    FactorialBudget(
        "evidence-32kib",
        "evidence_bits",
        ANCHOR.acquired_bits,
        32 * 1024 * 8,
        ANCHOR.induction_evaluations,
        ANCHOR.inference_operations_per_item,
    ),
    FactorialBudget(
        "induce-500",
        "induction_evaluations",
        ANCHOR.acquired_bits,
        ANCHOR.evidence_bits,
        500,
        ANCHOR.inference_operations_per_item,
        500,
    ),
    FactorialBudget(
        "induce-5k",
        "induction_evaluations",
        ANCHOR.acquired_bits,
        ANCHOR.evidence_bits,
        5_000,
        ANCHOR.inference_operations_per_item,
        5_000,
    ),
    FactorialBudget(
        "infer-8",
        "inference_operations_per_item",
        ANCHOR.acquired_bits,
        ANCHOR.evidence_bits,
        ANCHOR.induction_evaluations,
        8,
    ),
    FactorialBudget(
        "infer-32",
        "inference_operations_per_item",
        ANCHOR.acquired_bits,
        ANCHOR.evidence_bits,
        ANCHOR.induction_evaluations,
        32,
    ),
    ANCHOR,
)

AXIS_SWEEPS = {
    "acquired_bits": ("size-128b", "size-512b", "anchor"),
    "evidence_bits": ("evidence-4kib", "evidence-32kib", "anchor"),
    "induction_evaluations": ("induce-500", "induce-5k", "anchor"),
    "inference_operations_per_item": ("infer-8", "infer-32", "anchor"),
}


def _budgeted_fit(
    examples: Sequence[MixedInteraction],
    *,
    remaining_evaluations: int,
    per_fit_ceiling: int,
) -> tuple[Hypothesis | None, int]:
    """Fit without ever spending more than the remaining campaign budget."""

    if remaining_evaluations <= 0 or not examples:
        return None, 0

    # The string primitive path reports one evaluation per example and otherwise
    # ignores max_candidates, so account for it explicitly before delegating.
    string_hypothesis = _fit_string_hypothesis(examples)
    if string_hypothesis is not None:
        cost = len(examples)
        if cost > remaining_evaluations:
            return None, 0
        return string_hypothesis, cost

    allowance = min(remaining_evaluations, per_fit_ceiling)
    if allowance <= 0:
        return None, 0
    hypothesis, cost = _fit_hypothesis(examples, max_candidates=allowance)
    if cost > allowance:
        raise RuntimeError("fit routine exceeded its declared candidate allowance")
    return hypothesis, cost


def induce_globally_budgeted_model(
    calibration: Iterable[MixedInteraction],
    *,
    global_candidate_budget: int,
    per_fit_ceiling: int = 20_000,
) -> tuple[MixedTaskModel, int, bool]:
    """Induce expressible subsets under a strict campaign-wide search limit."""

    examples = tuple(calibration)
    if global_candidate_budget < 0:
        raise ValueError("global candidate budget must be non-negative")
    if per_fit_ceiling < 1:
        raise ValueError("per-fit ceiling must be positive")
    if not examples:
        return MixedTaskModel(tuple(), 0, 0), 0, False

    buckets: dict[
        tuple[tuple[str, ...], tuple[str, ...]], list[MixedInteraction]
    ] = {}
    for example in examples:
        parsed = parse_prompt(example.prompt)
        if (
            parsed.arguments != example.trace.arguments
            or parsed.before != example.trace.before
        ):
            raise ValueError("calibration trace does not match generic prompt extraction")
        buckets.setdefault(parsed.signature, []).append(example)

    rules: list[RoutingRule] = []
    evaluations = 0
    unresolved = 0

    def fit(rows: Sequence[MixedInteraction]) -> Hypothesis | None:
        nonlocal evaluations
        hypothesis, cost = _budgeted_fit(
            rows,
            remaining_evaluations=global_candidate_budget - evaluations,
            per_fit_ceiling=per_fit_ceiling,
        )
        evaluations += cost
        if evaluations > global_candidate_budget:
            raise RuntimeError("global induction budget exceeded")
        return hypothesis

    for signature, bucket_rows in sorted(buckets.items(), key=lambda row: repr(row[0])):
        if evaluations >= global_candidate_budget:
            unresolved += len(bucket_rows)
            continue

        remaining = list(bucket_rows)
        whole = fit(remaining)
        if whole is not None:
            rules.append(RoutingRule(signature, None, whole, len(remaining)))
            continue

        features = _candidate_features(remaining)
        while remaining:
            best: tuple[
                tuple[int, int, int, str],
                str,
                Hypothesis,
                list[MixedInteraction],
            ] | None = None
            for feature in features:
                if evaluations >= global_candidate_budget:
                    break
                covered = [
                    example
                    for example in remaining
                    if feature in lexical_features(example.prompt)
                ]
                if len(covered) < 2:
                    continue
                before = evaluations
                hypothesis = fit(covered)
                fit_cost = evaluations - before
                if (
                    hypothesis is None
                    or _hypothesis_accuracy(hypothesis, covered) != 1.0
                ):
                    continue
                score = (
                    len(covered),
                    -hypothesis.description_bits,
                    -fit_cost,
                    feature,
                )
                if best is None or score > best[0]:
                    best = (score, feature, hypothesis, covered)

            if best is None:
                fallback = fit(remaining)
                if fallback is None:
                    unresolved += len(remaining)
                    break
                rules.append(RoutingRule(signature, None, fallback, len(remaining)))
                remaining.clear()
                break

            _, feature, hypothesis, covered = best
            rules.append(RoutingRule(signature, feature, hypothesis, len(covered)))
            covered_ids = {id(example) for example in covered}
            remaining = [
                example for example in remaining if id(example) not in covered_ids
            ]

    exhausted = evaluations >= global_candidate_budget and unresolved > 0
    model = MixedTaskModel(tuple(rules), evaluations, len(examples))
    return model, unresolved, exhausted


def run_point(
    budget: FactorialBudget,
    *,
    seed: int,
    training: Sequence[MixedInteraction],
    validation: Sequence[MixedInteraction],
    blind_examples: Sequence[BenchmarkExample],
) -> dict[str, object]:
    selected, evidence_bits = select_training_evidence(
        training,
        evidence_budget_bits=budget.evidence_bits,
        seed=seed,
    )
    full_model, unresolved, exhausted = induce_globally_budgeted_model(
        selected,
        global_candidate_budget=budget.induction_evaluations,
        per_fit_ceiling=budget.per_fit_ceiling,
    )
    acquired = consolidate_to_budget(
        full_model,
        acquired_budget_bits=budget.acquired_bits,
        validation=validation,
        operation_cap=budget.inference_operations_per_item,
    )
    score = evaluate_blind_suite(
        acquired,
        blind_examples,
        operation_cap=budget.inference_operations_per_item,
    )

    if acquired.description_bits > budget.acquired_bits:
        raise RuntimeError("consolidated model exceeds acquired-bit budget")
    if evidence_bits > budget.evidence_bits:
        raise RuntimeError("selected evidence exceeds evidence-bit budget")
    if full_model.candidate_evaluations > budget.induction_evaluations:
        raise RuntimeError("model exceeds strict global induction budget")

    return {
        "budget": asdict(budget),
        "seed": seed,
        "selected_training_examples": len(selected),
        "resolved_training_examples": len(selected) - unresolved,
        "unresolved_training_examples": unresolved,
        "training_evidence_bits": evidence_bits,
        "full_model_bits": full_model.description_bits,
        "acquired_model_bits": acquired.description_bits,
        "full_rules": len(full_model.rules),
        "selected_rules": len(acquired.rules),
        "candidate_evaluations": full_model.candidate_evaluations,
        "induction_budget_exhausted": exhausted,
        **score,
    }


def _summarize(points: Sequence[dict[str, object]]) -> dict[str, object]:
    budget = points[0]["budget"]
    return {
        "name": budget["name"],
        "varied_axis": budget["varied_axis"],
        "budget": budget,
        "seeds": len(points),
        "median_accuracy": median(float(row["accuracy"]) for row in points),
        "median_coverage": median(float(row["coverage"]) for row in points),
        "median_selective_accuracy": median(
            float(row["selective_accuracy"]) for row in points
        ),
        "median_acquired_bits": median(
            int(row["acquired_model_bits"]) for row in points
        ),
        "median_evidence_bits": median(
            int(row["training_evidence_bits"]) for row in points
        ),
        "median_candidate_evaluations": median(
            int(row["candidate_evaluations"]) for row in points
        ),
        "median_selected_rules": median(int(row["selected_rules"]) for row in points),
        "median_resolved_training_examples": median(
            int(row["resolved_training_examples"]) for row in points
        ),
    }


def _axis_value(summary: dict[str, object], axis: str) -> int:
    return int(summary["budget"][axis])


def _axis_frontiers(
    summaries_by_name: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for axis, names in AXIS_SWEEPS.items():
        ordered = sorted(
            (summaries_by_name[name] for name in names),
            key=lambda row: _axis_value(row, axis),
        )
        rows.append(
            {
                "axis": axis,
                "points": [
                    {
                        "name": row["name"],
                        "resource": _axis_value(row, axis),
                        "median_accuracy": row["median_accuracy"],
                        "median_coverage": row["median_coverage"],
                        "median_selective_accuracy": row[
                            "median_selective_accuracy"
                        ],
                    }
                    for row in ordered
                ],
                "accuracy_gain_low_to_high": (
                    float(ordered[-1]["median_accuracy"])
                    - float(ordered[0]["median_accuracy"])
                ),
                "coverage_gain_low_to_high": (
                    float(ordered[-1]["median_coverage"])
                    - float(ordered[0]["median_coverage"])
                ),
            }
        )
    return rows


def run() -> dict[str, object]:
    training = calibration_interactions()
    validation = validation_interactions()
    blind = synthetic_examples()

    rows = [
        run_point(
            budget,
            seed=seed,
            training=training,
            validation=validation,
            blind_examples=blind,
        )
        for budget in FACTORIAL_POINTS
        for seed in SEEDS
    ]
    summaries = [
        _summarize(
            [row for row in rows if row["budget"]["name"] == budget.name]
        )
        for budget in FACTORIAL_POINTS
    ]
    by_name = {str(row["name"]): row for row in summaries}
    axis_frontiers = _axis_frontiers(by_name)
    dominant = max(
        axis_frontiers,
        key=lambda row: (
            float(row["accuracy_gain_low_to_high"]),
            float(row["coverage_gain_low_to_high"]),
            str(row["axis"]),
        ),
    )

    return {
        "campaign": {
            "name": "phase17c-factorial-resource-identification-c1",
            "predecessor": "phase17b selective mixed learner",
            "architecture_change": (
                "strict global candidate budget; learner language and parser unchanged"
            ),
            "training_examples": len(training),
            "selection_examples": len(validation),
            "blind_examples": len(blind),
            "public_benchmark_examples_used": 0,
            "trained_from_scratch_per_point": True,
            "seeds": list(SEEDS),
            "factorial_design": "one-factor-at-a-time around one shared high-resource anchor",
        },
        "budget_runs": rows,
        "summaries": summaries,
        "axis_frontiers": axis_frontiers,
        "dominant_observed_resource": dominant["axis"],
        "gates": {
            "acquired_bits_hard_limited": True,
            "evidence_bits_hard_limited": True,
            "strict_global_induction_budget": True,
            "inference_operations_hard_limited": True,
            "resource_axes_varied_independently": True,
            "dense_interaction_grid_complete": False,
            "larger_blind_distribution_complete": False,
            "held_out_high_budget_forecast_validated": False,
            "high_budget_extrapolation_allowed": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "one-factor-at-a-time sweeps do not identify interactions among resource axes",
            "the task distribution is still the narrow generated Phase 12 mixture",
            "validation examples participate in size-constrained rule consolidation",
            "the fixed parser and hypothesis language remain human-designed",
            "this experiment diagnoses the present learner and cannot forecast GiB-scale parity",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Phase 17c results: independently varied resource axes",
        "",
        "Phase 17c keeps the Phase 17b parser and hypothesis language but replaces",
        "the per-fit-only search cap with a strict campaign-wide induction budget.",
        "Each sweep varies one resource while the other three remain at one shared",
        "high-resource anchor.",
        "",
        "| point | varied axis | acquired cap | evidence cap | induction cap | inference cap | median accuracy | median coverage | selective accuracy | acquired bits | candidate evals |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["summaries"]:
        budget = row["budget"]
        lines.append(
            f"| {row['name']} | {row['varied_axis']} | {budget['acquired_bits']} | "
            f"{budget['evidence_bits']} | {budget['induction_evaluations']} | "
            f"{budget['inference_operations_per_item']} | "
            f"{100 * row['median_accuracy']:.1f}% | "
            f"{100 * row['median_coverage']:.1f}% | "
            f"{100 * row['median_selective_accuracy']:.1f}% | "
            f"{row['median_acquired_bits']:.0f} | "
            f"{row['median_candidate_evaluations']:.0f} |"
        )

    lines.extend(
        [
            "",
            "## Observed one-axis sensitivity",
            "",
            "| resource | accuracy gain, low to high | coverage gain, low to high |",
            "|---|---:|---:|",
        ]
    )
    for row in payload["axis_frontiers"]:
        lines.append(
            f"| {row['axis']} | "
            f"{100 * row['accuracy_gain_low_to_high']:.1f} points | "
            f"{100 * row['coverage_gain_low_to_high']:.1f} points |"
        )
    lines.extend(
        [
            "",
            f"Dominant observed resource in this narrow pilot: **{payload['dominant_observed_resource']}**.",
            "",
            "## Claim boundary",
            "",
            "This identifies bottlenecks of the current tiny learner. It is not a",
            "GiB-scale forecast and does not support a general-LLM parity claim.",
            "The next campaign must expand the frozen blind distribution and reserve",
            "larger budget points for genuine out-of-sample forecast validation.",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase17c.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase17c.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
