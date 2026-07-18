from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_evidence_lineage import EvidenceLineageConsensusLearner
from .sparc_highschool_evidence_revision import EvidenceRevisionWorkspaceLearner
from .sparc_highschool_hypothesis_consensus_gate import run_gate as run_previous_gate
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
    learner = EvidenceLineageConsensusLearner(
        max_evidence_components=4,
        max_hypotheses_per_target=3,
        max_lineages=10,
        lineage_similarity_threshold=0.50,
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
    max_lineage_reads = 0
    max_graph_bytes = 0
    examples: list[dict[str, object]] = []
    for index in range(20):
        learner.reset_lineage_graph()
        target = f"由来論点{index}A"
        stable = f"由来論点{index}B"
        copied_initial = 7 + index
        independent_initial = copied_initial + 5
        stable_initial = 3 + index
        add = 2 + index % 4

        stamp = time.perf_counter()
        before_features = learner.lineage_feature_reads
        learner.ingest_lineage_verified_hypothesis(
            _narrative(target, copied_initial, add, "共同記録班の一次資料をそのまま転記した")
        )
        learner.ingest_lineage_verified_hypothesis(
            _narrative(target, copied_initial, add, "共同記録班の一次資料を一部整形して転記した")
        )
        learner.ingest_lineage_verified_hypothesis(
            _narrative(target, independent_initial, add, "別施設の担当者が独自に観測した")
        )
        tied = learner.answer_from_lineage_graph(f"{target}の現在の結論を説明してください。")
        learner.ingest_lineage_verified_hypothesis(
            _narrative(target, independent_initial, add, "第三者の測定器で最初から再計測した")
        )
        before_reads = learner.hypothesis_reads
        resolved = learner.answer_from_lineage_graph(f"{target}の現在の結論を説明してください。")
        reads = learner.hypothesis_reads - before_reads
        learner.ingest_lineage_verified_hypothesis(
            _narrative(stable, stable_initial, add + 1, "別地域の独立した保存記録を確認した")
        )
        stable_result = learner.answer_from_lineage_graph(f"{stable}の結論を説明してください。")
        inference_seconds += time.perf_counter() - stamp

        lineage_reads = learner.lineage_feature_reads - before_features
        max_lineage_reads = max(max_lineage_reads, lineage_reads)
        max_hypothesis_reads = max(max_hypothesis_reads, reads)
        max_graph_bytes = max(max_graph_bytes, len(learner.lineage_graph_bytes()))
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        resolved_states = {(row[2], row[3]) for row in resolved.selected_states}
        stable_states = {(row[2], row[3]) for row in stable_result.selected_states}
        passed = (
            not tied.accepted
            and tied.mechanism == "abstain-unresolved-independent-lineage-conflict"
            and resolved.accepted
            and resolved.support == 2
            and resolved.competing_hypotheses == 2
            and (0, independent_initial) in resolved_states
            and (0, copied_initial) not in resolved_states
            and stable_result.accepted
            and stable_result.support == 1
            and (0, stable_initial) in stable_states
            and resolved.mechanism == "shared-bounded-verified-evidence-lineage-consensus-graph"
            and learner.lineage_reuses >= 1
            and learner.lineage_dependent_duplicates >= 1
            and len(learner._hypotheses[target]) == 2
            and max_graph_bytes <= 16384
            and reads <= 3
        )
        correct += int(passed)
        examples.append({
            "target": target,
            "copied_documents_collapsed": learner.lineage_dependent_duplicates >= 1,
            "tied_after_reposts": not tied.accepted,
            "resolved_supporting_lineages": resolved.support,
            "competing_hypotheses": resolved.competing_hypotheses,
            "selected_states": resolved.selected_states,
            "stable_target_preserved": stable_result.accepted,
            "hypothesis_reads": reads,
            "lineage_feature_reads": lineage_reads,
            "graph_bytes": len(learner.lineage_graph_bytes()),
            "passed": passed,
        })

    axis_name = "verified_evidence_lineage_independence"
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
        "shared_bounded_verified_evidence_lineage_consensus_graph": True,
        "hypothesis_targets": len(learner._hypotheses),
        "hypothesis_count": sum(len(rows) for rows in learner._hypotheses.values()),
        "hypothesis_reads": learner.hypothesis_reads,
        "hypothesis_writes": learner.hypothesis_writes,
        "hypothesis_support_updates": learner.hypothesis_support_updates,
        "lineages": len(learner._lineages),
        "lineage_feature_reads": learner.lineage_feature_reads,
        "lineage_comparisons": learner.lineage_comparisons,
        "lineage_reuses": learner.lineage_reuses,
        "lineage_creations": learner.lineage_creations,
        "lineage_dependent_duplicates": learner.lineage_dependent_duplicates,
        "lineage_conflicts": learner.lineage_conflicts,
        "lineage_evictions": learner.lineage_evictions,
        "lineage_graph_bytes": len(learner.lineage_graph_bytes()),
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
        combined_model_bytes <= 131072
        and peak_rss <= 536870912
        and wall_seconds <= 20.0
        and max_candidates <= 16
        and max_graph_bytes <= 16384
        and max_hypothesis_reads <= 3
        and max_lineage_reads <= 1024
    )
    report = {
        "stage": "SPARC-highschool-general-001-r21-shared-verified-evidence-lineage",
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
        "combined_model_and_lineage_graph_bytes": combined_model_bytes,
        "peak_rss_bytes": peak_rss,
        "training_seconds": training_seconds,
        "inference_seconds_total": inference_seconds,
        "mean_inference_seconds": inference_seconds / 20,
        "max_candidates": max_candidates,
        "max_feature_reads": max_feature_reads,
        "max_hypothesis_reads": max_hypothesis_reads,
        "max_lineage_feature_reads": max_lineage_reads,
        "max_lineage_graph_bytes": max_graph_bytes,
        "estimated_sparse_operations": estimated_ops,
        "wall_seconds": wall_seconds,
        "examples": examples,
        "structural_integration_passed": improved and efficient,
        "highschool_level_passed": False,
        "passed": improved and efficient,
        "claim_boundary": "The same verified world learner now clusters sparse non-world document context into bounded evidence lineages, prevents near-copy reposts from manufacturing independent support, invalidates internally conflicting lineages, and answers only from a unique majority of independent verified lineages. Evaluation remains controlled synthetic Japanese; real provenance, broad textbooks, qualitative claims, source trust, and natural free dialogue remain unproven.",
    }
    (output / "SPARC-highschool-general-evidence-lineage.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "SPARC-highschool-general-evidence-lineage.model.zlib").write_bytes(learner.to_bytes())
    (output / "SPARC-highschool-general-evidence-lineage.graph.json").write_bytes(learner.lineage_graph_bytes())
    if not report["passed"]:
        raise SystemExit("shared verified-evidence lineage integrated gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
