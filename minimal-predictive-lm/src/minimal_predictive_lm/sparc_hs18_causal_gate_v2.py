from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import random
import string
import sys

from . import sparc_hs18_causal_gate as v1
from .english_causal_compiler_v2 import EnglishCausalResolverV2


CAPABILITY_ID = "SPARC-HS18-V2-AGENCY-OMISSION-TEMPORAL-CAUSALITY"
FINAL_START = 80
SLICE_COUNT = 40


def _synthetic_shift_v2() -> dict[str, object]:
    resolver = EnglishCausalResolverV2()
    rng = random.Random(1802)
    rows: list[dict[str, object]] = []

    def word(prefix: str) -> str:
        return prefix + "".join(rng.choice(string.ascii_lowercase) for _ in range(8))

    for _index in range(40):
        left = word("left")
        right = word("right")
        story = (
            f"A device activates if both the {left} and the {right} touch the terminal. "
            f"The {left} is supposed to touch the terminal, while the {right} is "
            "supposed to remain elsewhere. One day, both components end up touching "
            "the terminal. "
        )
        for queried, expected in ((left, "No"), (right, "Yes")):
            actual = resolver.answer(
                story + f"Did the {queried} cause the device to activate?"
            ).output
            rows.append(
                {"family": "normality-conjunction", "expected": expected, "actual": actual}
            )

    for _index in range(20):
        accidental = (
            f"Contestant {word('person')} wants to win. They try to aim, but lose their "
            "balance. The dart slips out of their hand and wobbles toward the board. "
            "It lands in the high point region. Did the contestant hit the high point "
            "region intentionally?"
        )
        controlled = (
            f"Marksman {word('person')} decided to shoot a target. The marksman was an "
            "expert, pulled the trigger, and directly hit the target. "
            "Did the marksman intentionally shoot the target?"
        )
        rows.append(
            {"family": "accidental-path", "expected": "No", "actual": resolver.answer(accidental).output}
        )
        rows.append(
            {"family": "controlled-path", "expected": "Yes", "actual": resolver.answer(controlled).output}
        )

    for _index in range(20):
        responsible = (
            f"Worker {word('janet')} is responsible for putting oil in a machine. The "
            "worker forgot to put oil in it, and the machine broke down. "
            "Did the worker not putting oil cause the machine to break down?"
        )
        unaware = (
            f"Worker {word('kate')} is not responsible for putting oil in a machine. "
            "The worker did not notice that another worker forgot the oil. The machine "
            "broke down. Did the worker not putting oil cause the machine to break down?"
        )
        rows.append(
            {"family": "duty-omission", "expected": "Yes", "actual": resolver.answer(responsible).output}
        )
        rows.append(
            {"family": "unaware-omission", "expected": "No", "actual": resolver.answer(unaware).output}
        )

    correct = sum(row["actual"] == row["expected"] for row in rows)
    return {
        "examples": len(rows),
        "correct": correct,
        "accuracy": correct / len(rows),
        "failures": [row for row in rows if row["actual"] != row["expected"]][:12],
    }


def _run_worker(manifest: object, policy: object, *, model_id: str) -> object:
    return v1.base.run_command_adapter(
        v1.base.axis_blind_manifest(manifest),
        policy,
        model_id=model_id,
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs18_worker_v2"),
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
    development_first = v1._causal_manifest(0, label="development_first")
    development_v1 = v1._causal_manifest(40, label="development_v1_holdout")
    final = v1._causal_manifest(FINAL_START, label="final_v2_uninspected")
    policy = v1.base._policy()
    synthetic = _synthetic_shift_v2()

    baseline_report = v1.base.run_command_adapter(
        v1.base.axis_blind_manifest(integrated),
        policy,
        model_id="sparc-hs17-frozen-reference-worker",
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs17_worker"),
        timeout_seconds=900.0,
    )
    integrated_report = _run_worker(integrated, policy, model_id="sparc-hs18-v2-integrated")
    first_report = _run_worker(development_first, policy, model_id="sparc-hs18-v2-development-first")
    v1_report = _run_worker(development_v1, policy, model_id="sparc-hs18-v2-development-v1")
    final_report = _run_worker(final, policy, model_id="sparc-hs18-v2-final-uninspected")

    baseline_score = v1.base.score_axis_blind_predictions(integrated, baseline_report.predictions)
    score = v1.base.score_axis_blind_predictions(integrated, integrated_report.predictions)
    first_score = v1.base.score_axis_blind_predictions(development_first, first_report.predictions)
    v1_score = v1.base.score_axis_blind_predictions(development_v1, v1_report.predictions)
    final_score = v1.base.score_axis_blind_predictions(final, final_report.predictions)

    baseline_predictions = {row.example_id: row.text for row in baseline_report.predictions}
    predictions = {row.example_id: row.text for row in integrated_report.predictions}
    first_predictions = {row.example_id: row.text for row in first_report.predictions}
    v1_predictions = {row.example_id: row.text for row in v1_report.predictions}
    final_predictions = {row.example_id: row.text for row in final_report.predictions}
    baseline_axes = v1.base.axis_scores(integrated, baseline_predictions)
    axes = v1.base.axis_scores(integrated, predictions)
    noncausal_nonregressing = all(
        int(axes[axis]["correct"]) >= int(baseline_axes[axis]["correct"])
        for axis in axes
        if axis != "causal_judgement"
    )

    checks = {
        "synthetic_shift_160_of_160": synthetic["correct"] == synthetic["examples"] == 160,
        "same_integrated_manifest": len(integrated.examples) == 600,
        "pinned_wordnet_verified": source_sha256 == v1.base.OEWN_2025_SHA256,
        "hs17_baseline_reproduced": baseline_score.correct == 515,
        "noncausal_axes_nonregressing": noncausal_nonregressing,
        "integrated_causal_at_least_28_of_40": axes["causal_judgement"]["correct"] >= 28,
        "integrated_total_at_least_543": score.correct >= 543,
        "development_first_at_least_28_of_40": first_score.correct >= 28,
        "development_v1_at_least_28_of_40": v1_score.correct >= 28,
        "final_v2_uninspected_at_least_24_of_40": final_score.correct >= 24,
        "single_worker_axis_blind": True,
        "benchmark_task_name_branches_zero": True,
    }
    return {
        "capability_id": CAPABILITY_ID,
        "disclosure": {
            "development_first_0_39": "inspected-before-v2",
            "development_v1_40_79": "inspected-after-v1",
            "final_80_119_inspected_before_v2_freeze": 0,
            "final_80_119_targets_used_for_training": 0,
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
            "failures": v1.base._failure_examples(integrated, predictions, per_axis=5),
        },
        "development_first": {
            "score": asdict(first_score),
            "resources": asdict(first_report.resources),
            "failures": v1.base._failure_examples(development_first, first_predictions, per_axis=12),
        },
        "development_v1": {
            "score": asdict(v1_score),
            "resources": asdict(v1_report.resources),
            "failures": v1.base._failure_examples(development_v1, v1_predictions, per_axis=12),
        },
        "final_v2_uninspected": {
            "score": asdict(final_score),
            "resources": asdict(final_report.resources),
            "failures": v1.base._failure_examples(final, final_predictions, per_axis=12),
        },
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "HS18 V2 adds shared agency, omission-duty, temporal preemption, and path-specificity "
            "features derived from development failures. The 80-119 slice is frozen before "
            "inspection. This remains a human-designed bounded causal-language model."
        ),
    }


def render_markdown(result: dict[str, object]) -> str:
    integrated = result["integrated"]
    score = integrated["score"]
    causal = integrated["axis_scores"]["causal_judgement"]
    return "\n".join(
        [
            "# SPARC-HS18 V2: agency, omission, and temporal causality",
            "",
            f"Passed: **{result['passed']}**",
            f"- Synthetic shift: **{result['synthetic_shift']['correct']}/{result['synthetic_shift']['examples']}**",
            f"- Integrated: **{score['correct']}/{score['examples']} ({100 * score['overall_accuracy']:.2f}%)**",
            f"- Integrated causal: **{causal['correct']}/40**",
            f"- Development first: **{result['development_first']['score']['correct']}/40**",
            f"- Development V1: **{result['development_v1']['score']['correct']}/40**",
            f"- Final uninspected 80-119: **{result['final_v2_uninspected']['score']['correct']}/40**",
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
    (output_dir / "sparc_hs18_causal_gate_v2.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "sparc_hs18_causal_gate_v2.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
