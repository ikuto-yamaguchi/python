from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_counterfactual_gate import run_gate as run_previous_gate
from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_long_temporal_gate import _long_corpus
from .sparc_highschool_narrative_alignment import NarrativeAlignedLearner
from .sparc_highschool_numeric_stream_gate import _numeric_corpus


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    previous = run_previous_gate(output / "previous-gate")
    started = time.perf_counter()
    learner = NarrativeAlignedLearner()

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
        subject = f"物語箱{index}"
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
        result = learner.infer_counterfactual_narrative(document)
        inference_seconds += time.perf_counter() - stamp
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        actual_value = None
        alternative_value = None
        if result.accepted and result.comparison is not None:
            actual_values = result.comparison.factual.world.number_map()
            alternative_values = result.comparison.counterfactual.world.number_map()
            actual_value = next(iter(actual_values.values())) if len(actual_values) == 1 else None
            alternative_value = next(iter(alternative_values.values())) if len(alternative_values) == 1 else None
        passed = (
            result.accepted
            and result.intervention_at == 0
            and actual_value == factual
            and alternative_value == alternative
        )
        correct += int(passed)
        examples.append(
            {
                "document": document,
                "accepted": result.accepted,
                "intervention_at": result.intervention_at,
                "factual_value": actual_value,
                "counterfactual_value": alternative_value,
                "passed": passed,
            }
        )

    axes = dict(previous["axes"])
    axes["unlabeled_multiparagraph_world_alignment"] = {"correct": correct, "total": 20}
    total_correct = sum(row["correct"] for row in axes.values())
    total = sum(row["total"] for row in axes.values())
    percentages = {name: row["correct"] / row["total"] for name, row in axes.items()}
    minimum_axis = min(percentages, key=percentages.get)
    baseline_total = previous["total"] + 20
    baseline_correct = previous["total_correct"]
    baseline_axes = dict(previous["axes"])
    baseline_axes["unlabeled_multiparagraph_world_alignment"] = {"correct": 0, "total": 20}

    model = learner.report()
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    wall_seconds = time.perf_counter() - started
    estimated_ops = previous["estimated_sparse_operations"] + max_feature_reads * 20
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
        and wall_seconds <= 8.0
        and max_candidates <= 16
    )
    report = {
        "stage": "SPARC-highschool-general-001-r10-unlabeled-narrative-world-alignment",
        "baseline": {
            "axes": baseline_axes,
            "total_correct": baseline_correct,
            "total": baseline_total,
            "overall_accuracy": baseline_correct / baseline_total,
            "minimum_axis": "unlabeled_multiparagraph_world_alignment",
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
            "One shared learner now infers observed endpoints, the factual executable path, and a program-aligned replacement event from an unlabeled multi-sentence narrative. "
            "The intervention index and separated action lists are not supplied. The documents remain controlled synthetic Japanese; real textbooks, open-ended explanations, broad calculation verification, and natural conversation are unproven."
        ),
    }
    (output / "SPARC-highschool-general-narrative-alignment.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "SPARC-highschool-general-narrative-alignment.model.zlib").write_bytes(learner.to_bytes())
    lines = [
        "# SPARC unlabeled narrative alignment integrated gate",
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
    (output / "SPARC-highschool-general-narrative-alignment.md").write_text("\n".join(lines), encoding="utf-8")
    if not report["passed"]:
        raise SystemExit("unlabeled narrative alignment integrated gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
