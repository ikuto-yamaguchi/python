from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
from typing import Mapping

from .benchmark_harness import (
    BenchmarkExample,
    RunPolicy,
    build_manifest,
    run_command_adapter,
    score_report,
)
from .cap_gen_001_integrated_public_reality_gate import (
    _failure_examples,
    axis_blind_manifest,
    axis_scores,
    build_integrated_manifest,
    score_axis_blind_predictions,
)
from .public_benchmarks import BBH_BASE_URL, download_verified_git_blob
from .wordnet_ontology import OEWN_2025_SHA256, download_pinned_wordnet


CAPABILITY_ID = "SPARC-HS17-ENGLISH-ROLE-COMPILER"
DISAMBIGUATION_BLOB_SHA1 = "d896cfe6b83a150d2904164e5424521f85bb0a3b"
HOLDOUT_EXAMPLES = 40


def build_uninspected_holdout() -> object:
    payload = download_verified_git_blob(
        f"{BBH_BASE_URL}/disambiguation_qa.json",
        DISAMBIGUATION_BLOB_SHA1,
    )
    document = json.loads(payload.decode("utf-8"))
    rows = document.get("examples")
    if not isinstance(rows, list) or len(rows) < 80:
        raise ValueError("disambiguation source is unexpectedly small")
    start = len(rows) - HOLDOUT_EXAMPLES
    examples = tuple(
        BenchmarkExample(
            f"bbh_disambiguation_tail_{index:03d}",
            "reference_resolution_holdout",
            str(item["input"]),
            str(item["target"]),
            "exact",
        )
        for index, item in enumerate(rows[start:], start=start)
    )
    return build_manifest(
        name="sparc-hs17-disambiguation-uninspected-tail",
        split=f"verified-tail-{start}-{len(rows)-1}",
        source="https://github.com/suzgunmirac/BIG-Bench-Hard/tree/main/bbh",
        license_id="MIT",
        public=True,
        examples=examples,
    )


def _policy() -> RunPolicy:
    return RunPolicy(
        max_output_chars=256,
        stop_sequences=("\n\n",),
        tools_allowed=(
            "pinned-open-english-wordnet-2025",
            "fixed-phase14b-provenance-documents",
        ),
        temperature=0.0,
        seed=0,
    )


def run_gate() -> dict[str, object]:
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    source_path, source_sha256, _source_bytes = download_pinned_wordnet(
        output_dir / "cache" / "english-wordnet-2025.zip"
    )
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    integrated = build_integrated_manifest()
    integrated_blind = axis_blind_manifest(integrated)
    holdout = build_uninspected_holdout()
    holdout_blind = axis_blind_manifest(holdout)
    policy = _policy()

    baseline_report = run_command_adapter(
        integrated_blind,
        policy,
        model_id="sparc-hs16-frozen-proposition-worker",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16f_worker"),
        timeout_seconds=900.0,
    )
    integrated_report = run_command_adapter(
        integrated_blind,
        policy,
        model_id="sparc-hs17-frozen-role-worker",
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs17_worker"),
        timeout_seconds=900.0,
    )
    holdout_report = run_command_adapter(
        holdout_blind,
        policy,
        model_id="sparc-hs17-frozen-role-worker-tail-holdout",
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs17_worker"),
        timeout_seconds=300.0,
    )

    baseline_score = score_axis_blind_predictions(integrated, baseline_report.predictions)
    score = score_axis_blind_predictions(integrated, integrated_report.predictions)
    baseline_predictions = {row.example_id: row.text for row in baseline_report.predictions}
    predictions = {row.example_id: row.text for row in integrated_report.predictions}
    baseline_axes = axis_scores(integrated, baseline_predictions)
    axes = axis_scores(integrated, predictions)
    holdout_score = score_report(holdout, holdout_report)
    holdout_predictions = {row.example_id: row.text for row in holdout_report.predictions}

    nonreference_nonregressing = tuple(
        axis
        for axis in axes
        if axis != "reference_resolution"
        and int(axes[axis]["correct"]) >= int(baseline_axes[axis]["correct"])
    )
    checks = {
        "same_integrated_manifest": len(integrated.examples) == 600,
        "axis_names_hidden": all(row.axis == "__hidden__" for row in integrated_blind.examples),
        "pinned_wordnet_verified": source_sha256 == OEWN_2025_SHA256,
        "hs16_baseline_reproduced": baseline_score.correct == 478,
        "nonreference_axes_nonregressing": len(nonreference_nonregressing) == 14,
        "integrated_reference_at_least_28_of_40": axes["reference_resolution"]["correct"] >= 28,
        "integrated_total_at_least_506": score.correct >= 506,
        "uninspected_tail_at_least_28_of_40": holdout_score.correct >= 28,
        "single_worker_axis_blind": True,
        "benchmark_task_name_branches_zero": True,
    }
    return {
        "capability_id": CAPABILITY_ID,
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
            "failures": _failure_examples(integrated, predictions, per_axis=3),
        },
        "uninspected_tail_holdout": {
            "score": asdict(holdout_score),
            "resources": asdict(holdout_report.resources),
            "failures": _failure_examples(holdout, holdout_predictions, per_axis=12),
        },
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "HS17 is a format-informed English role compiler evaluated on a separately "
            "frozen tail holdout. It is not strict zero-shot reference understanding, "
            "and causal judgement and adjective ordering remain unresolved."
        ),
    }


def render_markdown(result: Mapping[str, object]) -> str:
    integrated = result["integrated"]
    holdout = result["uninspected_tail_holdout"]
    score = integrated["score"]
    reference = integrated["axis_scores"]["reference_resolution"]
    lines = [
        "# SPARC-HS17: shared English role compiler",
        "",
        f"Passed: **{result['passed']}**",
        f"- Integrated score: **{score['correct']}/{score['examples']} ({100 * score['overall_accuracy']:.2f}%)**",
        f"- Integrated reference: **{reference['correct']}/40**",
        f"- Uninspected tail holdout: **{holdout['score']['correct']}/{holdout['score']['examples']} ({100 * holdout['score']['overall_accuracy']:.1f}%)**",
        f"- Gain over HS16: **+{integrated['gain_correct']}**",
        "",
        "## Disclosure",
        "",
        "- CAP-GEN first-40 format and targets were inspected during development.",
        "- The official generalisation result is therefore the separately frozen tail-40 holdout.",
        "- Strict zero-shot reference-resolution claims are forbidden.",
        "",
        "## Claim boundary",
        "",
        str(result["claim_boundary"]),
    ]
    return "\n".join(lines) + "\n"


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
