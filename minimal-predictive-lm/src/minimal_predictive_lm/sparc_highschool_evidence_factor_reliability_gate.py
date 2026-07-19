from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_evidence_factor_reliability import EvidenceFactorReliabilityConsensusLearner
from .sparc_highschool_evidence_reliability_gate import run_gate as run_previous_gate
from .sparc_highschool_evidence_revision import EvidenceRevisionWorkspaceLearner
from .sparc_highschool_long_temporal_gate import _long_corpus
from .sparc_highschool_numeric_stream_gate import _numeric_corpus


def _strong(target: str, initial: int, add: int, note: str) -> str:
    return (
        f"{target}には{initial}個ある。{target}に{add}個加える。{target}を2倍にする。"
        f"{target}には{(initial + add) * 2}個ある。{note}。"
        f"{target}について不足する状態を根拠付きで説明してください。"
    )


def _weak(target: str, initial: int, add: int, note: str) -> str:
    return (
        f"{target}に{add}個加える。{note}。{target}には{initial + add}個ある。"
        f"{target}を2倍にする。{target}について不足する状態を根拠付きで説明してください。"
    )


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    previous = run_previous_gate(output / "previous-gate")
    started = time.perf_counter()
    learner = EvidenceFactorReliabilityConsensusLearner(
        max_evidence_components=10,
        max_hypotheses_per_target=3,
        max_lineages=16,
        lineage_similarity_threshold=0.50,
        max_quality_weight=3,
        max_reliability_score=4,
        max_factor_score=4,
        max_factor_entries=2048,
    )
    training_started = time.perf_counter()
    learner.learn_independent_documents(_corpus(), min_support=4)
    learner.learn_independent_numeric_documents(_numeric_corpus())
    learner.learn_long_chronological_documents(_long_corpus())
    training_seconds = time.perf_counter() - training_started

    correct = 0
    inference_seconds = 0.0
    max_candidates = max_feature_reads = max_hypothesis_reads = 0
    max_quality_reads = max_factor_reads = max_graph_bytes = 0
    examples = []
    for index in range(20):
        learner.reset_factor_reliability_graph()
        reliable_core = f"校正済み光学標準器{index}による直接測定"
        unreliable_core = f"未校正推定装置{index}による間接算出"
        stamp = time.perf_counter()
        calibration_ok = True
        for round_index in range(4):
            target = f"構成要素校正{index}-{round_index}"
            truth = 8 + index + round_index
            add = 2 + round_index % 3
            learner.ingest_factor_verified_hypothesis(
                _strong(target, truth + 5, add, f"旧倉庫記録群{round_index}の異なる長文背景と{unreliable_core}")
            )
            learner.ingest_factor_verified_hypothesis(
                _strong(target, truth, add, f"山岳観測班{round_index}の独立した長文背景と{reliable_core}")
            )
            learner.ingest_factor_verified_hypothesis(
                _strong(target, truth, add, f"第三者監査機関{index}-{round_index}による完全独立再測定")
            )
            calibration_ok = learner.consolidate_verified_target_factors(target) and calibration_ok

        target = f"未知構成要素論点{index}"
        reliable_initial = 13 + index
        unreliable_initial = reliable_initial + 5
        add = 3 + index % 3
        learner.ingest_factor_verified_hypothesis(
            _weak(target, reliable_initial, add, f"沿岸調査班の新規背景と{reliable_core}")
        )
        learner.ingest_factor_verified_hypothesis(
            _strong(target, unreliable_initial, add, f"都市集計班の新規背景と{unreliable_core}")
        )
        before_h = learner.hypothesis_reads
        before_q = learner.quality_reads
        before_f = learner.factor_reads
        resolved = learner.answer_from_factor_reliability_graph(f"{target}の現在の結論を説明してください。")
        inference_seconds += time.perf_counter() - stamp
        h_reads = learner.hypothesis_reads - before_h
        q_reads = learner.quality_reads - before_q
        f_reads = learner.factor_reads - before_f
        graph_bytes = len(learner.factor_reliability_graph_bytes())
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        max_hypothesis_reads = max(max_hypothesis_reads, h_reads)
        max_quality_reads = max(max_quality_reads, q_reads)
        max_factor_reads = max(max_factor_reads, f_reads)
        max_graph_bytes = max(max_graph_bytes, graph_bytes)
        selected = {(row[2], row[3]) for row in resolved.selected_states}
        passed = (
            calibration_ok
            and learner.factor_consolidations == 4
            and resolved.accepted
            and (0, reliable_initial) in selected
            and (0, unreliable_initial) not in selected
            and resolved.mechanism == "shared-bounded-verified-source-factor-reliability-graph"
            and graph_bytes <= 131072
            and h_reads <= 3
            and q_reads <= 10
            and f_reads <= 512
        )
        correct += int(passed)
        examples.append({
            "target": target,
            "selected_states": resolved.selected_states,
            "factor_entries": len(learner._factor_reliability),
            "factor_reads": f_reads,
            "graph_bytes": graph_bytes,
            "passed": passed,
        })

    axis_name = "cross_lineage_verified_source_factor_reliability"
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
        "shared_bounded_verified_source_factor_reliability_graph": True,
        "factor_entries": len(learner._factor_reliability),
        "factor_reads": learner.factor_reads,
        "factor_writes": learner.factor_writes,
        "factor_consolidations": learner.factor_consolidations,
        "task_name_supplied": False,
        "domain_name_supplied": False,
    })
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    wall_seconds = time.perf_counter() - started
    combined_model_bytes = int(model["serialized_bytes"]) + max_graph_bytes
    estimated_ops = (
        previous["estimated_sparse_operations"]
        + max_feature_reads * 20
        + learner.hypothesis_reads + learner.hypothesis_writes + learner.hypothesis_support_updates
        + learner.lineage_feature_reads + learner.lineage_comparisons
        + learner.quality_observation_reads + learner.quality_transition_reads
        + learner.quality_canonical_replays + learner.quality_reads
        + learner.factor_reads + learner.factor_writes + learner.factor_consolidations
        + learner.latent_constraint_reads + learner.latent_forward_checks + learner.latent_state_nodes_recovered
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
        and max_graph_bytes <= 131072
        and max_hypothesis_reads <= 3
        and max_quality_reads <= 10
        and max_factor_reads <= 512
    )
    report = {
        "stage": "SPARC-highschool-general-001-r24-source-factor-reliability",
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
        "combined_model_and_factor_graph_bytes": combined_model_bytes,
        "peak_rss_bytes": peak_rss,
        "training_seconds": training_seconds,
        "inference_seconds_total": inference_seconds,
        "mean_inference_seconds": inference_seconds / 20,
        "max_candidates": max_candidates,
        "max_feature_reads": max_feature_reads,
        "max_hypothesis_reads": max_hypothesis_reads,
        "max_quality_reads": max_quality_reads,
        "max_factor_reads": max_factor_reads,
        "max_factor_graph_bytes": max_graph_bytes,
        "estimated_sparse_operations": estimated_ops,
        "wall_seconds": wall_seconds,
        "examples": examples,
        "structural_integration_passed": improved and efficient,
        "highschool_level_passed": False,
        "passed": improved and efficient,
        "claim_boundary": "The same verified latent-world model now transfers bounded reproducibility through sparse source factors shared across otherwise distinct provenance lineages. Evaluation remains controlled synthetic Japanese; real actor, instrument, condition, time and citation extraction, broad textbooks and natural free dialogue remain unproven.",
    }
    (output / "SPARC-highschool-general-evidence-factor-reliability.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "SPARC-highschool-general-evidence-factor-reliability.model.zlib").write_bytes(learner.to_bytes())
    (output / "SPARC-highschool-general-evidence-factor-reliability.graph.json").write_bytes(
        learner.factor_reliability_graph_bytes()
    )
    if not report["passed"]:
        raise SystemExit("verified source factor reliability integrated gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
