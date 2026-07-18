from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_implicit_world_gate import run_gate as run_previous_gate
from .sparc_highschool_latent_state_graph import LatentStateGraphLearner
from .sparc_highschool_long_temporal_gate import _long_corpus
from .sparc_highschool_numeric_stream_gate import _numeric_corpus


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    previous = run_previous_gate(output / "previous-gate")
    started = time.perf_counter()
    learner = LatentStateGraphLearner()
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
        left = f"潜在時系列A{index}"
        right = f"潜在時系列B{index}"
        unrelated = f"未観測系列{index}"
        fixed = f"固定資料{index}"
        fixed_value = 99 + index
        left_initial = 7 + index
        left_add = 2 + index % 3
        left_middle = left_initial + left_add
        left_after_mul = left_middle * 2
        left_final = left_after_mul + 4
        right_initial = 5 + index
        right_middle = right_initial * 3
        right_final = right_middle + 2
        document = (
            f"{unrelated}に5個加える。{fixed}には{fixed_value}個ある。"
            f"{left}に{left_add}個加える。{left}には{left_middle}個ある。"
            f"別資料を確認した。{left}を2倍にする。{left}に4個加える。{left}には{left_final}個ある。"
            f"{right}を3倍にする。{right}には{right_middle}個ある。{right}に2個加える。"
            "観測されていない各時点の状態を、同じ出来事の流れから説明せよ。"
        )
        before_reads = learner.latent_constraint_reads
        before_skipped = learner.latent_unanchored_components_skipped
        before_fixed = learner.latent_fixed_observation_components
        stamp = time.perf_counter()
        result = learner.infer_latent_state_graph(document)
        inference_seconds += time.perf_counter() - stamp
        reads = learner.latent_constraint_reads - before_reads
        skipped = learner.latent_unanchored_components_skipped - before_skipped
        fixed_components = learner.latent_fixed_observation_components - before_fixed
        max_constraint_reads = max(max_constraint_reads, reads)
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        recovered = {(subject, node, value) for subject, _relation, node, value in result.recovered_states}
        expected = {
            (left, 0, left_initial),
            (left, 2, left_after_mul),
            (right, 0, right_initial),
            (right, 2, right_final),
        }
        passed = (
            result.accepted
            and result.verified
            and expected.issubset(recovered)
            and result.mechanism == "shared-bidirectional-latent-state-graph"
            and "検算" in result.answer
            and result.initial_world.number_map().get((fixed, "count")) == fixed_value
            and result.final_world.number_map().get((fixed, "count")) == fixed_value
            and (unrelated, "count") not in result.initial_world.number_map()
            and skipped == 1
            and fixed_components == 1
            and reads <= 42
        )
        correct += int(passed)
        examples.append({
            "document": document,
            "accepted": result.accepted,
            "verified": result.verified,
            "recovered_states": result.recovered_states,
            "constraint_reads": reads,
            "unanchored_components_skipped": skipped,
            "fixed_observation_components": fixed_components,
            "passed": passed,
        })

    axis_name = "bidirectional_latent_state_graph"
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
    estimated_ops = (
        previous["estimated_sparse_operations"]
        + max_feature_reads * 20
        + learner.latent_constraint_reads
        + learner.latent_forward_checks
    )
    no_regression = all(
        axes[name]["correct"] >= row["correct"] and axes[name]["total"] == row["total"]
        for name, row in previous["axes"].items()
    )
    improved = (
        total_correct / total > baseline_correct / baseline_total
        and percentages[axis_name] > 0
        and no_regression
    )
    efficient = (
        model["serialized_bytes"] <= 131072
        and peak_rss <= 536870912
        and wall_seconds <= 20.0
        and max_candidates <= 16
        and max_constraint_reads <= 42
    )
    report = {
        "stage": "SPARC-highschool-general-001-r16-shared-bidirectional-latent-state-graph",
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
            "The same learner now solves omitted initial, intermediate, and terminal "
            "numeric states by propagating learned sparse affine transitions in both "
            "directions, selecting only observation-anchored transition components, "
            "preserving observation-only fixed context, and verifying every relevant "
            "observation. Evaluation remains controlled synthetic Japanese; real "
            "textbooks, broad qualitative relations, and natural open-ended dialogue "
            "are unproven."
        ),
    }
    (output / "SPARC-highschool-general-latent-state-graph.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output / "SPARC-highschool-general-latent-state-graph.model.zlib").write_bytes(
        learner.to_bytes()
    )
    if not report["passed"]:
        raise SystemExit("shared bidirectional latent-state integrated gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
