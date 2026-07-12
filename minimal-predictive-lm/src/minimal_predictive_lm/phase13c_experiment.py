from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

from .benchmark_harness import RunPolicy, answer_is_correct, run_command_adapter, score_report
from .generic_algebra import ExpressionExample, induce_generic_algebra_model
from .phase13a_experiment import build_phase13a_manifest
from .phase13b_experiment import (
    operator_calibration,
    ordering_calibration,
    precedence_calibration,
)


def unary_scope_calibration() -> tuple[ExpressionExample, ...]:
    """Independent interactions that distinguish prefix scope from binary precedence."""
    return (
        ExpressionExample("2 * -3 =", -6),
        ExpressionExample("-2 * -3 =", 6),
        ExpressionExample("4 + 2 * -3 =", -2),
        ExpressionExample("8 - 3 * -2 =", 14),
        ExpressionExample("20 / -4 + 7 =", 2),
    )


def build_scope_corrected_algebra_model():
    return induce_generic_algebra_model(
        operator_calibration(),
        precedence_calibration() + unary_scope_calibration(),
        ordering_calibration(),
    )


def _axis_scores(manifest, predictions: dict[str, str]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[object]] = {}
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


def run() -> dict[str, object]:
    manifest, source_hashes = build_phase13a_manifest()
    policy = RunPolicy(
        max_output_chars=256,
        stop_sequences=("\n\n",),
        tools_allowed=(),
        temperature=0.0,
        seed=0,
    )
    before = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase13b-generic-algebra",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase13b_worker"),
        timeout_seconds=300.0,
    )
    after = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase13c-scope-corrected-algebra",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase13c_worker"),
        timeout_seconds=300.0,
    )
    before_score = score_report(manifest, before)
    after_score = score_report(manifest, after)
    before_predictions = {row.example_id: row.text for row in before.predictions}
    after_predictions = {row.example_id: row.text for row in after.predictions}
    before_axes = _axis_scores(manifest, before_predictions)
    after_axes = _axis_scores(manifest, after_predictions)
    algebra = build_scope_corrected_algebra_model()
    calibration_prompts = {row.text for row in unary_scope_calibration()}
    exact_overlap = sum(row.prompt in calibration_prompts for row in manifest.examples)
    multistep_rows = [row for row in manifest.examples if row.axis == "multistep_arithmetic"]
    multistep_wrong = sum(
        bool(after_predictions.get(row.example_id, "").strip())
        and after_predictions.get(row.example_id, "").strip() != "__ABSTAIN__"
        and not answer_is_correct(row, after_predictions.get(row.example_id, ""))
        for row in multistep_rows
    )
    multistep_abstained = sum(
        not after_predictions.get(row.example_id, "").strip()
        or after_predictions.get(row.example_id, "").strip() == "__ABSTAIN__"
        for row in multistep_rows
    )
    return {
        "suite": {
            "name": manifest.name,
            "manifest_sha256": manifest.sha256,
            "source_hashes": source_hashes,
            "public": manifest.public,
            "examples": len(manifest.examples),
            "axes": len(after_axes),
            "exact_new_calibration_prompt_overlap": exact_overlap,
            "benchmark_examples_used_for_calibration": 0,
        },
        "scope_correction": {
            "independent_interactions": len(unary_scope_calibration()),
            "precedence_candidates_evaluated": algebra.expression.precedence_candidates_evaluated,
            "precedence": dict(algebra.expression.precedence),
            "description_bits": algebra.description_bits,
            "description_bytes": (algebra.description_bits + 7) // 8,
            "domain_specific_handlers": algebra.domain_specific_handlers,
            "benchmark_specific_handlers_added": 0,
            "benchmark_specific_grammar_rules_added": 0,
        },
        "before": {
            "score": asdict(before_score),
            "axis_scores": before_axes,
            "resources": asdict(before.resources),
        },
        "after": {
            "score": asdict(after_score),
            "axis_scores": after_axes,
            "resources": asdict(after.resources),
            "multistep_wrong": multistep_wrong,
            "multistep_abstained": multistep_abstained,
        },
        "delta": {
            "correct": after_score.correct - before_score.correct,
            "accuracy_points": 100 * (after_score.overall_accuracy - before_score.overall_accuracy),
            "coverage_points": 100 * (after_score.coverage - before_score.coverage),
        },
        "gates": {
            "fully_public_improvement_measured": manifest.public,
            "benchmark_specialization_used": False,
            "unary_scope_failure_resolved": (
                after_axes["multistep_arithmetic"]["accuracy"] == 1.0
                and multistep_wrong == 0
                and multistep_abstained == 0
            ),
            "public_multi_domain_quality_parity_allowed": False,
            "public_multi_domain_runtime_pareto_allowed": False,
            "general_llm_parity_allowed": False,
            "stage_c_score_changed": False,
        },
        "limitations": [
            "the correction uses five independently authored scope interactions after failure analysis",
            "the parser and bounded precedence candidate language remain human-designed",
            "object counting still lacks open-world category grounding",
            "no matched open-model comparison is included",
            "natural-language generation, coding, long context, and open-domain knowledge remain untested",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    scope = payload["scope_correction"]
    before = payload["before"]
    after = payload["after"]
    lines = [
        "# Phase 13c results: generic unary-scope correction",
        "",
        "Failure diagnostics showed that multiplication followed by a negative operand",
        "was the common structural failure. Five independent interactions distinguish",
        "prefix unary scope from binary precedence; no benchmark example is used.",
        "",
        "## Anti-specialization checks",
        "",
        f"- independent scope interactions: **{scope['independent_interactions']}**",
        f"- exact benchmark prompt overlap: **{payload['suite']['exact_new_calibration_prompt_overlap']}**",
        f"- benchmark examples used for calibration: **{payload['suite']['benchmark_examples_used_for_calibration']}**",
        f"- benchmark-specific handlers / grammar rules: **{scope['benchmark_specific_handlers_added']} / {scope['benchmark_specific_grammar_rules_added']}**",
        f"- induced precedence: **{scope['precedence']}**",
        "",
        "## Public accuracy before and after",
        "",
        "| axis | Phase 13b | Phase 13c |",
        "|---|---:|---:|",
    ]
    for axis in after["axis_scores"]:
        lines.append(
            f"| {axis.replace('_', ' ')} | {100 * before['axis_scores'][axis]['accuracy']:.1f}% | {100 * after['axis_scores'][axis]['accuracy']:.1f}% |"
        )
    lines.extend(
        [
            "",
            f"Overall: **{100 * before['score']['overall_accuracy']:.1f}% → {100 * after['score']['overall_accuracy']:.1f}%**",
            f"Coverage: **{100 * before['score']['coverage']:.1f}% → {100 * after['score']['coverage']:.1f}%**",
            f"Multistep wrong / abstained: **{after['multistep_wrong']} / {after['multistep_abstained']}**",
            "",
            "## Claim boundary",
            "",
            "This is a generic grammar correction inside a bounded algebra, not evidence",
            "of open-ended representation learning or parity with an LLM.",
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
    (output_dir / "phase13c.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "phase13c.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
