from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_implicit_world import ImplicitWorldLearner
from .sparc_highschool_intervention_lattice_gate import run_gate as run_previous_gate
from .sparc_highschool_long_temporal_gate import _long_corpus
from .sparc_highschool_numeric_stream_gate import _numeric_corpus


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    previous = run_previous_gate(output / "previous-gate")
    started = time.perf_counter()
    learner = ImplicitWorldLearner()

    training_started = time.perf_counter()
    learner.learn_independent_documents(_corpus(), min_support=4)
    learner.learn_independent_numeric_documents(_numeric_corpus())
    learner.learn_long_chronological_documents(_long_corpus())
    training_seconds = time.perf_counter() - training_started

    correct = 0
    inference_seconds = 0.0
    max_candidates = 0
    max_feature_reads = 0
    max_constraint_reads = 0
    examples: list[dict[str, object]] = []
    for index in range(20):
        left = f"潜在主系列{index}"
        right = f"潜在副系列{index}"
        left_initial = 8 + index
        right_initial = 5 + index
        left_add = 3 + index % 2
        right_add = 4
        left_factor = 2
        right_factor = 3
        left_final = (left_initial + left_add) * left_factor
        right_final = (right_initial + right_add) * right_factor
        document = (
            f"{left}に{left_add}個加える。途中の記録を整理した。{left}を{left_factor}倍にする。"
            f"別の担当者は資料を確認した。{right}に{right_add}個加える。{right}を{right_factor}倍にする。"
            f"{left}には{left_final}個ある。{right}には{right_final}個ある。"
            "観測と出来事が矛盾しない初期状態を説明せよ。"
        )
        before_reads = learner.reverse_constraint_reads
        stamp = time.perf_counter()
        result = learner.infer_implicit_world(document)
        inference_seconds += time.perf_counter() - stamp
        reads = learner.reverse_constraint_reads - before_reads
        max_constraint_reads = max(max_constraint_reads, reads)
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        inferred = {(subject, value) for subject, _relation, value in result.inferred_values}
        expected = {(left, left_initial), (right, right_initial)}
        passed = (
            result.accepted
            and result.verified
            and inferred == expected
            and result.mechanism == "shared-reversible-affine-world-constraint"
            and "検算" in result.answer
            and reads <= 24
        )
        correct += int(passed)
        examples.append({
            "document": document,
            "accepted": result.accepted,
            "verified": result.verified,
            "inferred_values": result.inferred_values,
            "mechanism": result.mechanism,
            "constraint_reads": reads,
            "passed": passed,
        })

    axis_name = "implicit_multiobject_world_recovery"
    axes = dict(previous["axes"])
    axes[axis_name] = {"correct": correct, "total": 20}
    baseline_axes = dict(previous["axes"])
    baseline_axes[axis_name] = {"correct": 0, "total": 20}
    total_correct = sum(row["correct"] for row in axes.values())
    total = sum(row["total"] for row in axes.values())
    baseline_correct = previous["total_correct"]
    baseline_total = previous["total"] + 20
    percentages = {name: row["correct"] / row["total"] for name, row in axes.items()}
    minimum_axis = min(percentages, key=percentages.get)

    model = learner.report()
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    wall_seconds = time.perf_counter() - started
    estimated_ops = previous["estimated_sparse_operations"] + max_feature_reads * 20 + learner.reverse_constraint_reads
    no_regression = all(
        axes[name]["correct"] >= row["correct"] and axes[name]["total"] == row["total"]
        for name, row in previous["axes"].items()
    )
    improved = (
        total_correct / total > baseline_correct / baseline_total
        and percentages[axis_name] > 0.0
        and no_regression
    )
    efficient = (
        model["serialized_bytes"] <= 131072
        and peak_rss <= 536870912
        and wall_seconds <= 15.0
        and max_candidates <= 16
        and max_constraint_reads <= 24
    )
    report = {
        "stage": "SPARC-highschool-general-001-r15-shared-implicit-world-constraints",
        "baseline": {
            "axes": baseline_axes,
            "total_correct": baseline_correct,
            "total": baseline_total,
            "overall_accuracy": baseline_correct / baseline_total,
            "minimum_axis": axis_name,
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
        "max_constraint_reads": max_constraint_reads,
        "estimated_sparse_operations": estimated_ops,
        "wall_seconds": wall_seconds,
        "examples": examples,
        "structural_integration_passed": improved and efficient,
        "highschool_level_passed": False,
        "passed": improved and efficient,
        "claim_boundary": (
            "The same learner now compiles learned numeric transitions into reversible sparse affine constraints and recovers omitted initial values for multiple subjects from later observations, then verifies them with forward execution. The evaluation remains controlled synthetic Japanese; real textbooks, implicit qualitative states, broad knowledge, and natural open-ended conversation are unproven."
        ),
    }
    (output / "SPARC-highschool-general-implicit-world.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "SPARC-highschool-general-implicit-world.model.zlib").write_bytes(learner.to_bytes())
    lines = [
        "# SPARC shared implicit-world integrated gate",
        "",
        f"- baseline overall: {baseline_correct}/{baseline_total} ({baseline_correct / baseline_total:.2%})",
        f"- current overall: {total_correct}/{total} ({total_correct / total:.2%})",
        f"- current minimum axis: {minimum_axis} ({percentages[minimum_axis]:.2%})",
        f"- no regression: {no_regression}",
        f"- model bytes: {model['serialized_bytes']}",
        f"- peak RSS: {peak_rss}",
        f"- training seconds: {training_seconds:.6f}",
        f"- mean inference seconds: {report['mean_inference_seconds']:.9f}",
        f"- max candidates / feature reads / constraint reads: {max_candidates} / {max_feature_reads} / {max_constraint_reads}",
        f"- estimated sparse operations: {estimated_ops}",
        "",
        "## Axes",
    ]
    for name, row in axes.items():
        lines.append(f"- {name}: {row['correct']}/{row['total']}")
    lines += ["", "## Claim boundary", report["claim_boundary"]]
    (output / "SPARC-highschool-general-implicit-world.md").write_text("\n".join(lines), encoding="utf-8")
    if not report["passed"]:
        raise SystemExit("shared implicit-world integrated gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
