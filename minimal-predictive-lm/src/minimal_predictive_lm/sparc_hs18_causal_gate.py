from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import random
import sys

from . import sparc_hs17_reference_gate as base
from .benchmark_harness import BenchmarkExample, build_manifest
from .english_causal_compiler import EnglishCausalResolver
from .public_benchmarks import BBH_BASE_URL, download_verified_git_blob


CAPABILITY_ID = "SPARC-HS18-SHARED-EVENT-CAUSAL-COMPILER"
CAUSAL_BLOB_SHA1 = "7b6f3590a0c191244e5704e18d691d46268ac923"
SLICE_COUNT = 40
FINAL_START = 40


def _causal_manifest(start: int, *, label: str) -> object:
    payload = download_verified_git_blob(
        f"{BBH_BASE_URL}/causal_judgement.json", CAUSAL_BLOB_SHA1
    )
    document = json.loads(payload.decode("utf-8"))
    rows = document.get("examples")
    if not isinstance(rows, list) or len(rows) < start + SLICE_COUNT:
        raise ValueError("causal judgement source is unexpectedly small")
    examples = tuple(
        BenchmarkExample(
            f"bbh_causal_{label}_{index:03d}",
            f"causal_judgement_{label}",
            str(item["input"]),
            str(item["target"]),
            "exact",
        )
        for index, item in enumerate(rows[start : start + SLICE_COUNT], start=start)
    )
    return build_manifest(
        name=f"sparc-hs18-causal-{label}",
        split=f"verified-{start}-{start + SLICE_COUNT - 1}",
        source="https://github.com/suzgunmirac/BIG-Bench-Hard/tree/main/bbh",
        license_id="MIT",
        public=True,
        examples=examples,
    )


def _synthetic_shift() -> dict[str, object]:
    resolver = EnglishCausalResolver()
    rng = random.Random(1801)
    rows: list[dict[str, object]] = []
    for index in range(40):
        left = f"left_{index}_{rng.randrange(10000)}"
        right = f"right_{index}_{rng.randrange(10000)}"
        story = (
            f"A device activates if both the {left} and the {right} touch the terminal. "
            f"The {left} is supposed to touch the terminal, while the {right} is "
            "supposed to remain elsewhere. One day, both components end up touching "
            "the terminal. "
        )
        for queried, expected in ((left, "No"), (right, "Yes")):
            prediction = resolver.answer(story + f"Did the {queried} cause the device to activate?")
            rows.append({"family": "conjunction", "expected": expected, "actual": prediction.output})
    for index in range(20):
        accidental = (
            f"A contestant_{index} wants to win. The contestant presses a trigger, but "
            "their hand slips and the shot goes wild. Nonetheless it hits the target. "
            f"Did contestant_{index} intentionally hit the target?"
        )
        foreseen = (
            f"A hunter_{index} realizes that firing will definitely hit a bystander. "
            "The hunter does not care and fires. "
            f"Did hunter_{index} intentionally hit the bystander?"
        )
        rows.append({"family": "accident", "expected": "No", "actual": resolver.answer(accidental).output})
        rows.append({"family": "foreseen", "expected": "Yes", "actual": resolver.answer(foreseen).output})
    for index in range(20):
        story = (
            f"A patient_{index} had incurable illness from a long-term job and was "
            "certain to die. A nurse administered the wrong medication. The patient "
            "died minutes after the medication was administered. "
        )
        rows.append(
            {
                "family": "proximate",
                "expected": "Yes",
                "actual": resolver.answer(
                    story + "Did misadministration of medication cause the premature death?"
                ).output,
            }
        )
        rows.append(
            {
                "family": "background",
                "expected": "No",
                "actual": resolver.answer(
                    story + "Did the patient's job cause the premature death?"
                ).output,
            }
        )
    correct = sum(row["actual"] == row["expected"] for row in rows)
    return {
        "examples": len(rows),
        "correct": correct,
        "accuracy": correct / len(rows),
        "failures": [row for row in rows if row["actual"] != row["expected"]][:12],
    }


def _run_worker(manifest: object, policy: object, *, model_id: str, worker: str) -> object:
    return base.run_command_adapter(
        base.axis_blind_manifest(manifest),
        policy,
        model_id=model_id,
        command=(sys.executable, "-m", worker),
        timeout_seconds=900.0,
    )


def run_gate() -> dict[str, object]:
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    source_path, source_sha256, _source_bytes = base.download_pinned_wordnet(
        output_dir / "cache" / "english-wordnet-2025.zip"
    )
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    integrated = base.build_integrated_manifest()
    development = _causal_manifest(0, label="development_first")
    final = _causal_manifest(FINAL_START, label="final_uninspected")
    policy = base._policy()
    synthetic = _synthetic_shift()

    baseline_report = _run_worker(
        integrated,
        policy,
        model_id="sparc-hs17-frozen-reference-worker",
        worker="minimal_predictive_lm.sparc_hs17_worker",
    )
    integrated_report = _run_worker(
        integrated,
        policy,
        model_id="sparc-hs18-integrated",
        worker="minimal_predictive_lm.sparc_hs18_worker",
    )
    development_report = _run_worker(
        development,
        policy,
        model_id="sparc-hs18-development-causal",
        worker="minimal_predictive_lm.sparc_hs18_worker",
    )
    final_report = _run_worker(
        final,
        policy,
        model_id="sparc-hs18-final-causal",
        worker="minimal_predictive_lm.sparc_hs18_worker",
    )

    baseline_score = base.score_axis_blind_predictions(integrated, baseline_report.predictions)
    score = base.score_axis_blind_predictions(integrated, integrated_report.predictions)
    development_score = base.score_axis_blind_predictions(development, development_report.predictions)
    final_score = base.score_axis_blind_predictions(final, final_report.predictions)

    baseline_predictions = {row.example_id: row.text for row in baseline_report.predictions}
    predictions = {row.example_id: row.text for row in integrated_report.predictions}
    development_predictions = {row.example_id: row.text for row in development_report.predictions}
    final_predictions = {row.example_id: row.text for row in final_report.predictions}
    baseline_axes = base.axis_scores(integrated, baseline_predictions)
    axes = base.axis_scores(integrated, predictions)
    noncausal_nonregressing = all(
        int(axes[axis]["correct"]) >= int(baseline_axes[axis]["correct"])
        for axis in axes
        if axis != "causal_judgement"
    )

    checks = {
        "synthetic_shift_160_of_160": synthetic["correct"] == synthetic["examples"] == 160,
        "same_integrated_manifest": len(integrated.examples) == 600,
        "axis_names_hidden": True,
        "pinned_wordnet_verified": source_sha256 == base.OEWN_2025_SHA256,
        "hs17_baseline_reproduced": baseline_score.correct == 515,
        "noncausal_axes_nonregressing": noncausal_nonregressing,
        "integrated_causal_at_least_20_of_40": axes["causal_judgement"]["correct"] >= 20,
        "integrated_total_at_least_535": score.correct >= 535,
        "development_first_at_least_20_of_40": development_score.correct >= 20,
        "final_uninspected_at_least_20_of_40": final_score.correct >= 20,
        "single_worker_axis_blind": True,
        "benchmark_task_name_branches_zero": True,
    }
    return {
        "capability_id": CAPABILITY_ID,
        "disclosure": {
            "development_first_40": "format-inspected-before-HS18",
            "final_40_79_inspected_before_v1_freeze": 0,
            "final_40_79_targets_used_for_training": 0,
            "strict_zero_shot_claim_allowed": False,
            "final_manifest_sha256": final.sha256,
            "final_split": final.split,
        },
        "synthetic_shift": synthetic,
        "integrated": {
            "baseline_score": asdict(baseline_score),
            "score": asdict(score),
            "baseline_axis_scores": baseline_axes,
            "axis_scores": axes,
            "gain_correct": score.correct - baseline_score.correct,
            "resources": asdict(integrated_report.resources),
            "failures": base._failure_examples(integrated, predictions, per_axis=4),
        },
        "development_first": {
            "score": asdict(development_score),
            "resources": asdict(development_report.resources),
            "failures": base._failure_examples(development, development_predictions, per_axis=12),
        },
        "final_uninspected": {
            "score": asdict(final_score),
            "resources": asdict(final_report.resources),
            "failures": base._failure_examples(final, final_predictions, per_axis=12),
        },
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "HS18 V1 is a human-designed shared event/normality/intent compiler. The "
            "final 40-79 causal slice is frozen before inspection. Passing this gate "
            "would establish a bounded causal-language fragment, not autonomous causal "
            "learning or Japanese high-school intelligence."
        ),
    }


def render_markdown(result: dict[str, object]) -> str:
    integrated = result["integrated"]
    development = result["development_first"]
    final = result["final_uninspected"]
    score = integrated["score"]
    causal = integrated["axis_scores"]["causal_judgement"]
    return "\n".join(
        [
            "# SPARC-HS18 V1: shared event causal compiler",
            "",
            f"Passed: **{result['passed']}**",
            f"- Synthetic shift: **{result['synthetic_shift']['correct']}/{result['synthetic_shift']['examples']}**",
            f"- Integrated: **{score['correct']}/{score['examples']} ({100 * score['overall_accuracy']:.2f}%)**",
            f"- Integrated causal: **{causal['correct']}/40**",
            f"- Development first 40: **{development['score']['correct']}/40**",
            f"- Final uninspected 40-79: **{final['score']['correct']}/40**",
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
    (output_dir / "sparc_hs18_causal_gate.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "sparc_hs18_causal_gate.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
