from __future__ import annotations

from dataclasses import asdict
from fractions import Fraction
import json
from pathlib import Path
import sys

from .benchmark_harness import (
    BenchmarkExample,
    BenchmarkManifest,
    RunPolicy,
    answer_is_correct,
    run_command_adapter,
    score_report,
)
from .generic_algebra import (
    ExpressionExample,
    OperatorObservation,
    OrderingExample,
    induce_generic_algebra_model,
)
from .mixed_task_learner import induce_mixed_task_model
from .phase12a_experiment import calibration_interactions
from .phase13a_experiment import build_phase13a_manifest


def operator_calibration() -> tuple[OperatorObservation, ...]:
    return (
        OperatorObservation("+", (2, 3), 5),
        OperatorObservation("+", (11, -4), 7),
        OperatorObservation("-", (9, 4), 5),
        OperatorObservation("-", (-2, 7), -9),
        OperatorObservation("*", (6, 7), 42),
        OperatorObservation("*", (-3, 5), -15),
        OperatorObservation("/", (8, 2), 4),
        OperatorObservation("/", (3, 2), Fraction(3, 2)),
        OperatorObservation("neg", (3,), -3),
        OperatorObservation("neg", (-4,), 4),
        OperatorObservation("not", (True,), False),
        OperatorObservation("not", (False,), True),
        OperatorObservation("and", (False, False), False),
        OperatorObservation("and", (False, True), False),
        OperatorObservation("and", (True, False), False),
        OperatorObservation("and", (True, True), True),
        OperatorObservation("or", (False, False), False),
        OperatorObservation("or", (False, True), True),
        OperatorObservation("or", (True, False), True),
        OperatorObservation("or", (True, True), True),
    )


def precedence_calibration() -> tuple[ExpressionExample, ...]:
    return (
        ExpressionExample("1 + 2 * 3 =", 7),
        ExpressionExample("8 - 2 * 3 =", 2),
        ExpressionExample("20 / 5 + 1 =", 5),
        ExpressionExample("-2 * 3 + 10 =", 4),
        ExpressionExample("18 / 3 / 2 =", 3),
        ExpressionExample("True or False and False is", True),
        ExpressionExample("not True and False is", False),
        ExpressionExample("not ( True and False ) is", True),
    )


def ordering_calibration() -> tuple[OrderingExample, ...]:
    return (
        OrderingExample(
            "Sort these identifiers alphabetically: zeta alpha gamma",
            "alpha gamma zeta",
        ),
        OrderingExample(
            "Sort these repository paths alphabetically: src/z.py src/a.py docs/readme",
            "docs/readme src/a.py src/z.py",
        ),
        OrderingExample(
            "Arrange and sort these sensor labels alphabetically: sensor9 sensor2 sensor5",
            "sensor2 sensor5 sensor9",
        ),
        OrderingExample(
            "Sort these command names alphabetically: verify apply rollback",
            "apply rollback verify",
        ),
    )


def build_algebra_model():
    return induce_generic_algebra_model(
        operator_calibration(), precedence_calibration(), ordering_calibration()
    )


def cross_domain_examples() -> tuple[BenchmarkExample, ...]:
    return (
        BenchmarkExample("heldout_numeric_1", "numeric_expression", "( 4 + 3 ) * 2 =", "14", "numeric"),
        BenchmarkExample("heldout_numeric_2", "numeric_expression", "-5 + 2 * 4 =", "3", "numeric"),
        BenchmarkExample("heldout_logic_1", "logic_expression", "not False or False is", "true"),
        BenchmarkExample("heldout_logic_2", "logic_expression", "True and ( False or True ) is", "true"),
        BenchmarkExample(
            "heldout_order_1",
            "sequence_ordering",
            "Sort these API symbols alphabetically: render apply emit",
            "apply emit render",
        ),
        BenchmarkExample(
            "heldout_order_2",
            "sequence_ordering",
            "Sort these filesystem paths alphabetically: /z /a /m",
            "/a /m /z",
        ),
    )


def _axis_scores(
    manifest: BenchmarkManifest, predictions: dict[str, str]
) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[BenchmarkExample]] = {}
    for example in manifest.examples:
        grouped.setdefault(example.axis, []).append(example)
    output: dict[str, dict[str, object]] = {}
    for axis, rows in sorted(grouped.items()):
        answered = sum(
            bool(predictions.get(row.example_id, "").strip())
            and predictions.get(row.example_id, "").strip() != "__ABSTAIN__"
            for row in rows
        )
        correct = sum(
            answer_is_correct(row, predictions.get(row.example_id, "")) for row in rows
        )
        output[axis] = {
            "examples": len(rows),
            "answered": answered,
            "correct": correct,
            "accuracy": correct / len(rows),
            "coverage": answered / len(rows),
        }
    return output


def _cross_domain_score(model) -> dict[str, object]:
    rows = cross_domain_examples()
    correct = 0
    predictions: dict[str, str] = {}
    for row in rows:
        prediction = model.predict(row.prompt).output
        if isinstance(prediction, bool):
            text = "true" if prediction else "false"
        elif isinstance(prediction, Fraction):
            text = (
                str(prediction.numerator)
                if prediction.denominator == 1
                else f"{prediction.numerator}/{prediction.denominator}"
            )
        elif prediction is None:
            text = "__ABSTAIN__"
        else:
            text = str(prediction)
        predictions[row.example_id] = text
        correct += int(answer_is_correct(row, text))
    return {
        "examples": len(rows),
        "correct": correct,
        "accuracy": correct / len(rows),
        "predictions": predictions,
    }


def run() -> dict[str, object]:
    manifest, source_hashes = build_phase13a_manifest()
    policy = RunPolicy(
        max_output_chars=256,
        stop_sequences=("\n\n",),
        tools_allowed=(),
        temperature=0.0,
        seed=0,
    )
    baseline = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase12a-frozen-baseline",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase12a_worker"),
        timeout_seconds=300.0,
    )
    enhanced = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase13b-generic-algebra",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase13b_worker"),
        timeout_seconds=300.0,
    )
    baseline_score = score_report(manifest, baseline)
    enhanced_score = score_report(manifest, enhanced)
    baseline_predictions = {row.example_id: row.text for row in baseline.predictions}
    enhanced_predictions = {row.example_id: row.text for row in enhanced.predictions}
    baseline_axes = _axis_scores(manifest, baseline_predictions)
    enhanced_axes = _axis_scores(manifest, enhanced_predictions)

    phase12 = induce_mixed_task_model(calibration_interactions())
    algebra = build_algebra_model()
    calibration_prompts = {row.prompt for row in calibration_interactions()}
    calibration_prompts.update(row.text for row in precedence_calibration())
    calibration_prompts.update(row.prompt for row in ordering_calibration())
    exact_overlap = sum(row.prompt in calibration_prompts for row in manifest.examples)
    cross_domain = _cross_domain_score(algebra)

    return {
        "suite": {
            "name": manifest.name,
            "manifest_sha256": manifest.sha256,
            "source_hashes": source_hashes,
            "public": manifest.public,
            "examples": len(manifest.examples),
            "axes": len(enhanced_axes),
            "exact_calibration_prompt_overlap": exact_overlap,
            "benchmark_examples_used_for_calibration": 0,
        },
        "generic_algebra": {
            "operator_programs": len(algebra.expression.operators),
            "precedence_candidates_evaluated": algebra.expression.precedence_candidates_evaluated,
            "precedence": dict(algebra.expression.precedence),
            "ordering_mode": algebra.ordering.mode,
            "ordering_cues": algebra.ordering.cues,
            "description_bits": algebra.description_bits,
            "description_bytes": (algebra.description_bits + 7) // 8,
            "combined_description_bytes": (
                phase12.description_bits + algebra.description_bits + 7
            )
            // 8,
            "domain_specific_handlers": algebra.domain_specific_handlers,
            "benchmark_specific_handlers_added": 0,
            "benchmark_specific_item_lexicon_entries": 0,
            "cross_domain_heldout": cross_domain,
        },
        "baseline": {
            "score": asdict(baseline_score),
            "axis_scores": baseline_axes,
            "resources": asdict(baseline.resources),
        },
        "enhanced": {
            "score": asdict(enhanced_score),
            "axis_scores": enhanced_axes,
            "resources": asdict(enhanced.resources),
        },
        "delta": {
            "correct": enhanced_score.correct - baseline_score.correct,
            "accuracy_points": 100
            * (enhanced_score.overall_accuracy - baseline_score.overall_accuracy),
            "coverage_points": 100 * (enhanced_score.coverage - baseline_score.coverage),
        },
        "gates": {
            "fully_public_improvement_measured": manifest.public,
            "same_generic_algebra_for_numeric_boolean_and_ordering": True,
            "benchmark_specialization_used": False,
            "cross_domain_transfer_passed": cross_domain["accuracy"] == 1.0,
            "public_multi_domain_quality_parity_allowed": False,
            "public_multi_domain_runtime_pareto_allowed": False,
            "general_llm_parity_allowed": False,
            "stage_c_score_changed": False,
        },
        "limitations": [
            "the expression tokenizer and shunting-yard execution algorithm are human-designed generic meta-structure",
            "operator semantics and precedence are induced only inside a bounded candidate language",
            "ordering supports four predefined comparator families",
            "object counting still lacks open-world entity-category grounding",
            "calibration interactions were created after observing the Phase 13a capability classes, although no benchmark examples or item lexicon were used",
            "no matched open-model run is included in Phase 13b",
            "natural-language generation, coding, long context, and open-domain knowledge remain untested",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    suite = payload["suite"]
    algebra = payload["generic_algebra"]
    baseline = payload["baseline"]
    enhanced = payload["enhanced"]
    lines = [
        "# Phase 13b results: induced generic expression and sequence algebra",
        "",
        "One bounded algebra is induced from independent operator, precedence, and ordering",
        "interactions. The public benchmark supplies no calibration examples, task names,",
        "or item lexicon to the model.",
        "",
        "## Anti-specialization checks",
        "",
        f"- fully public examples / axes: **{suite['examples']} / {suite['axes']}**",
        f"- exact calibration prompt overlap: **{suite['exact_calibration_prompt_overlap']}**",
        f"- benchmark examples used for calibration: **{suite['benchmark_examples_used_for_calibration']}**",
        f"- benchmark-specific handlers / item lexicon entries: **{algebra['benchmark_specific_handlers_added']} / {algebra['benchmark_specific_item_lexicon_entries']}**",
        f"- generic operator programs: **{algebra['operator_programs']}**",
        f"- algebra payload / combined payload: **{algebra['description_bytes']:,} / {algebra['combined_description_bytes']:,} bytes**",
        f"- cross-domain held-out transfer: **{100 * algebra['cross_domain_heldout']['accuracy']:.1f}%**",
        "",
        "## Public accuracy before and after",
        "",
        "| axis | frozen Phase 12 | Phase 13b algebra |",
        "|---|---:|---:|",
    ]
    for axis in enhanced["axis_scores"]:
        before = baseline["axis_scores"][axis]["accuracy"]
        after = enhanced["axis_scores"][axis]["accuracy"]
        lines.append(f"| {axis.replace('_', ' ')} | {100 * before:.1f}% | {100 * after:.1f}% |")
    lines.extend(
        [
            "",
            f"Overall: **{100 * baseline['score']['overall_accuracy']:.1f}% → {100 * enhanced['score']['overall_accuracy']:.1f}%**",
            f"Coverage: **{100 * baseline['score']['coverage']:.1f}% → {100 * enhanced['score']['coverage']:.1f}%**",
            "",
            "## Claim boundary",
            "",
            "This phase measures public transfer of a shared bounded algebra. It does not",
            "authorize parity with an open model or a general LLM. The generic tokenizer,",
            "parser, and comparator candidate families remain human-designed, and object",
            "counting still requires open-world category grounding.",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "phase13b.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "phase13b.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
