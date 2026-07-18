from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_evidence_lineage_gate import run_gate as run_previous_gate
from .sparc_highschool_evidence_quality import EvidenceQualityConsensusLearner
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
    learner = EvidenceQualityConsensusLearner(
        max_evidence_components=4,
        max_hypotheses_per_target=3,
        max_lineages=10,
        lineage_similarity_threshold=0.50,
        max_quality_weight=3,
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
    max_graph_bytes = 0
    examples = []
    for index in range(20):
        learner.reset_quality_graph()
        target = f"品質論点{index}A"
        stable = f"品質論点{index}B"
        weak_initial = 7 + index
        strong_initial = weak_initial + 5
        stable_initial = 3 + index
        add = 2 + index % 4
        stamp = time.perf_counter()
        for note in (f"北側の伝聞記録{index}", f"西側の間接記録{index}", f"旧帳簿の再構成{index}"):
            learner.ingest_quality_verified_hypothesis(_weak(target, weak_initial, add, note))
        for note in (
            f"山岳観測所{index}の光学計器による原簿",
            f"沿岸研究船{index}の重量センサー再測定",
        ):
            learner.ingest_quality_verified_hypothesis(_strong(target, strong_initial, add, note))
        before_reads = learner.hypothesis_reads
        before_quality_reads = learner.quality_reads
        resolved = learner.answer_from_quality_graph(f"{target}の現在の結論を説明してください。")
        hypothesis_reads = learner.hypothesis_reads - before_reads
        quality_reads = learner.quality_reads - before_quality_reads
        learner.ingest_quality_verified_hypothesis(
            _strong(stable, stable_initial, add + 1, f"河川監視塔{index}の流量計による直接観測")
        )
        stable_result = learner.answer_from_quality_graph(f"{stable}の結論を説明してください。")
        inference_seconds += time.perf_counter() - stamp

        max_hypothesis_reads = max(max_hypothesis_reads, hypothesis_reads)
        max_quality_reads = max(max_quality_reads, quality_reads)
        max_graph_bytes = max(max_graph_bytes, len(learner.quality_graph_bytes()))
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        selected = {(row[2], row[3]) for row in resolved.selected_states}
        stable_states = {(row[2], row[3]) for row in stable_result.selected_states}
        passed = (
            resolved.accepted
            and resolved.support == 4
            and resolved.competing_hypotheses == 2
            and (0, strong_initial) in selected
            and (0, weak_initial) not in selected
            and stable_result.accepted
            and stable_result.support == 2
            and (0, stable_initial) in stable_states
            and resolved.mechanism == "shared-bounded-verified-evidence-quality-consensus-graph"
            and max_graph_bytes <= 32768
            and hypothesis_reads <= 3
            and quality_reads <= 10
        )
        correct += int(passed)
        examples.append({
            "target": target,
            "weak_independent_lineages": 3,
            "strong_independent_lineages": 2,
            "weak_total_weight": 3,
            "strong_total_weight": resolved.support,
            "selected_states": resolved.selected_states,
            "stable_target_preserved": stable_result.accepted,
            "hypothesis_reads": hypothesis_reads,
            "quality_reads": quality_reads,
            "graph_bytes": len(learner.quality_graph_bytes()),
            "passed": passed,
        })

    axis_name = "verified_evidence_structural_quality"
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
        "shared_bounded_verified_evidence_quality_consensus_graph": True,
        "hypothesis_targets": len(learner._hypotheses),
        "hypothesis_count": sum(len(rows) for rows in learner._hypotheses.values()),
        "lineages": len(learner._lineages),
        "quality_observation_reads": learner.quality_observation_reads,
        "quality_transition_reads": learner.quality_transition_reads,
        "quality_canonical_replays": learner.quality_canonical_replays,
        "quality_writes": learner.quality_writes,
        "quality_reads": learner.quality_reads,
        "quality_graph_bytes": len(learner.quality_graph_bytes()),
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
        combined_model_bytes <= 196608
        and peak_rss <= 536870912
        and wall_seconds <= 25.0
        and max_candidates <= 16
        and max_graph_bytes <= 32768
        and max_hypothesis_reads <= 3
        and max_quality_reads <= 10
    )
    report = {
        "stage": "SPARC-highschool-general-001-r22-shared-verified-evidence-quality",
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
        "combined_model_and_quality_graph_bytes": combined_model_bytes,
        "peak_rss_bytes": peak_rss,
        "training_seconds": training_seconds,
        "inference_seconds_total": inference_seconds,
        "mean_inference_seconds": inference_seconds / 20,
        "max_candidates": max_candidates,
        "max_feature_reads": max_feature_reads,
        "max_hypothesis_reads": max_hypothesis_reads,
        "max_quality_reads": max_quality_reads,
        "max_quality_graph_bytes": max_graph_bytes,
        "estimated_sparse_operations": estimated_ops,
        "wall_seconds": wall_seconds,
        "examples": examples,
        "structural_integration_passed": improved and efficient,
        "highschool_level_passed": False,
        "passed": improved and efficient,
        "claim_boundary": "The same verified latent-world learner now canonicalizes worlds across observation layouts and ranks independent lineages by bounded directly replayable observation coverage rather than raw source count. Evaluation remains controlled synthetic Japanese; broad textbooks, qualitative evidence quality, source expertise, real measurement uncertainty, and natural free dialogue remain unproven.",
    }
    (output / "SPARC-highschool-general-evidence-quality.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "SPARC-highschool-general-evidence-quality.model.zlib").write_bytes(learner.to_bytes())
    (output / "SPARC-highschool-general-evidence-quality.graph.json").write_bytes(learner.quality_graph_bytes())
    if not report["passed"]:
        raise SystemExit("shared verified-evidence quality integrated gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
