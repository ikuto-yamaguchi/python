from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_evidence_factor_interaction import EvidenceFactorInteractionConsensusLearner
from .sparc_highschool_evidence_factor_reliability_gate import _strong, _weak
from .sparc_highschool_evidence_revision import EvidenceRevisionWorkspaceLearner
from .sparc_highschool_factor_interaction_gate import run_gate as run_previous_gate
from .sparc_highschool_interaction_support import EvidenceFactorInteractionSupportLearner
from .sparc_highschool_long_temporal_gate import _long_corpus
from .sparc_highschool_numeric_stream_gate import _numeric_corpus


def _kwargs():
    return dict(
        max_evidence_components=10,
        max_hypotheses_per_target=3,
        max_lineages=16,
        lineage_similarity_threshold=0.50,
        max_quality_weight=3,
        max_reliability_score=4,
        max_factor_score=4,
        max_factor_entries=2048,
        max_interaction_score=4,
        max_interaction_entries=4096,
        max_interaction_features=64,
        max_pairs_per_lineage=512,
    )


def _prepare(learner):
    learner.learn_independent_documents(_corpus(), min_support=4)
    learner.learn_independent_numeric_documents(_numeric_corpus())
    learner.learn_long_chronological_documents(_long_corpus())


def _note(index):
    token = chr(ord("ぁ") + index)
    return f"{token}方式{token}回路{token}環境{token}条件{token}記録"


def _resolve_once(learner, index):
    target = f"単発相互作用校正論点{index}"
    truth = 20 + index
    wrong = truth + 8
    note = _note(index)
    learner.ingest_interaction_verified_hypothesis(_strong(target, wrong, 3, note))
    learner.ingest_interaction_verified_hypothesis(_strong(target, truth, 3, note))
    learner.ingest_interaction_verified_hypothesis(_weak(target, truth, 3, f"独立再測定班{index}"))
    ok = learner.consolidate_verified_target_interactions(target)
    lineages = [
        lineage_id
        for lineage_id in learner._lineages
        if learner._interaction_pairs(lineage_id)
    ]
    if not lineages:
        return ok, 0, False, 0
    best = max(lineages, key=lambda lineage_id: len(learner._interaction_pairs(lineage_id)))
    adjustment, conflict, active = learner._interaction_signal(best)
    return ok, adjustment, conflict, active


def run_gate(output_dir: str | Path):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    previous = run_previous_gate(output / "previous-gate")
    started = time.perf_counter()
    baseline = EvidenceFactorInteractionConsensusLearner(**_kwargs())
    learner = EvidenceFactorInteractionSupportLearner(
        **_kwargs(), min_interaction_targets=2, max_interaction_support=15
    )
    train_started = time.perf_counter()
    _prepare(baseline)
    _prepare(learner)
    training_seconds = time.perf_counter() - train_started

    baseline_correct = 0
    correct = 0
    inference_seconds = 0.0
    examples = []
    max_graph_bytes = 0
    max_candidates = max_feature_reads = max_support_reads = 0
    for index in range(20):
        baseline.reset_factor_interaction_graph()
        learner.reset_factor_interaction_graph()
        baseline_ok, baseline_adjustment, baseline_conflict, baseline_active = _resolve_once(baseline, index)
        before = learner.interaction_support_reads
        stamp = time.perf_counter()
        ok, adjustment, conflict, active = _resolve_once(learner, index)
        inference_seconds += time.perf_counter() - stamp
        support_reads = learner.interaction_support_reads - before
        graph_bytes = len(learner.factor_interaction_support_graph_bytes())
        baseline_passed = baseline_ok and baseline_active == 0
        passed = (
            ok
            and adjustment == 0
            and not conflict
            and active == 0
            and learner.low_support_interactions_ignored > 0
            and learner.interaction_consolidations == 1
            and all(value == 1 for value in learner._interaction_support.values())
            and graph_bytes <= 262144
            and support_reads <= 4096
        )
        baseline_correct += int(baseline_passed)
        correct += int(passed)
        max_graph_bytes = max(max_graph_bytes, graph_bytes)
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        max_support_reads = max(max_support_reads, support_reads)
        examples.append({
            "index": index,
            "baseline_adjustment": baseline_adjustment,
            "baseline_conflict": baseline_conflict,
            "baseline_active_interactions": baseline_active,
            "supported_adjustment": adjustment,
            "supported_conflict": conflict,
            "supported_active_interactions": active,
            "low_support_ignored": learner.low_support_interactions_ignored,
            "graph_bytes": graph_bytes,
            "passed": passed,
        })

    axis = "single_episode_spurious_interaction_resistance"
    axes = dict(previous["axes"])
    axes[axis] = {"correct": correct, "total": 20}
    baseline_axes = dict(previous["axes"])
    baseline_axes[axis] = {"correct": baseline_correct, "total": 20}
    total_correct = sum(row["correct"] for row in axes.values())
    total = sum(row["total"] for row in axes.values())
    baseline_total_correct = int(previous["total_correct"]) + baseline_correct
    baseline_total = int(previous["total"]) + 20
    percentages = {name: row["correct"] / row["total"] for name, row in axes.items()}
    minimum_axis = min(percentages, key=percentages.get)
    model = EvidenceRevisionWorkspaceLearner.report(learner)
    model.update({
        "repeated_verified_interaction_support": True,
        "interaction_entries": len(learner._factor_interactions),
        "interaction_support_entries": len(learner._interaction_support),
        "interaction_support_reads": learner.interaction_support_reads,
        "interaction_support_writes": learner.interaction_support_writes,
        "low_support_interactions_ignored": learner.low_support_interactions_ignored,
        "task_name_supplied": False,
        "domain_name_supplied": False,
    })
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    wall_seconds = time.perf_counter() - started
    combined_bytes = int(model["serialized_bytes"]) + max_graph_bytes
    no_regression = all(
        axes[name]["correct"] >= row["correct"] and axes[name]["total"] == row["total"]
        for name, row in previous["axes"].items()
    )
    improved = (
        total_correct / total > baseline_total_correct / baseline_total
        and correct > baseline_correct
        and no_regression
    )
    estimated_ops = (
        int(previous["estimated_sparse_operations"])
        + learner.interaction_reads + learner.interaction_writes
        + learner.interaction_support_reads + learner.interaction_support_writes
        + learner.factor_reads + learner.factor_writes
        + learner.hypothesis_reads + learner.hypothesis_writes
        + max_feature_reads * 20
    )
    efficient = (
        combined_bytes <= 524288 and peak_rss <= 536870912 and wall_seconds <= 45.0
        and max_candidates <= 16 and max_graph_bytes <= 262144
        and max_support_reads <= 4096
    )
    report = {
        "stage": "SPARC-highschool-general-001-r28-interaction-support",
        "baseline": {
            "axes": baseline_axes,
            "total_correct": baseline_total_correct,
            "total": baseline_total,
            "overall_accuracy": baseline_total_correct / baseline_total,
            "new_axis_correct": baseline_correct,
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
        "combined_model_and_graph_bytes": combined_bytes,
        "peak_rss_bytes": peak_rss,
        "training_seconds": training_seconds,
        "inference_seconds_total": inference_seconds,
        "mean_inference_seconds": inference_seconds / 20,
        "max_candidates": max_candidates,
        "max_feature_reads": max_feature_reads,
        "max_interaction_support_reads": max_support_reads,
        "estimated_sparse_operations": estimated_ops,
        "wall_seconds": wall_seconds,
        "examples": examples,
    }
    report["passed"] = bool(improved and efficient and correct > baseline_correct)
    path = output / "SPARC-highschool-general-interaction-support.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    report = run_gate(args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
