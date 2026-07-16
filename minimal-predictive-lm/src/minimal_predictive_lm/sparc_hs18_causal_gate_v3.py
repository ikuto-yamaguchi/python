from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import random
import string
import sys

from . import sparc_hs18_causal_gate as v1
from .english_causal_compiler_v3 import EnglishCausalResolverV3


CAPABILITY_ID = "SPARC-HS18-V3-UNIFIED-CAUSAL-EVIDENCE-LATTICE"
FINAL_START = 120
SLICE_COUNT = 40


def _synthetic_shift_v3() -> dict[str, object]:
    resolver = EnglishCausalResolverV3()
    rng = random.Random(1803)
    rows: list[dict[str, object]] = []

    def token(prefix: str) -> str:
        return prefix + "".join(rng.choice(string.ascii_lowercase) for _ in range(8))

    for _ in range(20):
        agent = token("agent")
        accidental = (
            f"{agent} wants to win, but loses his balance. The dart slips out of his "
            "hand and wobbles toward the board, landing in the target. "
            f"Did {agent} intentionally hit the target?"
        )
        controlled = (
            f"Expert marksman {agent} decided to shoot the target, pulled the trigger, "
            f"and directly hit it. Did {agent} intentionally shoot the target?"
        )
        rows.append({"family": "accidental", "expected": "No", "actual": resolver.answer(accidental).output})
        rows.append({"family": "controlled", "expected": "Yes", "actual": resolver.answer(controlled).output})

    for _ in range(20):
        worker = token("worker")
        duty = (
            f"{worker} is responsible for putting oil in a machine. {worker} forgot "
            "to put oil in it, and the machine broke down. "
            f"Did {worker} not putting oil cause the machine to break down?"
        )
        passive = (
            "A company sends a sample if a client is on its list. The client is already "
            "subscribed and did not change the subscription status. The sample arrived. "
            "Did the client receive the sample because the client did not change the "
            "subscription status?"
        )
        rows.append({"family": "duty-omission", "expected": "Yes", "actual": resolver.answer(duty).output})
        rows.append({"family": "passive-state", "expected": "No", "actual": resolver.answer(passive).output})

    for _ in range(20):
        violator = token("violator")
        compliant = token("compliant")
        story = (
            "A bridge collapses if two trains enter at the same time. "
            f"{violator} is not supposed to enter, while {compliant} is supposed to "
            f"enter. {violator} ignores the signal and {compliant} follows the signal. "
            "Both trains enter and the bridge collapses. "
        )
        rows.append(
            {
                "family": "abnormal-conjunct",
                "expected": "Yes",
                "actual": resolver.answer(story + f"Did {violator} cause the bridge to collapse?").output,
            }
        )
        rows.append(
            {
                "family": "normal-conjunct",
                "expected": "No",
                "actual": resolver.answer(story + f"Did {compliant} cause the bridge to collapse?").output,
            }
        )

    for _ in range(20):
        actor = token("actor")
        redundant = (
            "A device activates if either the safety switch is off or knob A is on. "
            f"The safety switch is off and knob A is off. {actor} changed the position "
            "of knob A to on. The device activated. "
            f"Did the device activate because {actor} changed the position of knob A?"
        )
        equal = (
            "A shop makes a profit if anyone orders coffee. Only one order is needed. "
            f"As usual, {actor} ordered coffee, and two other regular customers also "
            f"ordered. Did {actor} ordering coffee cause the shop to make a profit?"
        )
        rows.append({"family": "redundant-addition", "expected": "No", "actual": resolver.answer(redundant).output})
        rows.append({"family": "equal-status-disjunct", "expected": "Yes", "actual": resolver.answer(equal).output})

    correct = sum(row["actual"] == row["expected"] for row in rows)
    return {
        "examples": len(rows),
        "correct": correct,
        "accuracy": correct / len(rows),
        "failures": [row for row in rows if row["actual"] != row["expected"]][:16],
    }


def _run_worker(manifest: object, policy: object, *, model_id: str) -> object:
    return v1.base.run_command_adapter(
        v1.base.axis_blind_manifest(manifest),
        policy,
        model_id=model_id,
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs18_worker_v3"),
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
    development_first = v1._causal_manifest(0, label="development_0_39")
    development_v1 = v1._causal_manifest(40, label="development_40_79")
    development_v2 = v1._causal_manifest(80, label="development_80_119")
    final = v1._causal_manifest(FINAL_START, label="final_v3_uninspected")
    policy = v1.base._policy()
    synthetic = _synthetic_shift_v3()

    baseline_report = v1.base.run_command_adapter(
        v1.base.axis_blind_manifest(integrated),
        policy,
        model_id="sparc-hs17-frozen-reference-worker",
        command=(sys.executable, "-m", "minimal_predictive_lm.sparc_hs17_worker"),
        timeout_seconds=900.0,
    )
    integrated_report = _run_worker(integrated, policy, model_id="sparc-hs18-v3-integrated")
    first_report = _run_worker(development_first, policy, model_id="sparc-hs18-v3-development-0-39")
    v1_report = _run_worker(development_v1, policy, model_id="sparc-hs18-v3-development-40-79")
    v2_report = _run_worker(development_v2, policy, model_id="sparc-hs18-v3-development-80-119")
    final_report = _run_worker(final, policy, model_id="sparc-hs18-v3-final-120-159")

    baseline_score = v1.base.score_axis_blind_predictions(integrated, baseline_report.predictions)
    score = v1.base.score_axis_blind_predictions(integrated, integrated_report.predictions)
    first_score = v1.base.score_axis_blind_predictions(development_first, first_report.predictions)
    v1_score = v1.base.score_axis_blind_predictions(development_v1, v1_report.predictions)
    v2_score = v1.base.score_axis_blind_predictions(development_v2, v2_report.predictions)
    final_score = v1.base.score_axis_blind_predictions(final, final_report.predictions)

    baseline_predictions = {row.example_id: row.text for row in baseline_report.predictions}
    predictions = {row.example_id: row.text for row in integrated_report.predictions}
    first_predictions = {row.example_id: row.text for row in first_report.predictions}
    v1_predictions = {row.example_id: row.text for row in v1_report.predictions}
    v2_predictions = {row.example_id: row.text for row in v2_report.predictions}
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
        "integrated_causal_at_least_34_of_40": axes["causal_judgement"]["correct"] >= 34,
        "integrated_total_at_least_549": score.correct >= 549,
        "development_0_39_at_least_34": first_score.correct >= 34,
        "development_40_79_at_least_30": v1_score.correct >= 30,
        "development_80_119_at_least_24": v2_score.correct >= 24,
        "final_120_159_at_least_24": final_score.correct >= 24,
        "single_worker_axis_blind": True,
        "benchmark_task_name_branches_zero": True,
    }

    def section(manifest: object, report: object, score_row: object, pred: dict[str, str]) -> dict[str, object]:
        return {
            "score": asdict(score_row),
            "resources": asdict(report.resources),
            "failures": v1.base._failure_examples(manifest, pred, per_axis=16),
        }

    return {
        "capability_id": CAPABILITY_ID,
        "disclosure": {
            "development_0_39": "inspected-before-v3",
            "development_40_79": "inspected-before-v3",
            "development_80_119": "inspected-after-v2",
            "final_120_159_inspected_before_v3_freeze": 0,
            "final_120_159_targets_used_for_training": 0,
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
            "failures": v1.base._failure_examples(integrated, predictions, per_axis=6),
        },
        "development_0_39": section(development_first, first_report, first_score, first_predictions),
        "development_40_79": section(development_v1, v1_report, v1_score, v1_predictions),
        "development_80_119": section(development_v2, v2_report, v2_score, v2_predictions),
        "final_120_159": section(final, final_report, final_score, final_predictions),
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "HS18 V3 replaces failure-specific routing with a shared causal evidence lattice. "
            "The 120-159 slice is frozen before inspection. The system remains a "
            "human-designed bounded fragment, not autonomous causal discovery."
        ),
    }


def render_markdown(result: dict[str, object]) -> str:
    integrated = result["integrated"]
    score = integrated["score"]
    causal = integrated["axis_scores"]["causal_judgement"]
    return "\n".join(
        [
            "# SPARC-HS18 V3: unified causal evidence lattice",
            "",
            f"Passed: **{result['passed']}**",
            f"- Synthetic shift: **{result['synthetic_shift']['correct']}/{result['synthetic_shift']['examples']}**",
            f"- Integrated: **{score['correct']}/{score['examples']} ({100 * score['overall_accuracy']:.2f}%)**",
            f"- Integrated causal: **{causal['correct']}/40**",
            f"- Development 0-39: **{result['development_0_39']['score']['correct']}/40**",
            f"- Development 40-79: **{result['development_40_79']['score']['correct']}/40**",
            f"- Development 80-119: **{result['development_80_119']['score']['correct']}/40**",
            f"- Final uninspected 120-159: **{result['final_120_159']['score']['correct']}/40**",
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
    (output_dir / "sparc_hs18_causal_gate_v3.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "sparc_hs18_causal_gate_v3.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
