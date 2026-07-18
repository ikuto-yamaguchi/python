from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_counterfactual import CounterfactualNarrativeLearner
from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_long_temporal_gate import _long_corpus, run_gate as run_previous_gate
from .sparc_highschool_numeric_stream_gate import _numeric_corpus


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # The previous frozen 216-point gate is rerun unchanged.  Its model is the
    # baseline on the expanded denominator and has no branch-comparison method.
    previous = run_previous_gate(output / "previous-gate")
    started = time.perf_counter()
    learner = CounterfactualNarrativeLearner()

    training_started = time.perf_counter()
    learner.learn_independent_documents(_corpus(), min_support=4)
    learner.learn_independent_numeric_documents(_numeric_corpus())
    learner.learn_long_chronological_documents(_long_corpus())
    training_seconds = time.perf_counter() - training_started

    counterfactual_correct = 0
    inference_seconds = 0.0
    queries = 0
    max_candidates = 0
    max_feature_reads = 0

    count_relation = next(
        relation
        for subject, relation in learner.learned_numeric_world().number_map()
        if subject == "青箱"
    )
    temperature_relation = next(
        relation
        for subject, relation in learner.learned_numeric_world().number_map()
        if subject == "試料甲"
    )

    for index in range(10, 20):
        subject = f"反実箱{index}"
        start = learner.observe_world([f"{subject}には{index}個ある"]).world
        stamp = time.perf_counter()
        result = learner.compare_intervention(
            start,
            [f"{subject}に3個加える", f"{subject}を2倍にする"],
            intervention_at=0,
            replacement_actions=[f"{subject}を2倍にする"],
        )
        inference_seconds += time.perf_counter() - stamp
        queries += 1
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        factual = result.factual.world.number_map().get((subject, count_relation))
        alternative = result.counterfactual.world.number_map().get((subject, count_relation))
        counterfactual_correct += int(
            result.accepted
            and factual == 2 * (index + 3)
            and alternative == 4 * index
            and result.changed_numbers
        )

    for index in range(10):
        subject = f"反実試料{index}"
        initial = 10 + index
        start = learner.observe_world([f"{subject}の温度は{initial}度である"]).world
        stamp = time.perf_counter()
        result = learner.compare_intervention(
            start,
            [f"{subject}の温度を5度上げる", f"{subject}の温度を5度上げる"],
            intervention_at=1,
            replacement_actions=[],
        )
        inference_seconds += time.perf_counter() - stamp
        queries += 1
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        factual = result.factual.world.number_map().get((subject, temperature_relation))
        alternative = result.counterfactual.world.number_map().get((subject, temperature_relation))
        counterfactual_correct += int(
            result.accepted
            and factual == initial + 10
            and alternative == initial + 5
            and result.changed_numbers
        )

    axes = dict(previous["axes"])
    axes["shared_counterfactual_branching"] = {
        "correct": counterfactual_correct,
        "total": 20,
    }
    total_correct = sum(row["correct"] for row in axes.values())
    total = sum(row["total"] for row in axes.values())
    percentages = {name: row["correct"] / row["total"] for name, row in axes.items()}
    minimum_axis = min(percentages, key=percentages.get)

    baseline_total = previous["total"] + 20
    baseline_correct = previous["total_correct"]
    baseline_axes = dict(previous["axes"])
    baseline_axes["shared_counterfactual_branching"] = {"correct": 0, "total": 20}
    model = learner.report()
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    wall_seconds = time.perf_counter() - started
    estimated_ops = previous["estimated_sparse_operations"] + max_feature_reads * max(1, queries)

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
        "stage": "SPARC-highschool-general-001-r9-shared-counterfactual-world-branches",
        "baseline": {
            "axes": baseline_axes,
            "total_correct": baseline_correct,
            "total": baseline_total,
            "overall_accuracy": baseline_correct / baseline_total,
            "minimum_axis": "shared_counterfactual_branching",
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
        "mean_inference_seconds": inference_seconds / max(1, queries),
        "max_candidates": max_candidates,
        "max_feature_reads": max_feature_reads,
        "estimated_sparse_operations": estimated_ops,
        "structural_integration_passed": improved and efficient,
        "highschool_level_passed": False,
        "passed": improved and efficient,
        "claim_boundary": (
            "The same learned event programs now create immutable factual and intervention branches from one shared prefix state. "
            "The expanded frozen baseline scores zero on this new axis. Real textbook counterfactual language, open-ended explanations, "
            "broad mathematics, and natural Japanese conversation remain unproven."
        ),
    }
    (output / "SPARC-highschool-general-counterfactual.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "SPARC-highschool-general-counterfactual.model.zlib").write_bytes(learner.to_bytes())
    lines = [
        "# SPARC shared counterfactual integrated gate",
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
    (output / "SPARC-highschool-general-counterfactual.md").write_text("\n".join(lines), encoding="utf-8")
    if not report["passed"]:
        raise SystemExit("shared counterfactual integrated gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
