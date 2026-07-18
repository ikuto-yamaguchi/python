from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_evidence_revision_gate import run_gate as run_previous_gate
from .sparc_highschool_hypothesis_consensus import HypothesisConsensusWorkspaceLearner
from .sparc_highschool_long_temporal_gate import _long_corpus
from .sparc_highschool_numeric_stream_gate import _numeric_corpus


def _narrative(target: str, initial: int, add: int, note: str) -> str:
    observed = initial + add
    return (
        f"{target}に{add}個加える。{note}。{target}には{observed}個ある。"
        f"{target}を2倍にする。{target}について不足する状態を根拠付きで説明してください。"
    )


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    previous = run_previous_gate(output / "previous-gate")
    started = time.perf_counter()
    learner = HypothesisConsensusWorkspaceLearner(
        max_evidence_components=4,
        max_hypotheses_per_target=3,
    )
    training_started = time.perf_counter()
    learner.learn_independent_documents(_corpus(), min_support=4)
    learner.learn_independent_numeric_documents(_numeric_corpus())
    learner.learn_long_chronological_documents(_long_corpus())
    training_seconds = time.perf_counter() - training_started

    correct = 0
    inference_seconds = 0.0
    max_candidates = 0
    max_feature_reads = 0
    max_hypothesis_reads = 0
    max_graph_bytes = 0
    examples: list[dict[str, object]] = []
    for index in range(20):
        learner.reset_hypothesis_graph()
        target = f"仮説論点{index}A"
        stable = f"仮説論点{index}B"
        first_initial = 7 + index
        second_initial = first_initial + 5
        add = 2 + index % 4
        stable_initial = 4 + index

        stamp = time.perf_counter()
        learner.ingest_verified_hypothesis(
            _narrative(target, first_initial, add, "第一の未加工資料を確認した")
        )
        learner.ingest_verified_hypothesis(
            _narrative(target, second_initial, add, "別の未加工資料を確認した")
        )
        tied = learner.answer_from_hypothesis_graph(f"{target}の現在の結論を説明してください。")
        learner.ingest_verified_hypothesis(
            _narrative(target, second_initial, add, "独立した追加資料を確認した")
        )
        before_reads = learner.hypothesis_reads
        resolved = learner.answer_from_hypothesis_graph(f"{target}の現在の結論を説明してください。")
        reads = learner.hypothesis_reads - before_reads
        learner.ingest_verified_hypothesis(
            _narrative(stable, stable_initial, add + 1, "別論点の資料を確認した")
        )
        stable_result = learner.answer_from_hypothesis_graph(f"{stable}の結論を説明してください。")
        inference_seconds += time.perf_counter() - stamp

        max_hypothesis_reads = max(max_hypothesis_reads, reads)
        max_graph_bytes = max(max_graph_bytes, len(learner.hypothesis_graph_bytes()))
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        resolved_states = {(row[2], row[3]) for row in resolved.selected_states}
        stable_states = {(row[2], row[3]) for row in stable_result.selected_states}
        passed = (
            not tied.accepted
            and tied.mechanism == "abstain-unresolved-verified-hypothesis-conflict"
            and resolved.accepted
            and resolved.support == 2
            and resolved.competing_hypotheses == 2
            and (0, second_initial) in resolved_states
            and (0, first_initial) not in resolved_states
            and stable_result.accepted
            and stable_result.support == 1
            and (0, stable_initial) in stable_states
            and resolved.mechanism == "shared-bounded-verified-hypothesis-consensus-graph"
            and len(learner._hypotheses[target]) == 2
            and max_graph_bytes <= 8192
            and reads <= 3
        )
        correct += int(passed)
        examples.append({
            "target": target,
            "tied_abstained": not tied.accepted,
            "resolved_support": resolved.support,
            "competing_hypotheses": resolved.competing_hypotheses,
            "selected_states": resolved.selected_states,
            "stable_target_preserved": stable_result.accepted,
            "hypothesis_reads": reads,
            "graph_bytes": len(learner.hypothesis_graph_bytes()),
            "passed": passed,
        })

    axis_name = "verified_hypothesis_conflict_and_consensus"
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
    combined_model_bytes = int(model["serialized_bytes"]) + max_graph_bytes
    estimated_ops = (
        previous["estimated_sparse_operations"]
        + max_feature_reads * 20
        + learner.hypothesis_reads
        + learner.hypothesis_writes
        + learner.hypothesis_support_updates
        + learner.latent_constraint_reads
        + learner.latent_forward_checks
        + learner.latent_state_nodes_recovered
    )
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
        combined_model_bytes <= 131072
        and peak_rss <= 536870912
        and wall_seconds <= 20.0
        and max_candidates <= 16
        and max_graph_bytes <= 8192
        and max_hypothesis_reads <= 3
    )
    report = {
        "stage": "SPARC-highschool-general-001-r20-shared-verified-hypothesis-consensus",
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
        "combined_model_and_hypothesis_bytes": combined_model_bytes,
        "peak_rss_bytes": peak_rss,
        "training_seconds": training_seconds,
        "inference_seconds_total": inference_seconds,
        "mean_inference_seconds": inference_seconds / 20,
        "max_candidates": max_candidates,
        "max_feature_reads": max_feature_reads,
        "max_hypothesis_reads": max_hypothesis_reads,
        "max_hypothesis_graph_bytes": max_graph_bytes,
        "estimated_sparse_operations": estimated_ops,
        "wall_seconds": wall_seconds,
        "examples": examples,
        "structural_integration_passed": improved and efficient,
        "highschool_level_passed": False,
        "passed": improved and efficient,
        "claim_boundary": (
            "The same verified world learner now retains incompatible verified state components as bounded hypotheses, ignores exact duplicate evidence, abstains on equal support, and answers only after independent evidence gives one hypothesis uniquely greater support. Evaluation remains controlled synthetic Japanese; real source reliability, broad textbooks, qualitative claims, and natural free dialogue remain unproven."
        ),
    }
    (output / "SPARC-highschool-general-hypothesis-consensus.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "SPARC-highschool-general-hypothesis-consensus.model.zlib").write_bytes(
        learner.to_bytes()
    )
    (output / "SPARC-highschool-general-hypothesis-consensus.graph.json").write_bytes(
        learner.hypothesis_graph_bytes()
    )
    if not report["passed"]:
        raise SystemExit("shared verified-hypothesis consensus integrated gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
