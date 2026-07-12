from __future__ import annotations

from dataclasses import asdict
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
    _hypothesis_accuracy,
    lexical_features,
    parse_prompt,
)
from .phase12a_experiment import calibration_interactions, synthetic_examples
from .phase17a_resource_scaling import (
    PILOT_BUDGETS,
    PILOT_SEEDS,
    ScalingBudget,
    consolidate_to_budget,
    evaluate_blind_suite,
    select_training_evidence,
    validation_interactions,
)


def induce_partial_mixed_task_model(
    calibration: Iterable[MixedInteraction],
    *,
    max_candidates_per_fit: int,
) -> tuple[MixedTaskModel, int]:
    """Induce every expressible subset and abstain on the unresolved remainder.

    The original mixed learner is intentionally strict: if even one residual bucket
    is not expressible, construction raises and no model is returned. That is useful
    for exact Phase 12 reproduction but invalid for a size/capability curve because
    one missing mechanism erases already acquired skills. This variant keeps the
    same parser, hypothesis language, feature generator, and fit routine; it changes
    only the acceptance policy from all-or-nothing to selective prediction.
    """

    examples = tuple(calibration)
    if not examples:
        return MixedTaskModel(tuple(), 0, 0), 0
    if max_candidates_per_fit < 1:
        raise ValueError("max_candidates_per_fit must be positive")

    buckets: dict[
        tuple[tuple[str, ...], tuple[str, ...]], list[MixedInteraction]
    ] = {}
    for example in examples:
        parsed = parse_prompt(example.prompt)
        if parsed.arguments != example.trace.arguments or parsed.before != example.trace.before:
            raise ValueError("calibration trace does not match generic prompt extraction")
        buckets.setdefault(parsed.signature, []).append(example)

    rules: list[RoutingRule] = []
    evaluations = 0
    unresolved = 0

    for signature, bucket_rows in sorted(buckets.items(), key=lambda row: repr(row[0])):
        remaining = list(bucket_rows)
        whole, cost = _fit_hypothesis(
            remaining,
            max_candidates=max_candidates_per_fit,
        )
        evaluations += cost
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
                covered = [
                    example
                    for example in remaining
                    if feature in lexical_features(example.prompt)
                ]
                if len(covered) < 2:
                    continue
                hypothesis, fit_cost = _fit_hypothesis(
                    covered,
                    max_candidates=max_candidates_per_fit,
                )
                evaluations += fit_cost
                if hypothesis is None or _hypothesis_accuracy(hypothesis, covered) != 1.0:
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
                fallback, fit_cost = _fit_hypothesis(
                    remaining,
                    max_candidates=max_candidates_per_fit,
                )
                evaluations += fit_cost
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

    return MixedTaskModel(tuple(rules), evaluations, len(examples)), unresolved


def run_budget_point(
    budget: ScalingBudget,
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
    full_model, unresolved = induce_partial_mixed_task_model(
        selected,
        max_candidates_per_fit=budget.candidate_cap_per_fit,
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
        **score,
    }


def run() -> dict[str, object]:
    training = calibration_interactions()
    validation = validation_interactions()
    blind = synthetic_examples()
    rows = [
        run_budget_point(
            budget,
            seed=seed,
            training=training,
            validation=validation,
            blind_examples=blind,
        )
        for budget in PILOT_BUDGETS
        for seed in PILOT_SEEDS
    ]

    summaries = []
    for budget in PILOT_BUDGETS:
        points = [row for row in rows if row["budget"]["name"] == budget.name]
        summaries.append(
            {
                "budget": asdict(budget),
                "seeds": len(points),
                "median_accuracy": median(float(row["accuracy"]) for row in points),
                "median_coverage": median(float(row["coverage"]) for row in points),
                "median_selective_accuracy": median(
                    float(row["selective_accuracy"]) for row in points
                ),
                "median_acquired_bits": median(
                    int(row["acquired_model_bits"]) for row in points
                ),
                "median_selected_rules": median(
                    int(row["selected_rules"]) for row in points
                ),
                "median_resolved_training_examples": median(
                    int(row["resolved_training_examples"]) for row in points
                ),
                "median_candidate_evaluations": median(
                    int(row["candidate_evaluations"]) for row in points
                ),
            }
        )

    monotone_best_accuracy = []
    best = 0.0
    for summary in summaries:
        best = max(best, float(summary["median_accuracy"]))
        monotone_best_accuracy.append(best)

    return {
        "campaign": {
            "name": "phase17b-selective-mixed-learner-resource-scaling-c1",
            "predecessor": "phase17a fail-fast measurement",
            "architecture_change": "accept expressible subsets and abstain on unresolved calibration rows",
            "training_examples": len(training),
            "selection_examples": len(validation),
            "blind_examples": len(blind),
            "public_benchmark_examples_used": 0,
            "same_parser_hypothesis_language_and_fit_routine": True,
            "trained_from_scratch_per_point": True,
            "seeds": list(PILOT_SEEDS),
        },
        "budget_runs": rows,
        "summaries": summaries,
        "monotone_best_accuracy": monotone_best_accuracy,
        "gates": {
            "acquired_bits_hard_limited": True,
            "evidence_bits_hard_limited": True,
            "inference_operations_hard_limited": True,
            "unresolved_training_rows_cause_abstention_not_global_failure": True,
            "candidate_cap_is_per_fit_not_global": True,
            "strict_global_induction_budget": False,
            "independent_resource_exponents_identified": False,
            "high_budget_extrapolation_allowed": False,
            "public_transfer_claim_allowed": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "resource axes still grow together, so independent scaling exponents cannot be identified",
            "the candidate cap is per fitting call rather than a strict campaign-wide interruption",
            "the validation set participates in rule consolidation and is separate from but related to the generated blind families",
            "the task distribution is narrow and generated",
            "the fixed parser and hypothesis language contain human-designed inductive bias",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Phase 17b results: selective resource-capability scaling",
        "",
        "Phase 17a erased all learned skills when one residual bucket was not",
        "expressible. Phase 17b preserves every induced rule and abstains only on",
        "unresolved rows, without changing the parser, hypothesis language, feature",
        "generator, or fitting routine.",
        "",
        "| point | acquired cap | evidence cap | candidate cap/fit | inference cap | median accuracy | median coverage | selective accuracy | acquired bits | rules | resolved train |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["summaries"]:
        budget = row["budget"]
        lines.append(
            f"| {budget['name']} | {budget['acquired_bits']} | {budget['evidence_bits']} | "
            f"{budget['candidate_cap_per_fit']} | {budget['inference_operations_per_item']} | "
            f"{100 * row['median_accuracy']:.1f}% | {100 * row['median_coverage']:.1f}% | "
            f"{100 * row['median_selective_accuracy']:.1f}% | {row['median_acquired_bits']:.0f} | "
            f"{row['median_selected_rules']:.0f} | {row['median_resolved_training_examples']:.0f} |"
        )
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "This is the first non-degenerate pilot curve, not a fitted scaling law.",
            "A strict global induction budget, factorial resource grid, larger blind",
            "distribution, and held-out high-budget forecast points are still required.",
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
    (output / "phase17b.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase17b.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
