from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_grounded_explanation import GroundedExplanationLearner
from .sparc_highschool_long_temporal_gate import _long_corpus
from .sparc_highschool_narrative_alignment_gate import run_gate as run_previous_gate
from .sparc_highschool_numeric_stream_gate import _numeric_corpus


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    previous = run_previous_gate(output / "previous-gate")
    started = time.perf_counter()
    learner = GroundedExplanationLearner()

    training_started = time.perf_counter()
    learner.learn_independent_documents(_corpus(), min_support=4)
    learner.learn_independent_numeric_documents(_numeric_corpus())
    learner.learn_long_chronological_documents(_long_corpus())
    training_seconds = time.perf_counter() - training_started

    correct = 0
    inference_seconds = 0.0
    max_candidates = 0
    max_feature_reads = 0
    examples: list[dict[str, object]] = []
    for index in range(20):
        subject = f"説明箱{index}"
        initial = 10 + index
        factual = 2 * (initial + 3)
        alternative = 2 * (initial + 5)
        document = (
            f"{subject}には{initial}個ある。\n"
            f"{subject}に3個加える。担当者は途中の記録を確認した。{subject}を2倍にする。"
            f"{subject}には{factual}個ある。\n"
            f"別の案として{subject}に5個加える。結果の違いを説明せよ。"
        )
        stamp = time.perf_counter()
        result = learner.explain_counterfactual_narrative(document)
        inference_seconds += time.perf_counter() - stamp
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        expected_factual = (initial, initial + 3, factual)
        expected_counterfactual = (initial, initial + 5, alternative)
        passed = (
            result.accepted
            and result.verified
            and result.factual_trace == expected_factual
            and result.counterfactual_trace == expected_counterfactual
            and str(factual) in result.answer
            and str(alternative) in result.answer
            and "検算" in result.answer
        )
        correct += int(passed)
        examples.append({
            "document": document,
            "accepted": result.accepted,
            "verified": result.verified,
            "factual_trace": result.factual_trace,
            "counterfactual_trace": result.counterfactual_trace,
            "answer": result.answer,
            "passed": passed,
        })

    axes = dict(previous["axes"])
    axes["grounded_freeform_explanation_with_verification"] = {"correct": correct, "total": 20}
    total_correct = sum(row["correct"] for row in axes.values())
    total = sum(row["total"] for row in axes.values())
    percentages = {name: row["correct"] / row["total"] for name, row in axes.items()}
    minimum_axis = min(percentages, key=percentages.get)
    baseline_total = previous["total"] + 20
    baseline_correct = previous["total_correct"]
    baseline_axes = dict(previous["axes"])
    baseline_axes["grounded_freeform_explanation_with_verification"] = {"correct": 0, "total": 20}

    model = learner.report()
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    wall_seconds = time.perf_counter() - started
    estimated_ops = previous["estimated_sparse_operations"] + max_feature_reads * 40
    no_regression = all(
        axes[name]["correct"] >= row["correct"] and axes[name]["total"] == row["total"]
        for name, row in previous["axes"].items()
    )
    improved = (
        total_correct / total > baseline_correct / baseline_total
        and min(percentages.values()) > 0.0
        and no_regression
    )
    efficient = (
        model["serialized_bytes"] <= 131072
        and peak_rss <= 536870912
        and wall_seconds <= 12.0
        and max_candidates <= 16
    )
    report = {
        "stage": "SPARC-highschool-general-001-r11-grounded-explanation-verification",
        "baseline": {
            "axes": baseline_axes,
            "total_correct": baseline_correct,
            "total": baseline_total,
            "overall_accuracy": baseline_correct / baseline_total,
            "minimum_axis": "grounded_freeform_explanation_with_verification",
            "minimum_axis_accuracy": 0.0,
            "model_bytes": previous["model"]["serialized_bytes"],
        },
        "axes": axes,
        "total_correct": total_correct,
        "total": total,
        "overall_accuracy": total_correct / total,
        "minimum_axis": minimum_axis,
        "minimum_axis_accuracy": percentages[minimum_axis],
        "no_regression": no_regression,
        "aggregate_improved": improved,
        "efficiency_acceptable": efficient,
        "model": model,
        "peak_rss_bytes": peak_rss,
        "training_seconds": training_seconds,
        "inference_seconds_total": inference_seconds,
        "mean_inference_seconds": inference_seconds / 20,
        "max_candidates": max_candidates,
        "max_feature_reads": max_feature_reads,
        "estimated_sparse_operations": estimated_ops,
        "wall_seconds": wall_seconds,
        "examples": examples,
        "structural_integration_passed": improved and efficient,
        "highschool_level_passed": False,
        "passed": improved and efficient,
        "claim_boundary": (
            "The same learner now aligns an unlabeled narrative, replays factual and intervention paths through one executor, verifies both final worlds, and verbalizes only the reproduced traces. "
            "The material remains controlled synthetic Japanese; real textbooks, implicit questions, broad mathematics, and natural open-ended conversation are unproven."
        ),
    }
    (output / "SPARC-highschool-general-grounded-explanation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "SPARC-highschool-general-grounded-explanation.model.zlib").write_bytes(learner.to_bytes())
    lines = [
        "# SPARC grounded explanation and verification integrated gate",
        "",
        f"- baseline overall: {baseline_correct}/{baseline_total} ({baseline_correct / baseline_total:.2%})",
        f"- current overall: {total_correct}/{total} ({total_correct / total:.2%})",
        f"- current minimum axis: {minimum_axis} ({percentages[minimum_axis]:.2%})",
        f"- no regression: {no_regression}",
        f"- model bytes: {model['serialized_bytes']}",
        f"- peak RSS: {peak_rss}",
        f"- training seconds: {training_seconds:.6f}",
        f"- mean inference seconds: {report['mean_inference_seconds']:.9f}",
        f"- max candidates / feature reads: {max_candidates} / {max_feature_reads}",
        f"- estimated sparse operations: {estimated_ops}",
        "",
        "## Axes",
    ]
    for name, row in axes.items():
        lines.append(f"- {name}: {row['correct']}/{row['total']}")
    lines += ["", "## Claim boundary", report["claim_boundary"]]
    (output / "SPARC-highschool-general-grounded-explanation.md").write_text("\n".join(lines), encoding="utf-8")
    if not report["passed"]:
        raise SystemExit("grounded explanation integrated gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
