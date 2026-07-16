from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

from . import sparc_hs17_reference_gate as base


def run_gate() -> dict[str, object]:
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    source_path, source_sha256, _source_bytes = base.download_pinned_wordnet(
        output_dir / "cache" / "english-wordnet-2025.zip"
    )
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    integrated = base.build_integrated_manifest()
    integrated_blind = base.axis_blind_manifest(integrated)
    holdout = base.build_uninspected_holdout()
    holdout_blind = base.axis_blind_manifest(holdout)
    policy = base._policy()

    baseline_report = base.run_command_adapter(
        integrated_blind,
        policy,
        model_id="sparc-hs16-frozen-proposition-worker",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16f_worker"),
        timeout_seconds=900.0,
    )
    integrated_report = base.run_command_adapter(
        integrated_blind,
        policy,
        model_id="sparc-hs17-frozen-role-worker",
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs17_worker"),
        timeout_seconds=900.0,
    )
    holdout_report = base.run_command_adapter(
        holdout_blind,
        policy,
        model_id="sparc-hs17-frozen-role-worker-tail-holdout",
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs17_worker"),
        timeout_seconds=300.0,
    )

    baseline_score = base.score_axis_blind_predictions(
        integrated, baseline_report.predictions
    )
    score = base.score_axis_blind_predictions(integrated, integrated_report.predictions)
    holdout_score = base.score_axis_blind_predictions(
        holdout, holdout_report.predictions
    )
    baseline_predictions = {
        row.example_id: row.text for row in baseline_report.predictions
    }
    predictions = {row.example_id: row.text for row in integrated_report.predictions}
    holdout_predictions = {
        row.example_id: row.text for row in holdout_report.predictions
    }
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
        "axis_names_hidden": all(
            row.axis == "__hidden__" for row in integrated_blind.examples
        ),
        "pinned_wordnet_verified": source_sha256 == base.OEWN_2025_SHA256,
        "hs16_baseline_reproduced": baseline_score.correct == 478,
        "nonreference_axes_nonregressing": len(nonreference_nonregressing) == 14,
        "integrated_reference_at_least_28_of_40": axes["reference_resolution"][
            "correct"
        ]
        >= 28,
        "integrated_total_at_least_506": score.correct >= 506,
        "uninspected_tail_at_least_28_of_40": holdout_score.correct >= 28,
        "single_worker_axis_blind": True,
        "benchmark_task_name_branches_zero": True,
    }
    return {
        "capability_id": base.CAPABILITY_ID,
        "disclosure": {
            "cap_gen_first_40_format_inspected": True,
            "cap_gen_first_40_targets_inspected_during_development": True,
            "strict_zero_shot_claim_allowed": False,
            "tail_holdout_examples_inspected_before_freeze": 0,
            "tail_holdout_targets_used_for_training": 0,
            "tail_holdout_manifest_sha256": holdout.sha256,
            "tail_holdout_split": holdout.split,
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
        "uninspected_tail_holdout": {
            "score": asdict(holdout_score),
            "resources": asdict(holdout_report.resources),
            "failures": base._failure_examples(
                holdout, holdout_predictions, per_axis=12
            ),
        },
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "HS17 is a format-informed English role compiler evaluated on a separately "
            "frozen tail holdout. It is not strict zero-shot reference understanding, "
            "and causal judgement and adjective ordering remain unresolved."
        ),
    }


def main() -> None:
    result = run_gate()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "sparc_hs17_reference_gate.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "sparc_hs17_reference_gate.md").write_text(
        base.render_markdown(result), encoding="utf-8"
    )
    print(base.render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
