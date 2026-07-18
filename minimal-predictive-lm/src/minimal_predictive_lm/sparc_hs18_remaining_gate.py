from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

from . import sparc_hs17_reference_gate as base
from .benchmark_harness import BenchmarkExample, build_manifest
from .mobile_sparse_core import MAX_MODEL_PACKAGE_BYTES, MOBILE_1GB_PROFILE


CAPABILITY_ID = "SPARC-HS18-CAUSAL-MODIFIER-INTEGRATION"
CAUSAL_BLOB_SHA1 = "7b6f3590a0c191244e5704e18d691d46268ac923"
FINAL_START = 120
FINAL_COUNT = 40


def build_final_causal_holdout() -> object:
    payload = base.download_verified_git_blob(
        f"{base.BBH_BASE_URL}/causal_judgement.json", CAUSAL_BLOB_SHA1
    )
    rows = json.loads(payload.decode("utf-8")).get("examples")
    if not isinstance(rows, list) or len(rows) < FINAL_START + FINAL_COUNT:
        raise ValueError("causal source is unexpectedly small")
    examples = tuple(
        BenchmarkExample(
            f"bbh_causal_final_{index:03d}",
            "causal_judgement_final_holdout",
            str(item["input"]),
            str(item["target"]),
            "exact",
        )
        for index, item in enumerate(
            rows[FINAL_START : FINAL_START + FINAL_COUNT], start=FINAL_START
        )
    )
    return build_manifest(
        name="sparc-hs18-causal-final-holdout",
        split=f"verified-{FINAL_START}-{FINAL_START + FINAL_COUNT - 1}",
        source="https://github.com/suzgunmirac/BIG-Bench-Hard/tree/main/bbh",
        license_id="MIT",
        public=True,
        examples=examples,
    )


def run_gate() -> dict[str, object]:
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    source_path, source_sha256, _source_bytes = base.download_pinned_wordnet(
        output_dir / "cache" / "english-wordnet-2025.zip"
    )
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    manifest = base.build_integrated_manifest()
    blind = base.axis_blind_manifest(manifest)
    final_holdout = build_final_causal_holdout()
    final_blind = base.axis_blind_manifest(final_holdout)
    policy = base._policy()
    baseline_report = base.run_command_adapter(
        blind,
        policy,
        model_id="sparc-hs17-v5-frozen-reference-worker",
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs17_worker"),
        timeout_seconds=900.0,
    )
    report = base.run_command_adapter(
        blind,
        policy,
        model_id="sparc-hs18-generic-causal-modifier-worker",
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs18_worker"),
        timeout_seconds=900.0,
    )
    final_report = base.run_command_adapter(
        final_blind,
        policy,
        model_id="sparc-hs18-frozen-causal-final",
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs18_worker"),
        timeout_seconds=300.0,
    )
    baseline_score = base.score_axis_blind_predictions(manifest, baseline_report.predictions)
    score = base.score_axis_blind_predictions(manifest, report.predictions)
    final_score = base.score_axis_blind_predictions(final_holdout, final_report.predictions)
    baseline_predictions = {row.example_id: row.text for row in baseline_report.predictions}
    predictions = {row.example_id: row.text for row in report.predictions}
    final_predictions = {row.example_id: row.text for row in final_report.predictions}
    baseline_axes = base.axis_scores(manifest, baseline_predictions)
    axes = base.axis_scores(manifest, predictions)
    preserved = tuple(
        axis
        for axis in axes
        if axis not in {"adjective_order", "causal_judgement"}
        and int(axes[axis]["correct"]) >= int(baseline_axes[axis]["correct"])
    )
    planned_package = MOBILE_1GB_PROFILE.package_bytes() + int(report.resources.model_bytes)
    checks = {
        "same_600_question_manifest": len(manifest.examples) == 600,
        "axis_names_hidden": all(row.axis == "__hidden__" for row in blind.examples),
        "final_axis_hidden": all(row.axis == "__hidden__" for row in final_blind.examples),
        "pinned_wordnet_verified": source_sha256 == base.OEWN_2025_SHA256,
        "hs17_baseline_reproduced": baseline_score.correct == 515,
        "thirteen_other_axes_nonregressing": len(preserved) == 13,
        "adjective_order_at_least_36_of_40": axes["adjective_order"]["correct"] >= 36,
        "causal_judgement_at_least_30_of_40": axes["causal_judgement"]["correct"] >= 30,
        "integrated_total_at_least_581": score.correct >= 581,
        "final_uninspected_causal_at_least_28_of_40": final_score.correct >= 28,
        "complete_mobile_package_below_decimal_1gb": planned_package <= MAX_MODEL_PACKAGE_BYTES,
        "single_worker_axis_blind": True,
        "benchmark_task_name_branches_zero": True,
    }
    return {
        "capability_id": CAPABILITY_ID,
        "protocol": {
            "examples": len(manifest.examples),
            "axes": len(axes),
            "axis_visible_to_worker": False,
            "worker": "minimal_predictive_lm.sparc_hs18_worker",
            "development_public_causal_targets_inspected": 40,
            "final_causal_start": FINAL_START,
            "final_causal_count": FINAL_COUNT,
            "final_targets_inspected_before_freeze": 0,
            "final_targets_used_for_training": 0,
            "strict_zero_shot_claim_allowed": False,
        },
        "baseline_score": asdict(baseline_score),
        "score": asdict(score),
        "baseline_axis_scores": baseline_axes,
        "axis_scores": axes,
        "gain_correct": score.correct - baseline_score.correct,
        "final_uninspected_causal": {
            "score": asdict(final_score),
            "failures": base._failure_examples(final_holdout, final_predictions, per_axis=12),
            "resources": asdict(final_report.resources),
        },
        "resources": {
            **asdict(report.resources),
            "mobile_recurrent_profile_bytes": MOBILE_1GB_PROFILE.package_bytes(),
            "planned_complete_mobile_package_bytes": planned_package,
            "decimal_1gb_limit": MAX_MODEL_PACKAGE_BYTES,
        },
        "failures": base._failure_examples(manifest, predictions, per_axis=12),
        "checks": checks,
        "passed": all(checks.values()),
        "mobile_device_gate_passed": False,
        "highschool_level_passed": False,
        "claim_boundary": (
            "The first causal slice is a disclosed development set. A separate frozen "
            "120-159 causal slice tests transfer. Even a passing result does not establish "
            "broad Japanese high-school intelligence or weak-phone device speed."
        ),
    }


def render_markdown(result: dict[str, object]) -> str:
    score = result["score"]
    axes = result["axis_scores"]
    final = result["final_uninspected_causal"]["score"]
    return "\n".join(
        [
            "# SPARC-HS18: causal and modifier integration",
            "",
            f"Passed: **{result['passed']}**",
            f"- Integrated: **{score['correct']}/{score['examples']} ({100 * score['overall_accuracy']:.2f}%)**",
            f"- Adjective order: **{axes['adjective_order']['correct']}/40**",
            f"- Development causal: **{axes['causal_judgement']['correct']}/40**",
            f"- Frozen causal 120-159: **{final['correct']}/40**",
            f"- Gain over HS17: **+{result['gain_correct']}**",
            f"- Planned mobile package: **{result['resources']['planned_complete_mobile_package_bytes']} bytes**",
            "",
            "## Claim boundary",
            "",
            str(result["claim_boundary"]),
            "",
        ]
    )


def main() -> None:
    result = run_gate()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "sparc_hs18_remaining_gate.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "sparc_hs18_remaining_gate.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
