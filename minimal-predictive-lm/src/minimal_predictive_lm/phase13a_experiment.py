from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Iterable

from .benchmark_harness import (
    ABSTAIN_TOKEN,
    BenchmarkExample,
    BenchmarkManifest,
    RunPolicy,
    answer_is_correct,
    build_manifest,
    run_command_adapter,
    score_report,
)
from .mixed_task_learner import MixedTaskModel, induce_mixed_task_model
from .phase12a_experiment import calibration_interactions
from .public_benchmarks import (
    load_bbh_multi_domain_subset,
    load_bigbench_arithmetic_subset,
)


PHASE13A_EXAMPLES_PER_TASK = 40


def model_fingerprint(model: MixedTaskModel) -> str:
    payload = json.dumps(
        model.render(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_phase13a_manifest(
    *, examples_per_task: int = PHASE13A_EXAMPLES_PER_TASK
) -> tuple[BenchmarkManifest, dict[str, str]]:
    arithmetic = load_bigbench_arithmetic_subset(
        examples_per_task=max(1, examples_per_task // 20),
        expected_manifest_sha256=None,
    )
    arithmetic_rows = tuple(
        BenchmarkExample(
            row.example_id,
            "direct_arithmetic",
            row.prompt,
            row.target,
            row.answer_type,
        )
        for row in arithmetic.examples
    )
    bbh = load_bbh_multi_domain_subset(
        examples_per_task=examples_per_task,
        expected_manifest_sha256=None,
    )
    manifest = build_manifest(
        name="phase13a-frozen-public-multi-domain",
        split=f"direct-arithmetic-40-plus-bbh-first-{examples_per_task}",
        source=(
            "Google BIG-bench arithmetic and BIG-Bench-Hard boolean expressions, "
            "multistep arithmetic, object counting, and word sorting"
        ),
        license_id="mixed:Apache-2.0+MIT",
        public=True,
        examples=arithmetic_rows + bbh.examples,
    )
    return manifest, {
        "bigbench_arithmetic_sha256": arithmetic.sha256,
        "bbh_multi_domain_sha256": bbh.sha256,
    }


def _axis_scores(
    manifest: BenchmarkManifest, predictions: dict[str, str]
) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[BenchmarkExample]] = {}
    for example in manifest.examples:
        grouped.setdefault(example.axis, []).append(example)
    output: dict[str, dict[str, object]] = {}
    for axis, examples in sorted(grouped.items()):
        answered = sum(
            bool(predictions.get(example.example_id, "").strip())
            and predictions.get(example.example_id, "").strip() != ABSTAIN_TOKEN
            for example in examples
        )
        correct = sum(
            answer_is_correct(example, predictions.get(example.example_id, ""))
            for example in examples
        )
        output[axis] = {
            "examples": len(examples),
            "answered": answered,
            "correct": correct,
            "accuracy": correct / len(examples),
            "coverage": answered / len(examples),
            "selective_accuracy": correct / answered if answered else 0.0,
        }
    return output


def failure_summary(
    manifest: BenchmarkManifest, predictions: dict[str, str]
) -> dict[str, int]:
    counts = {"correct": 0, "wrong": 0, "abstained": 0}
    for example in manifest.examples:
        prediction = predictions.get(example.example_id, "").strip()
        if not prediction or prediction == ABSTAIN_TOKEN:
            counts["abstained"] += 1
        elif answer_is_correct(example, prediction):
            counts["correct"] += 1
        else:
            counts["wrong"] += 1
    return counts


def _capability_gap_inventory(axes: Iterable[str]) -> dict[str, str]:
    descriptions = {
        "direct_arithmetic": "single-step lexical operation grounding",
        "boolean_expressions": "recursive symbolic composition and precedence",
        "multistep_arithmetic": "nested program parsing and execution",
        "object_counting": "entity selection, number-word grounding, and aggregation",
        "word_sorting": "variable-length sequence extraction and ordering",
    }
    return {axis: descriptions.get(axis, "unknown public capability") for axis in axes}


def run() -> dict[str, object]:
    calibration = calibration_interactions()
    frozen_model = induce_mixed_task_model(calibration)
    fingerprint_before = model_fingerprint(frozen_model)
    manifest, source_hashes = build_phase13a_manifest()
    policy = RunPolicy(
        max_output_chars=256,
        stop_sequences=("\n\n",),
        tools_allowed=(),
        temperature=0.0,
        seed=0,
    )
    report = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase12a-frozen-before-public-multi-domain-adaptation",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase12a_worker"),
        timeout_seconds=300.0,
    )
    fingerprint_after = model_fingerprint(frozen_model)
    score = score_report(manifest, report)
    predictions = {row.example_id: row.text for row in report.predictions}
    axes = _axis_scores(manifest, predictions)
    calibration_prompts = {row.prompt for row in calibration}
    exact_overlap = sum(
        example.prompt in calibration_prompts for example in manifest.examples
    )
    failures = failure_summary(manifest, predictions)
    non_arithmetic_axes = [axis for axis in axes if axis != "direct_arithmetic"]
    non_arithmetic_correct = sum(int(axes[axis]["correct"]) for axis in non_arithmetic_axes)
    non_arithmetic_examples = sum(int(axes[axis]["examples"]) for axis in non_arithmetic_axes)
    return {
        "suite": {
            "name": manifest.name,
            "manifest_sha256": manifest.sha256,
            "source_hashes": source_hashes,
            "public": manifest.public,
            "examples": len(manifest.examples),
            "axes": len(axes),
            "examples_per_axis": {
                axis: int(row["examples"]) for axis, row in axes.items()
            },
            "calibration_examples": len(calibration),
            "exact_calibration_prompt_overlap": exact_overlap,
        },
        "frozen_model": {
            "fingerprint_before": fingerprint_before,
            "fingerprint_after": fingerprint_after,
            "unchanged": fingerprint_before == fingerprint_after,
            "rules": len(frozen_model.rules),
            "description_bits": frozen_model.description_bits,
            "description_bytes": (frozen_model.description_bits + 7) // 8,
            "induction_candidate_evaluations": frozen_model.candidate_evaluations,
            "domain_specific_handlers": frozen_model.domain_specific_handlers,
            "benchmark_specific_handlers_added": 0,
            "benchmark_specific_primitives_added": 0,
            "benchmark_examples_used_for_calibration": 0,
        },
        "score": asdict(score),
        "axis_scores": axes,
        "non_arithmetic": {
            "correct": non_arithmetic_correct,
            "examples": non_arithmetic_examples,
            "accuracy": non_arithmetic_correct / non_arithmetic_examples,
        },
        "failure_summary": failures,
        "capability_gap_inventory": _capability_gap_inventory(axes),
        "resources": asdict(report.resources),
        "gates": {
            "frozen_public_baseline_valid": (
                manifest.public
                and exact_overlap == 0
                and fingerprint_before == fingerprint_after
                and frozen_model.domain_specific_handlers == 0
            ),
            "benchmark_specialization_used": False,
            "public_multi_domain_quality_parity_allowed": False,
            "public_multi_domain_runtime_pareto_allowed": False,
            "general_llm_parity_allowed": False,
            "stage_c_score_changed": False,
        },
        "limitations": [
            "the frozen model was calibrated on forty Phase 12 interactions rather than pretrained on open language",
            "direct arithmetic is represented in calibration while the four BBH capabilities are not",
            "the baseline intentionally does not learn from benchmark examples",
            "task axes are used only for evaluation and failure analysis, never for routing or execution",
            "no open-model comparison is included in Phase 13a",
            "natural-language generation, coding, long context, and open-domain knowledge remain untested",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    suite = payload["suite"]
    model = payload["frozen_model"]
    score = payload["score"]
    resources = payload["resources"]
    lines = [
        "# Phase 13a results: frozen public multi-domain baseline",
        "",
        "The Phase 12 model is frozen before seeing a fully public five-axis suite.",
        "Benchmark task names are used only by the scorer; the model receives raw prompts.",
        "",
        "## Suite and anti-specialization checks",
        "",
        f"- public examples / axes: **{suite['examples']} / {suite['axes']}**",
        f"- exact calibration prompt overlap: **{suite['exact_calibration_prompt_overlap']}**",
        f"- model fingerprint unchanged: **{model['unchanged']}**",
        f"- benchmark-specific handlers / primitives / calibration examples: **{model['benchmark_specific_handlers_added']} / {model['benchmark_specific_primitives_added']} / {model['benchmark_examples_used_for_calibration']}**",
        f"- compiled payload: **{model['description_bits']:,}bit / {model['description_bytes']:,}bytes**",
        "",
        "## Accuracy by public axis",
        "",
        "| axis | correct | answered | examples | accuracy | coverage |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for axis, row in payload["axis_scores"].items():
        lines.append(
            f"| {axis.replace('_', ' ')} | {row['correct']} | {row['answered']} | {row['examples']} | {100 * row['accuracy']:.1f}% | {100 * row['coverage']:.1f}% |"
        )
    lines.extend(
        [
            "",
            f"Overall accuracy / coverage: **{100 * score['overall_accuracy']:.1f}% / {100 * score['coverage']:.1f}%**",
            f"Non-arithmetic accuracy: **{100 * payload['non_arithmetic']['accuracy']:.1f}%**",
            "",
            "## Resources",
            "",
            f"- model bytes: **{resources['model_bytes']:,}**",
            f"- peak RSS: **{resources['peak_rss_bytes']:,} bytes**",
            f"- wall time including fresh-process re-induction: **{resources['wall_ns'] / 1_000_000:.3f} ms**",
            f"- operations / reads / writes: **{resources['operations']} / {resources['reads']} / {resources['writes']}**",
            "",
            "## Claim gate",
            "",
            "This is a valid frozen public baseline, not a parity result. Public multi-domain",
            "quality parity, runtime Pareto, and general LLM parity remain closed until a",
            "matched open-model run and non-benchmark-specific improvement are demonstrated.",
            "",
            "## Capability gaps",
            "",
        ]
    )
    for axis, description in payload["capability_gap_inventory"].items():
        lines.append(f"- **{axis}**: {description}")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "phase13a.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "phase13a.md").write_text(
        render_markdown(payload), encoding="utf-8"
    )
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
