from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_evidence_quality_gate import run_gate as run_previous_gate
from .sparc_highschool_evidence_reliability import EvidenceReliabilityConsensusLearner
from .sparc_highschool_evidence_revision import EvidenceRevisionWorkspaceLearner
from .sparc_highschool_long_temporal_gate import _long_corpus
from .sparc_highschool_numeric_stream_gate import _numeric_corpus


def _weak(target: str, initial: int, add: int, note: str) -> str:
    return (
        f"{target}に{add}個加える。{note}。{target}には{initial + add}個ある。"
        f"{target}を2倍にする。{target}について不足する状態を根拠付きで説明してください。"
    )


def _strong(target: str, initial: int, add: int, note: str) -> str:
    final = (initial + add) * 2
    return (
        f"{target}には{initial}個ある。{target}に{add}個加える。"
        f"{target}を2倍にする。{target}には{final}個ある。{note}。"
        f"{target}について不足する状態を根拠付きで説明してください。"
    )


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    previous = run_previous_gate(output / "previous-gate")
    started = time.perf_counter()
    learner = EvidenceReliabilityConsensusLearner(
        max_evidence_components=8,
        max_hypotheses_per_target=3,
        max_lineages=12,
        lineage_similarity_threshold=0.50,
        max_quality_weight=3,
        max_reliability_score=4,
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
    max_quality_reads = 0
    max_reliability_reads = 0
    max_graph_bytes = 0
    examples = []

    for index in range(20):
        learner.reset_reliability_graph()
        reliable = f"第三者校正研究所{index}の標準器による継続測定"
        unreliable = f"旧式集計局{index}の推定装置による継続測定"
        stamp = time.perf_counter()
        calibration_ok = True
        for round_index in range(3):
            calibration_target = f"再現性校正{index}-{round_index}A"
            add = 2 + round_index
            truth = 8 + index + round_index
            learner.ingest_reliability_verified_hypothesis(
                _strong(calibration_target, truth + 5, add, unreliable)
            )
            learner.ingest_reliability_verified_hypothesis(
                _strong(calibration_target, truth, add, reliable)
            )
            learner.ingest_reliability_verified_hypothesis(
                _strong(calibration_target, truth, add, f"独立監査班{index}-{round_index}の再測定")
            )
            calibration_ok = learner.consolidate_verified_target(calibration_target) and calibration_ok

        target = f"未知再現性論点{index}B"
        reliable_initial = 11 + index
        unreliable_initial = reliable_initial + 5
        add = 3 + index % 3
        learner.ingest_reliability_verified_hypothesis(_weak(target, reliable_initial, add, reliable))
        learner.ingest_reliability_verified_hypothesis(_strong(target, unreliable_initial, add, unreliable))
        before_hypothesis = learner.hypothesis_reads
        before_quality = learner.quality_reads
        before_reliability = learner.reliability_reads
        resolved = learner.answer_from_reliability_graph(f"{target}の現在の結論を説明してください。")
        hypothesis_reads = learner.hypothesis_reads - before_hypothesis
        quality_reads = learner.quality_reads - before_quality
        reliability_reads = learner.reliability_reads - before_reliability
        inference_seconds += time.perf_counter() - stamp

        graph_bytes = len(learner.reliability_graph_bytes())
        max_graph_bytes = max(max_graph_bytes, graph_bytes)
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        max_hypothesis_reads = max(max_hypothesis_reads, hypothesis_reads)
        max_quality_reads = max(max_quality_reads, quality_reads)
        max_reliability_reads = max(max_reliability_reads, reliability_reads)
        selected = {(row[2], row[3]) for row in resolved.selected_states}
        passed = (
            calibration_ok
            and learner.reliability_consolidations == 3
            and resolved.accepted
            and (0, reliable_initial) in selected
            and (0, unreliable_initial) not in selected
            and resolved.competing_hypotheses == 2
            and resolved.mechanism == "shared-bounded-cross-topic-verified-source-reliability-graph"
            and graph_bytes <= 65536
            and hypothesis_reads <= 3
            and quality_reads <= 10
            and reliability_reads <= 10
        )
        correct += int(passed)
        examples.append({
            "target": target,
            "calibration_targets": 3,
            "reliable_initial": reliable_initial,
            "unreliable_initial": unreliable_initial,
            "selected_states": resolved.selected_states,
            "support": resolved.support,
            "reliability_scores": dict(sorted(learner._reliability.items())),
            "hypothesis_reads": hypothesis_reads,
            "quality_reads": quality_reads,
            "reliability_reads": reliability_reads,
            "graph_bytes": graph_bytes,
            "passed": passed,
        })

    axis_name = "cross_topic_verified_source_reliability"
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

    model = EvidenceRevisionWorkspaceLearner.report(learner)
    model.update({
        "shared_bounded_cross_topic_verified_source_reliability_graph": True,
        "hypothesis_targets": len(learner._hypotheses),
        "hypothesis_count": sum(len(rows) for rows in learner._hypotheses.values()),
        "lineages": len(learner._lineages),
        "reliability_entries": len(learner._reliability),
        "reliability_consolidations": learner.reliability_consolidations,
        "reliability_writes": learner.reliability_writes,
        "reliability_reads": learner.reliability_reads,
        "reliability_graph_bytes": len(learner.reliability_graph_bytes()),
        "task_name_supplied": False,
        "domain_name_supplied": False,
    })
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    wall_seconds = time.perf_counter() - started
    combined_model_bytes = int(model["serialized_bytes"]) + max_graph_bytes
    estimated_ops = (
        previous["estimated_sparse_operations"]
        + max_feature_reads * 20
        + learner.hypothesis_reads
        + learner.hypothesis_writes
        + learner.hypothesis_support_updates
        + learner.lineage_feature_reads
        + learner.lineage_comparisons
        + learner.quality_observation_reads
        + learner.quality_transition_reads
        + learner.quality_canonical_replays
        + learner.quality_reads
        + learner.reliability_reads
        + learner.reliability_writes
        + learner.reliability_consolidations
        + learner.latent_constraint_reads
        + learner.latent_forward_checks
        + learner.latent_state_nodes_recovered
    )
    no_regression = all(
        axes[name]["correct"] >= row["correct"] and axes[name]["total"] == row["total"]
        for name, row in previous["axes"].items()
    )
    improved = total_correct / total > baseline_correct / baseline_total and percentages[axis_name] > 0.0 and no_regression
    efficient = (
        combined_model_bytes <= 262144
        and peak_rss <= 536870912
        and wall_seconds <= 30.0
        and max_candidates <= 16
        and max_graph_bytes <= 65536
        and max_hypothesis_reads <= 3
        and max_quality_reads <= 10
        and max_reliability_reads <= 10
    )
    report = {
        "stage": "SPARC-highschool-general-001-r23-cross-topic-source-reliability",
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
        "combined_model_and_reliability_graph_bytes": combined_model_bytes,
        "peak_rss_bytes": peak_rss,
        "training_seconds": training_seconds,
        "inference_seconds_total": inference_seconds,
        "mean_inference_seconds": inference_seconds / 20,
        "max_candidates": max_candidates,
        "max_feature_reads": max_feature_reads,
        "max_hypothesis_reads": max_hypothesis_reads,
        "max_quality_reads": max_quality_reads,
        "max_reliability_reads": max_reliability_reads,
        "max_reliability_graph_bytes": max_graph_bytes,
        "estimated_sparse_operations": estimated_ops,
        "wall_seconds": wall_seconds,
        "examples": examples,
        "structural_integration_passed": improved and efficient,
        "highschool_level_passed": False,
        "passed": improved and efficient,
        "claim_boundary": "The same verified latent-world model now learns bounded cross-topic source reproducibility from uniquely resolved worlds and combines it with provenance independence and direct observation coverage. Evaluation remains controlled synthetic Japanese; real source identity, measurement uncertainty, broad textbooks, qualitative evidence, and natural free dialogue remain unproven.",
    }
    (output / "SPARC-highschool-general-evidence-reliability.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "SPARC-highschool-general-evidence-reliability.model.zlib").write_bytes(learner.to_bytes())
    (output / "SPARC-highschool-general-evidence-reliability.graph.json").write_bytes(
        learner.reliability_graph_bytes()
    )
    if not report["passed"]:
        raise SystemExit("cross-topic verified source reliability integrated gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
