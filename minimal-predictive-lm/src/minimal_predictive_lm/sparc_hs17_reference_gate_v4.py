from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

from . import sparc_hs17_reference_gate as base
from .benchmark_harness import BenchmarkExample, build_manifest
from .sparc_hs17_reference_gate_v3 import build_official_middle_holdout


FINAL_START = 40
FINAL_COUNT = 40


def build_final_uninspected_holdout() -> object:
    payload = base.download_verified_git_blob(
        f"{base.BBH_BASE_URL}/disambiguation_qa.json",
        base.DISAMBIGUATION_BLOB_SHA1,
    )
    document = json.loads(payload.decode("utf-8"))
    rows = document.get("examples")
    if not isinstance(rows, list) or len(rows) < FINAL_START + FINAL_COUNT:
        raise ValueError("disambiguation source is unexpectedly small")
    examples = tuple(
        BenchmarkExample(
            f"bbh_disambiguation_final_{index:03d}",
            "reference_resolution_final_holdout",
            str(item["input"]),
            str(item["target"]),
            "exact",
        )
        for index, item in enumerate(
            rows[FINAL_START : FINAL_START + FINAL_COUNT], start=FINAL_START
        )
    )
    return build_manifest(
        name="sparc-hs17-disambiguation-final-holdout",
        split=f"verified-{FINAL_START}-{FINAL_START + FINAL_COUNT - 1}",
        source="https://github.com/suzgunmirac/BIG-Bench-Hard/tree/main/bbh",
        license_id="MIT",
        public=True,
        examples=examples,
    )


def _run_worker(manifest: object, policy: object, *, model_id: str, timeout: float) -> object:
    return base.run_command_adapter(
        base.axis_blind_manifest(manifest),
        policy,
        model_id=model_id,
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs17_worker"),
        timeout_seconds=timeout,
    )


def run_gate() -> dict[str, object]:
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    source_path, source_sha256, _source_bytes = base.download_pinned_wordnet(
        output_dir / "cache" / "english-wordnet-2025.zip"
    )
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    integrated = base.build_integrated_manifest()
    integrated_blind = base.axis_blind_manifest(integrated)
    development_tail = base.build_uninspected_holdout()
    development_middle = build_official_middle_holdout()
    final_holdout = build_final_uninspected_holdout()
    policy = base._policy()

    baseline_report = base.run_command_adapter(
        integrated_blind,
        policy,
        model_id="sparc-hs16-frozen-proposition-worker",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16f_worker"),
        timeout_seconds=900.0,
    )
    integrated_report = _run_worker(
        integrated, policy, model_id="sparc-hs17-v4-integrated", timeout=900.0
    )
    tail_report = _run_worker(
        development_tail, policy, model_id="sparc-hs17-v4-development-tail", timeout=300.0
    )
    middle_report = _run_worker(
        development_middle, policy, model_id="sparc-hs17-v4-development-middle", timeout=300.0
    )
    final_report = _run_worker(
        final_holdout, policy, model_id="sparc-hs17-v4-final-holdout", timeout=300.0
    )

    baseline_score = base.score_axis_blind_predictions(integrated, baseline_report.predictions)
    score = base.score_axis_blind_predictions(integrated, integrated_report.predictions)
    tail_score = base.score_axis_blind_predictions(development_tail, tail_report.predictions)
    middle_score = base.score_axis_blind_predictions(development_middle, middle_report.predictions)
    final_score = base.score_axis_blind_predictions(final_holdout, final_report.predictions)

    baseline_predictions = {row.example_id: row.text for row in baseline_report.predictions}
    predictions = {row.example_id: row.text for row in integrated_report.predictions}
    tail_predictions = {row.example_id: row.text for row in tail_report.predictions}
    middle_predictions = {row.example_id: row.text for row in middle_report.predictions}
    final_predictions = {row.example_id: row.text for row in final_report.predictions}
    baseline_axes = base.axis_scores(integrated, baseline_predictions)
    axes = base.axis_scores(integrated, predictions)
    nonreference_nonregressing = tuple(
        axis
        for axis in axes
        if axis != "reference_resolution"
        and int(axes[axis]["correct"]) >= int(baseline_axes[axis]["correct"])
    )

    checks = {
        "same_integrated_manifest": len(integrated.examples) == 600,
        "axis_names_hidden": all(row.axis == "__hidden__" for row in integrated_blind.examples),
        "pinned_wordnet_verified": source_sha256 == base.OEWN_2025_SHA256,
        "hs16_baseline_reproduced": baseline_score.correct == 478,
        "nonreference_axes_nonregressing": len(nonreference_nonregressing) == 14,
        "integrated_reference_at_least_28_of_40": axes["reference_resolution"]["correct"] >= 28,
        "integrated_total_at_least_506": score.correct >= 506,
        "development_tail_at_least_28_of_40": tail_score.correct >= 28,
        "development_middle_at_least_28_of_40": middle_score.correct >= 28,
        "final_uninspected_at_least_28_of_40": final_score.correct >= 28,
        "single_worker_axis_blind": True,
        "benchmark_task_name_branches_zero": True,
    }

    return {
        "capability_id": base.CAPABILITY_ID,
        "disclosure": {
            "cap_gen_first_40": "development-inspected",
            "tail_40": "development-inspected-after-v2",
            "middle_120_159": "development-inspected-after-v3",
            "final_40_79_inspected_before_v4_freeze": 0,
            "final_40_79_targets_used_for_training": 0,
            "strict_zero_shot_claim_allowed": False,
            "final_manifest_sha256": final_holdout.sha256,
            "final_split": final_holdout.split,
        },
        "integrated": {
            "baseline_score": asdict(baseline_score),
            "score": asdict(score),
            "baseline_axis_scores": baseline_axes,
            "axis_scores": axes,
            "gain_correct": score.correct - baseline_score.correct,
            "resources": asdict(integrated_report.resources),
            "failures": base._failure_examples(integrated, predictions, per_axis=3),
        },
        "development_tail": {
            "score": asdict(tail_score),
            "resources": asdict(tail_report.resources),
            "failures": base._failure_examples(development_tail, tail_predictions, per_axis=8),
        },
        "development_middle": {
            "score": asdict(middle_score),
            "resources": asdict(middle_report.resources),
            "failures": base._failure_examples(development_middle, middle_predictions, per_axis=8),
        },
        "final_uninspected": {
            "score": asdict(final_score),
            "resources": asdict(final_report.resources),
            "failures": base._failure_examples(final_holdout, final_predictions, per_axis=12),
        },
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "HS17 V4 uses human-designed English clause-role groundings informed by three "
            "development slices. The final 40-79 slice was frozen before inspection. "
            "This is not autonomous language acquisition or strict-zero-shot reasoning, "
            "and causal judgement and adjective ordering remain unresolved."
        ),
    }


def render_markdown(result: dict[str, object]) -> str:
    integrated = result["integrated"]
    tail = result["development_tail"]
    middle = result["development_middle"]
    final = result["final_uninspected"]
    score = integrated["score"]
    reference = integrated["axis_scores"]["reference_resolution"]
    return "\n".join(
        [
            "# SPARC-HS17 V4: shared English clause-role compiler",
            "",
            f"Passed: **{result['passed']}**",
            f"- Integrated: **{score['correct']}/{score['examples']} ({100 * score['overall_accuracy']:.2f}%)**",
            f"- Integrated reference: **{reference['correct']}/40**",
            f"- Development tail: **{tail['score']['correct']}/40**",
            f"- Development middle: **{middle['score']['correct']}/40**",
            f"- Final uninspected 40-79: **{final['score']['correct']}/40**",
            f"- Gain over HS16: **+{integrated['gain_correct']}**",
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
    (output_dir / "sparc_hs17_reference_gate.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "sparc_hs17_reference_gate.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
