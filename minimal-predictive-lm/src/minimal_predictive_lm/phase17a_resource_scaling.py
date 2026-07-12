from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import random
from statistics import median
from typing import Iterable, Sequence

from .benchmark_harness import ABSTAIN_TOKEN, BenchmarkExample, answer_is_correct
from .mixed_task_learner import (
    MixedInteraction,
    MixedTaskModel,
    RoutingRule,
    induce_mixed_task_model,
    interaction_from_observation,
)
from .phase12a_experiment import calibration_interactions, synthetic_examples
from .universal_program_induction import UnexpressibleTaskError


@dataclass(frozen=True)
class ScalingBudget:
    name: str
    acquired_bits: int
    evidence_bits: int
    candidate_cap_per_fit: int
    inference_operations_per_item: int


@dataclass(frozen=True)
class BudgetRun:
    budget: ScalingBudget
    seed: int
    selected_training_examples: int
    training_evidence_bits: int
    training_failed: bool
    training_failure: str | None
    full_model_bits: int
    acquired_model_bits: int
    selected_rules: int
    candidate_evaluations: int
    examples: int
    answered: int
    correct: int
    accuracy: float
    coverage: float
    selective_accuracy: float
    axis_scores: dict[str, dict[str, float | int]]


PILOT_BUDGETS = (
    ScalingBudget("b128", 128 * 8, 4 * 1024 * 8, 500, 8),
    ScalingBudget("b256", 256 * 8, 8 * 1024 * 8, 2_000, 16),
    ScalingBudget("b512", 512 * 8, 16 * 1024 * 8, 5_000, 32),
    ScalingBudget("b1k", 1024 * 8, 32 * 1024 * 8, 20_000, 64),
    ScalingBudget("b4k", 4 * 1024 * 8, 256 * 1024 * 8, 20_000, 256),
)
PILOT_SEEDS = (17, 29, 43)


def _json_bits(payload: object) -> int:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return len(encoded) * 8


def interaction_evidence_bits(interaction: MixedInteraction) -> int:
    trace = interaction.trace
    return _json_bits(
        {
            "prompt": interaction.prompt,
            "arguments": trace.arguments,
            "before": trace.before,
            "after": trace.after,
            "output": trace.output,
        }
    )


def select_training_evidence(
    interactions: Sequence[MixedInteraction],
    *,
    evidence_budget_bits: int,
    seed: int,
) -> tuple[tuple[MixedInteraction, ...], int]:
    if evidence_budget_bits < 0:
        raise ValueError("evidence budget must be non-negative")
    order = list(range(len(interactions)))
    random.Random(seed).shuffle(order)
    selected: list[MixedInteraction] = []
    used = 0
    for index in order:
        row = interactions[index]
        bits = interaction_evidence_bits(row)
        if used + bits > evidence_budget_bits:
            continue
        selected.append(row)
        used += bits
    return tuple(selected), used


def validation_interactions() -> tuple[MixedInteraction, ...]:
    rows: list[MixedInteraction] = []
    for prompt, answer in (
        ("What is 310019 plus 270031?", 580050),
        ("What is 920041 minus 410017?", 510024),
        ("What is 4013 times 19?", 76247),
        ("What is 630063 divided by 7?", 90009),
    ):
        rows.append(interaction_from_observation(prompt, output=answer))

    for count, delta in ((4, 19), (28, 15), (63, 22), (140, 17)):
        total = count + delta
        rows.append(
            interaction_from_observation(
                f"state_count={count} delta={delta}",
                after={"count": total},
                output=total,
            )
        )

    for status, yes_value, no_value in (
        ("ready", "ENTER", "WAIT"),
        ("busy", "OPEN", "SHUT"),
        ("blocked", "START", "STOP"),
        ("paused", "LEFT", "RIGHT"),
    ):
        rows.append(
            interaction_from_observation(
                f"choose status={status} yes={yes_value} no={no_value}",
                output=yes_value if status == "ready" else no_value,
            )
        )

    for source, target in (
        ("budgetcurve", "cvehfudvswf"),
        ("scalinglaw", "tdbmjohmbx"),
        ("cvehfudvswf", "budgetcurve"),
        ("tdbmjohmbx", "scalinglaw"),
    ):
        direction = "forward" if source[0] not in {"c", "t"} else "backward"
        rows.append(
            interaction_from_observation(
                f"convert {direction} value={source}", output=target
            )
        )

    for left, right in (
        ("resource", "frontier"),
        ("blind", "transfer"),
        ("model", "budget"),
        ("proof", "cost"),
    ):
        rows.append(
            interaction_from_observation(
                f"join left={left} right={right}", output=left + right
            )
        )

    for value, source in (
        ("verified", "audit17"),
        ("shifted", "suite21"),
        ("stable", "run33"),
        ("bounded", "ledger8"),
    ):
        rows.append(
            interaction_from_observation(
                f"claim value={value} source={source}", output=source
            )
        )

    for before, after in (
        ("theta", "THETA"),
        ("sigma", "SIGMA"),
        ("budget", "BUDGET"),
        ("frontier", "FRONTIER"),
    ):
        rows.append(
            interaction_from_observation(
                f"event before={before} after={after} result=PASS", output=before
            )
        )
    return tuple(rows)


def _empty_model(*, candidate_evaluations: int, calibration_examples: int) -> MixedTaskModel:
    return MixedTaskModel(
        rules=tuple(),
        candidate_evaluations=candidate_evaluations,
        calibration_examples=calibration_examples,
    )


def _prediction_text(model: MixedTaskModel, prompt: str, operation_cap: int) -> str:
    prediction = model.predict(prompt)
    if prediction.output is None or prediction.operations > operation_cap:
        return ABSTAIN_TOKEN
    if isinstance(prediction.output, bool):
        return "true" if prediction.output else "false"
    return str(prediction.output)


def _interaction_correct_count(
    model: MixedTaskModel,
    interactions: Iterable[MixedInteraction],
    *,
    operation_cap: int,
) -> int:
    correct = 0
    for row in interactions:
        prediction = model.predict(row.prompt)
        if prediction.output is None or prediction.operations > operation_cap:
            continue
        correct += int(
            prediction.output == row.trace.output
            and tuple(prediction.after) == tuple(row.trace.after)
        )
    return correct


def _model_from_rule_indexes(
    full_model: MixedTaskModel,
    indexes: Iterable[int],
) -> MixedTaskModel:
    chosen = set(indexes)
    rules = tuple(
        rule for index, rule in enumerate(full_model.rules) if index in chosen
    )
    return MixedTaskModel(
        rules=rules,
        candidate_evaluations=full_model.candidate_evaluations,
        calibration_examples=full_model.calibration_examples,
        domain_specific_handlers=full_model.domain_specific_handlers,
    )


def consolidate_to_budget(
    full_model: MixedTaskModel,
    *,
    acquired_budget_bits: int,
    validation: Sequence[MixedInteraction],
    operation_cap: int,
) -> MixedTaskModel:
    if acquired_budget_bits < 0:
        raise ValueError("acquired budget must be non-negative")
    if full_model.description_bits <= acquired_budget_bits:
        return full_model

    current_indexes: set[int] = set()
    current = _model_from_rule_indexes(full_model, current_indexes)
    if current.description_bits > acquired_budget_bits:
        return current
    current_correct = _interaction_correct_count(
        current, validation, operation_cap=operation_cap
    )

    remaining = set(range(len(full_model.rules)))
    while remaining:
        best: tuple[tuple[float, int, int, int], int, MixedTaskModel, int] | None = None
        for index in sorted(remaining):
            candidate_indexes = current_indexes | {index}
            candidate = _model_from_rule_indexes(full_model, candidate_indexes)
            if candidate.description_bits > acquired_budget_bits:
                continue
            candidate_correct = _interaction_correct_count(
                candidate, validation, operation_cap=operation_cap
            )
            gain = candidate_correct - current_correct
            if gain <= 0:
                continue
            delta_bits = max(1, candidate.description_bits - current.description_bits)
            key = (
                gain / delta_bits,
                gain,
                -candidate.description_bits,
                -index,
            )
            if best is None or key > best[0]:
                best = (key, index, candidate, candidate_correct)
        if best is None:
            break
        _, index, current, current_correct = best
        current_indexes.add(index)
        remaining.remove(index)
    return current


def evaluate_blind_suite(
    model: MixedTaskModel,
    examples: Sequence[BenchmarkExample],
    *,
    operation_cap: int,
) -> dict[str, object]:
    answered = 0
    correct = 0
    axes: dict[str, dict[str, int]] = {}
    for example in examples:
        text = _prediction_text(model, example.prompt, operation_cap)
        is_answered = text != ABSTAIN_TOKEN
        is_correct = answer_is_correct(example, text)
        answered += int(is_answered)
        correct += int(is_correct)
        row = axes.setdefault(
            example.axis,
            {"examples": 0, "answered": 0, "correct": 0},
        )
        row["examples"] += 1
        row["answered"] += int(is_answered)
        row["correct"] += int(is_correct)

    axis_scores: dict[str, dict[str, float | int]] = {}
    for axis, row in sorted(axes.items()):
        examples_count = row["examples"]
        answered_count = row["answered"]
        axis_scores[axis] = {
            **row,
            "accuracy": row["correct"] / examples_count,
            "coverage": answered_count / examples_count,
            "selective_accuracy": (
                row["correct"] / answered_count if answered_count else 0.0
            ),
        }
    examples_count = len(examples)
    return {
        "examples": examples_count,
        "answered": answered,
        "correct": correct,
        "accuracy": correct / examples_count if examples_count else 0.0,
        "coverage": answered / examples_count if examples_count else 0.0,
        "selective_accuracy": correct / answered if answered else 0.0,
        "axis_scores": axis_scores,
    }


def run_budget_point(
    budget: ScalingBudget,
    *,
    seed: int,
    training: Sequence[MixedInteraction],
    validation: Sequence[MixedInteraction],
    blind_examples: Sequence[BenchmarkExample],
) -> BudgetRun:
    selected, evidence_bits = select_training_evidence(
        training,
        evidence_budget_bits=budget.evidence_bits,
        seed=seed,
    )

    training_failed = False
    failure: str | None = None
    if not selected:
        full_model = _empty_model(candidate_evaluations=0, calibration_examples=0)
        training_failed = True
        failure = "no interaction fits within evidence budget"
    else:
        try:
            full_model = induce_mixed_task_model(
                selected,
                max_candidates_per_fit=budget.candidate_cap_per_fit,
            )
        except (UnexpressibleTaskError, ValueError, RuntimeError) as exc:
            full_model = _empty_model(
                candidate_evaluations=budget.candidate_cap_per_fit,
                calibration_examples=len(selected),
            )
            training_failed = True
            failure = f"{type(exc).__name__}: {exc}"

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

    return BudgetRun(
        budget=budget,
        seed=seed,
        selected_training_examples=len(selected),
        training_evidence_bits=evidence_bits,
        training_failed=training_failed,
        training_failure=failure,
        full_model_bits=full_model.description_bits,
        acquired_model_bits=acquired.description_bits,
        selected_rules=len(acquired.rules),
        candidate_evaluations=full_model.candidate_evaluations,
        examples=int(score["examples"]),
        answered=int(score["answered"]),
        correct=int(score["correct"]),
        accuracy=float(score["accuracy"]),
        coverage=float(score["coverage"]),
        selective_accuracy=float(score["selective_accuracy"]),
        axis_scores=score["axis_scores"],  # type: ignore[arg-type]
    )


def _campaign_fingerprint(
    training: Sequence[MixedInteraction],
    validation: Sequence[MixedInteraction],
    blind: Sequence[BenchmarkExample],
) -> str:
    payload = {
        "training": [row.prompt for row in training],
        "validation": [row.prompt for row in validation],
        "blind_ids": [row.example_id for row in blind],
        "budgets": [asdict(row) for row in PILOT_BUDGETS],
        "seeds": list(PILOT_SEEDS),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def run() -> dict[str, object]:
    training = calibration_interactions()
    validation = validation_interactions()
    blind = synthetic_examples()
    runs = [
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
        rows = [row for row in runs if row.budget.name == budget.name]
        summaries.append(
            {
                "budget": asdict(budget),
                "seeds": len(rows),
                "median_accuracy": median(row.accuracy for row in rows),
                "median_coverage": median(row.coverage for row in rows),
                "median_selective_accuracy": median(
                    row.selective_accuracy for row in rows
                ),
                "median_acquired_bits": median(
                    row.acquired_model_bits for row in rows
                ),
                "median_candidate_evaluations": median(
                    row.candidate_evaluations for row in rows
                ),
                "training_failures": sum(row.training_failed for row in rows),
            }
        )

    return {
        "campaign": {
            "name": "phase17a-mixed-learner-resource-scaling-pilot-c1",
            "fingerprint": _campaign_fingerprint(training, validation, blind),
            "training_examples": len(training),
            "selection_examples": len(validation),
            "blind_examples": len(blind),
            "public_benchmark_examples_used": 0,
            "architecture_frozen_across_points": True,
            "trained_from_scratch_per_point": True,
            "seeds": list(PILOT_SEEDS),
        },
        "budget_runs": [
            {
                **asdict(row),
                "budget": asdict(row.budget),
            }
            for row in runs
        ],
        "summaries": summaries,
        "gates": {
            "acquired_bits_hard_limited": True,
            "evidence_bits_hard_limited": True,
            "inference_operations_hard_limited": True,
            "candidate_cap_is_per_fit_not_global": True,
            "strict_global_induction_budget": False,
            "scaling_extrapolation_allowed": False,
            "public_transfer_claim_allowed": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "the pilot varies several resource axes together and cannot identify independent exponents",
            "candidate search is capped per fitting attempt; total candidate evaluations are measured but not interrupted globally",
            "the blind suite is generated and narrow rather than a broad public intelligence evaluation",
            "the fixed parser and primitive language already encode substantial human knowledge",
            "three seeds and five budget points are insufficient for a reliable high-budget forecast",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    campaign = payload["campaign"]
    lines = [
        "# Phase 17a results: resource-capability scaling pilot",
        "",
        "A frozen mixed-task learner is rebuilt from scratch at five jointly scaled",
        "resource budgets and three deterministic evidence-order seeds. Public Phase",
        "13--16 benchmarks are not used for training, rule selection, or evaluation.",
        "",
        f"- campaign fingerprint: `{campaign['fingerprint']}`",
        f"- train / selection / blind examples: **{campaign['training_examples']} / {campaign['selection_examples']} / {campaign['blind_examples']}**",
        "",
        "| point | acquired cap | evidence cap | candidate cap/fit | inference cap | median accuracy | median coverage | median acquired bits | failures |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["summaries"]:
        budget = row["budget"]
        lines.append(
            f"| {budget['name']} | {budget['acquired_bits']} | {budget['evidence_bits']} | "
            f"{budget['candidate_cap_per_fit']} | {budget['inference_operations_per_item']} | "
            f"{100 * row['median_accuracy']:.1f}% | {100 * row['median_coverage']:.1f}% | "
            f"{row['median_acquired_bits']:.0f} | {row['training_failures']} |"
        )
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "This pilot validates the measurement and hard size/evidence/inference",
            "budget plumbing. It does not yet fit or extrapolate a scaling law because",
            "the induction cap is per fit, the suite is narrow, and the budget axes are",
            "coupled. A strict global induction interrupt and factorial budget grid are",
            "required before forecasting public or LLM-level performance.",
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
    (output / "phase17a.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase17a.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
