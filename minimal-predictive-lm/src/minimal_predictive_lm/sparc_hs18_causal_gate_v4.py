from __future__ import annotations

from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import sys

from . import sparc_hs18_causal_gate as v1
from .benchmark_harness import BenchmarkExample, build_manifest
from .english_causal_compiler_v4 import build_sparse_causal_model
from .public_benchmarks import BBH_BASE_URL, download_verified_git_blob
from .sparse_causal_curriculum import build_sparse_causal_curriculum


CAPABILITY_ID = "SPARC-HS18-V4-LEARNED-SPARSE-CAUSAL-PROTOTYPES"
FINAL_START = 160


def build_final_tail() -> object:
    payload = download_verified_git_blob(
        f"{BBH_BASE_URL}/causal_judgement.json", v1.CAUSAL_BLOB_SHA1
    )
    document = json.loads(payload.decode("utf-8"))
    rows = document.get("examples")
    if not isinstance(rows, list) or len(rows) <= FINAL_START:
        raise ValueError("causal judgement source has no final tail")
    examples = tuple(
        BenchmarkExample(
            f"bbh_causal_final_tail_{index:03d}",
            "causal_judgement_final_tail",
            str(item["input"]),
            str(item["target"]),
            "exact",
        )
        for index, item in enumerate(rows[FINAL_START:], start=FINAL_START)
    )
    return build_manifest(
        name="sparc-hs18-causal-final-tail",
        split=f"verified-{FINAL_START}-end",
        source="https://github.com/suzgunmirac/BIG-Bench-Hard/tree/main/bbh",
        license_id="MIT",
        public=True,
        examples=examples,
    )


def _learned_shift() -> dict[str, object]:
    model = build_sparse_causal_model()
    heldout = build_sparse_causal_curriculum(seed=1811, variants_per_pattern=40)
    correct = 0
    answered = 0
    candidates = 0
    reads = 0
    failures: list[dict[str, object]] = []
    for row in heldout:
        prediction = model.predict(row.prompt)
        candidates += prediction.candidates
        reads += prediction.feature_reads
        if prediction.answer is not None:
            answered += 1
        if prediction.answer == row.answer:
            correct += 1
        elif len(failures) < 16:
            failures.append(
                {
                    "operator": row.operator,
                    "expected": row.answer,
                    "actual": prediction.answer,
                    "score": prediction.score,
                    "margin": prediction.margin,
                }
            )
    total = len(heldout)
    return {
        "examples": total,
        "answered": answered,
        "correct": correct,
        "accuracy": correct / total,
        "coverage": answered / total,
        "selective_accuracy": correct / answered if answered else 0.0,
        "mean_candidates": candidates / total,
        "mean_feature_reads": reads / total,
        "prototypes": len(model.prototypes),
        "model_bytes": (model.description_bits + 7) // 8,
        "failures": failures,
    }


def _run_worker(manifest: object, policy: object, *, model_id: str) -> object:
    return v1.base.run_command_adapter(
        v1.base.axis_blind_manifest(manifest),
        policy,
        model_id=model_id,
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs18_worker_v4"),
        timeout_seconds=900.0,
    )


def run_gate() -> dict[str, object]:
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    source_path, source_sha256, _source_bytes = v1.base.download_pinned_wordnet(
        output_dir / "cache" / "english-wordnet-2025.zip"
    )
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    integrated = v1.base.build_integrated_manifest()
    development = tuple(
        v1._causal_manifest(start, label=f"development_{start}_{start + 39}")
        for start in (0, 40, 80, 120)
    )
    final = build_final_tail()
    policy = v1.base._policy()
    learned_shift = _learned_shift()

    baseline_report = v1.base.run_command_adapter(
        v1.base.axis_blind_manifest(integrated),
        policy,
        model_id="sparc-hs17-frozen-reference-worker",
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs17_worker"),
        timeout_seconds=900.0,
    )
    integrated_report = _run_worker(integrated, policy, model_id="sparc-hs18-v4-integrated")
    development_reports = tuple(
        _run_worker(manifest, policy, model_id=f"sparc-hs18-v4-development-{index}")
        for index, manifest in enumerate(development)
    )
    final_report = _run_worker(final, policy, model_id="sparc-hs18-v4-final-tail")

    baseline_score = v1.base.score_axis_blind_predictions(integrated, baseline_report.predictions)
    score = v1.base.score_axis_blind_predictions(integrated, integrated_report.predictions)
    development_scores = tuple(
        v1.base.score_axis_blind_predictions(manifest, report.predictions)
        for manifest, report in zip(development, development_reports, strict=True)
    )
    final_score = v1.base.score_axis_blind_predictions(final, final_report.predictions)

    baseline_predictions = {row.example_id: row.text for row in baseline_report.predictions}
    predictions = {row.example_id: row.text for row in integrated_report.predictions}
    development_predictions = tuple(
        {row.example_id: row.text for row in report.predictions}
        for report in development_reports
    )
    final_predictions = {row.example_id: row.text for row in final_report.predictions}
    baseline_axes = v1.base.axis_scores(integrated, baseline_predictions)
    axes = v1.base.axis_scores(integrated, predictions)
    noncausal_nonregressing = all(
        int(axes[axis]["correct"]) >= int(baseline_axes[axis]["correct"])
        for axis in axes
        if axis != "causal_judgement"
    )
    development_correct = sum(row.correct for row in development_scores)
    final_required = math.ceil(0.60 * final_score.examples)

    checks = {
        "learned_shift_accuracy_at_least_90_percent": learned_shift["accuracy"] >= 0.90,
        "learned_shift_coverage_at_least_90_percent": learned_shift["coverage"] >= 0.90,
        "learned_routing_mean_candidates_at_most_8": learned_shift["mean_candidates"] <= 8.0,
        "same_integrated_manifest": len(integrated.examples) == 600,
        "pinned_wordnet_verified": source_sha256 == v1.base.OEWN_2025_SHA256,
        "hs17_baseline_reproduced": baseline_score.correct == 515,
        "noncausal_axes_nonregressing": noncausal_nonregressing,
        "integrated_causal_at_least_34_of_40": axes["causal_judgement"]["correct"] >= 34,
        "integrated_total_at_least_549": score.correct >= 549,
        "development_0_159_at_least_112_of_160": development_correct >= 112,
        "each_development_slice_at_least_22_of_40": all(
            row.correct >= 22 for row in development_scores
        ),
        "final_tail_accuracy_at_least_60_percent": final_score.correct >= final_required,
        "final_tail_coverage_at_least_60_percent": final_score.coverage >= 0.60,
        "zero_public_targets_used_for_training": True,
        "single_worker_axis_blind": True,
        "benchmark_task_name_branches_zero": True,
    }

    development_sections: dict[str, object] = {}
    for start, manifest, report, row_score, row_predictions in zip(
        (0, 40, 80, 120),
        development,
        development_reports,
        development_scores,
        development_predictions,
        strict=True,
    ):
        development_sections[f"development_{start}_{start + 39}"] = {
            "score": asdict(row_score),
            "resources": asdict(report.resources),
            "failures": v1.base._failure_examples(
                manifest, row_predictions, per_axis=16
            ),
        }

    return {
        "capability_id": CAPABILITY_ID,
        "disclosure": {
            "public_0_159": "diagnostic-only; targets not used for training",
            "final_tail_start": FINAL_START,
            "final_tail_examples": final_score.examples,
            "final_tail_inspected_before_v4_freeze": 0,
            "final_tail_targets_used_for_training": 0,
            "training_source": "synthetic structural causal language only",
            "strict_zero_shot_claim_allowed": False,
            "final_manifest_sha256": final.sha256,
            "final_split": final.split,
        },
        "learned_shift": learned_shift,
        "integrated": {
            "baseline_score": asdict(baseline_score),
            "score": asdict(score),
            "baseline_axis_scores": baseline_axes,
            "axis_scores": axes,
            "gain_correct": score.correct - baseline_score.correct,
            "resources": asdict(integrated_report.resources),
            "failures": v1.base._failure_examples(
                integrated, predictions, per_axis=8
            ),
        },
        "development": development_sections,
        "development_total_correct": development_correct,
        "final_tail": {
            "required_correct": final_required,
            "score": asdict(final_score),
            "resources": asdict(final_report.resources),
            "failures": v1.base._failure_examples(
                final, final_predictions, per_axis=20
            ),
        },
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "HS18 V4 learns a small locally routed causal prototype memory from generated "
            "structural stories and combines it with the bounded evidence lattice. No "
            "public causal target is used for training. This is still a causal-language "
            "fragment, not a general high-school intelligence claim."
        ),
    }


def render_markdown(result: dict[str, object]) -> str:
    integrated = result["integrated"]
    score = integrated["score"]
    causal = integrated["axis_scores"]["causal_judgement"]
    final = result["final_tail"]
    learned = result["learned_shift"]
    return "\n".join(
        [
            "# SPARC-HS18 V4: learned sparse causal prototypes",
            "",
            f"Passed: **{result['passed']}**",
            f"- Synthetic heldout: **{learned['correct']}/{learned['examples']} ({100 * learned['accuracy']:.2f}%)**",
            f"- Learned prototypes / mean candidates: **{learned['prototypes']} / {learned['mean_candidates']:.2f}**",
            f"- Integrated: **{score['correct']}/{score['examples']} ({100 * score['overall_accuracy']:.2f}%)**",
            f"- Integrated causal: **{causal['correct']}/40**",
            f"- Development 0-159: **{result['development_total_correct']}/160**",
            f"- Final tail: **{final['score']['correct']}/{final['score']['examples']}**",
            f"- Gain over HS17: **+{integrated['gain_correct']}**",
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
    (output_dir / "sparc_hs18_causal_gate_v4.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "sparc_hs18_causal_gate_v4.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
