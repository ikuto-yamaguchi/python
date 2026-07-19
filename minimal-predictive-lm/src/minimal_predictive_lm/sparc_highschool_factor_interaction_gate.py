from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_evidence_factor_interaction import (
    EvidenceFactorInteractionConsensusLearner,
)
from .sparc_highschool_evidence_factor_reliability import (
    EvidenceFactorReliabilityConsensusLearner,
)
from .sparc_highschool_evidence_factor_reliability_gate import _strong, _weak
from .sparc_highschool_evidence_revision import EvidenceRevisionWorkspaceLearner
from .sparc_highschool_factor_conflict_gate import run_gate as run_previous_gate
from .sparc_highschool_long_temporal_gate import _long_corpus
from .sparc_highschool_numeric_stream_gate import _numeric_corpus


def _note(method: str, environment: str, index: int, round_index: int) -> str:
    return (
        f"{method}方式の{method}回路と{method}経路を使用した。"
        f"独立背景記録{index}-{round_index}を参照した。"
        f"{environment}環境の{environment}室と{environment}条件で測定した"
    )


def _base_kwargs() -> dict[str, object]:
    return {
        "max_evidence_components": 10,
        "max_hypotheses_per_target": 3,
        "max_lineages": 16,
        "lineage_similarity_threshold": 0.50,
        "max_quality_weight": 3,
        "max_reliability_score": 4,
        "max_factor_score": 4,
        "max_factor_entries": 2048,
    }


def _prepare(learner: EvidenceFactorReliabilityConsensusLearner) -> None:
    learner.learn_independent_documents(_corpus(), min_support=4)
    learner.learn_independent_numeric_documents(_numeric_corpus())
    learner.learn_long_chronological_documents(_long_corpus())


def _ingest(
    learner: EvidenceFactorReliabilityConsensusLearner,
    text: str,
) -> None:
    if isinstance(learner, EvidenceFactorInteractionConsensusLearner):
        learner.ingest_interaction_verified_hypothesis(text)
    else:
        learner.ingest_factor_verified_hypothesis(text)


def _consolidate(
    learner: EvidenceFactorReliabilityConsensusLearner,
    target: str,
) -> bool:
    if isinstance(learner, EvidenceFactorInteractionConsensusLearner):
        return learner.consolidate_verified_target_interactions(target)
    return learner.consolidate_verified_target_factors(target)


def _reset(learner: EvidenceFactorReliabilityConsensusLearner) -> None:
    if isinstance(learner, EvidenceFactorInteractionConsensusLearner):
        learner.reset_factor_interaction_graph()
    else:
        learner.reset_factor_reliability_graph()


def _calibrate(
    learner: EvidenceFactorReliabilityConsensusLearner,
    index: int,
) -> bool:
    patterns = (
        ("青", "甲", "青", "乙"),
        ("赤", "乙", "赤", "甲"),
        ("青", "甲", "青", "乙"),
        ("赤", "乙", "赤", "甲"),
    )
    ok = True
    for round_index, (good_method, good_env, bad_method, bad_env) in enumerate(patterns):
        target = f"条件相互作用校正論点{index}-{round_index}"
        truth = 17 + index + round_index
        add = 2 + round_index % 2
        _ingest(
            learner,
            _strong(
                target,
                truth + 8,
                add,
                _note(bad_method, bad_env, index, round_index),
            ),
        )
        _ingest(
            learner,
            _strong(
                target,
                truth,
                add,
                _note(good_method, good_env, index, round_index),
            ),
        )
        _ingest(
            learner,
            _weak(
                target,
                truth,
                add,
                f"第三者再測定班{index}-{round_index}による独立確認",
            ),
        )
        ok = _consolidate(learner, target) and ok
    return ok


def _novel_case(
    learner: EvidenceFactorReliabilityConsensusLearner,
    index: int,
):
    target = f"未知条件相互作用論点{index}"
    truth = 31 + index
    wrong = truth + 8
    add = 3 + index % 2
    _ingest(
        learner,
        _weak(target, truth, add, _note("青", "甲", index, 90)),
    )
    _ingest(
        learner,
        _strong(target, wrong, add, _note("青", "乙", index, 91)),
    )
    answer = learner.answer_from_factor_reliability_graph(
        f"{target}の現在の結論を説明してください。"
    )
    selected = {(row[2], row[3]) for row in answer.selected_states}
    correct = answer.accepted and (0, truth) in selected and (0, wrong) not in selected
    return target, truth, wrong, answer, selected, correct


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    previous = run_previous_gate(output / "previous-gate")
    started = time.perf_counter()

    baseline = EvidenceFactorReliabilityConsensusLearner(**_base_kwargs())
    learner = EvidenceFactorInteractionConsensusLearner(
        **_base_kwargs(),
        max_interaction_score=4,
        max_interaction_entries=4096,
        max_interaction_features=64,
        max_pairs_per_lineage=512,
    )
    training_started = time.perf_counter()
    _prepare(baseline)
    _prepare(learner)
    training_seconds = time.perf_counter() - training_started

    baseline_correct = 0
    correct = 0
    inference_seconds = 0.0
    max_candidates = max_feature_reads = max_hypothesis_reads = 0
    max_quality_reads = max_factor_reads = max_interaction_reads = 0
    max_graph_bytes = 0
    examples: list[dict[str, object]] = []

    for index in range(20):
        _reset(baseline)
        _reset(learner)
        baseline_calibration = _calibrate(baseline, index)
        calibration = _calibrate(learner, index)

        _, _, _, baseline_answer, baseline_selected, baseline_passed = _novel_case(
            baseline,
            index,
        )
        before_h = learner.hypothesis_reads
        before_q = learner.quality_reads
        before_f = learner.factor_reads
        before_i = learner.interaction_reads
        stamp = time.perf_counter()
        target, truth, wrong, answer, selected, resolved = _novel_case(learner, index)
        inference_seconds += time.perf_counter() - stamp
        h_reads = learner.hypothesis_reads - before_h
        q_reads = learner.quality_reads - before_q
        f_reads = learner.factor_reads - before_f
        i_reads = learner.interaction_reads - before_i
        graph_bytes = len(learner.factor_interaction_graph_bytes())

        baseline_correct += int(baseline_calibration and baseline_passed)
        passed = (
            calibration
            and learner.interaction_consolidations == 4
            and resolved
            and answer.mechanism
            == "shared-bounded-verified-source-factor-reliability-graph"
            and len(learner._factor_interactions) > 0
            and graph_bytes <= 262144
            and h_reads <= 3
            and q_reads <= 10
            and f_reads <= 2048
            and i_reads <= 4096
        )
        correct += int(passed)
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        max_hypothesis_reads = max(max_hypothesis_reads, h_reads)
        max_quality_reads = max(max_quality_reads, q_reads)
        max_factor_reads = max(max_factor_reads, f_reads)
        max_interaction_reads = max(max_interaction_reads, i_reads)
        max_graph_bytes = max(max_graph_bytes, graph_bytes)
        examples.append(
            {
                "target": target,
                "truth": truth,
                "wrong": wrong,
                "baseline_accepted": baseline_answer.accepted,
                "baseline_mechanism": baseline_answer.mechanism,
                "baseline_selected_states": list(baseline_selected),
                "interaction_accepted": answer.accepted,
                "interaction_selected_states": list(selected),
                "interaction_entries": len(learner._factor_interactions),
                "interaction_reads": i_reads,
                "graph_bytes": graph_bytes,
                "passed": passed,
            }
        )

    axis_name = "conditional_verified_source_factor_pair_transfer"
    axes = dict(previous["axes"])
    axes[axis_name] = {"correct": correct, "total": 20}
    baseline_axes = dict(previous["axes"])
    baseline_axes[axis_name] = {"correct": baseline_correct, "total": 20}
    total_correct = sum(row["correct"] for row in axes.values())
    total = sum(row["total"] for row in axes.values())
    expanded_baseline_correct = int(previous["total_correct"]) + baseline_correct
    expanded_baseline_total = int(previous["total"]) + 20
    percentages = {name: row["correct"] / row["total"] for name, row in axes.items()}
    minimum_axis = min(percentages, key=percentages.get)

    model = EvidenceRevisionWorkspaceLearner.report(learner)
    model.update(
        {
            "shared_bounded_conditional_factor_pair_consensus": True,
            "factor_entries": len(learner._factor_reliability),
            "interaction_entries": len(learner._factor_interactions),
            "interaction_reads": learner.interaction_reads,
            "interaction_writes": learner.interaction_writes,
            "interaction_consolidations": learner.interaction_consolidations,
            "task_name_supplied": False,
            "domain_name_supplied": False,
        }
    )
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    wall_seconds = time.perf_counter() - started
    combined_model_bytes = int(model["serialized_bytes"]) + max_graph_bytes
    estimated_ops = (
        int(previous["estimated_sparse_operations"])
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
        + learner.factor_reads
        + learner.factor_writes
        + learner.factor_consolidations
        + learner.interaction_reads
        + learner.interaction_writes
        + learner.interaction_consolidations
        + learner.latent_constraint_reads
        + learner.latent_forward_checks
        + learner.latent_state_nodes_recovered
    )
    no_regression = all(
        axes[name]["correct"] >= row["correct"] and axes[name]["total"] == row["total"]
        for name, row in previous["axes"].items()
    )
    improved = (
        total_correct / total > expanded_baseline_correct / expanded_baseline_total
        and correct > baseline_correct
        and no_regression
    )
    efficient = (
        combined_model_bytes <= 524288
        and peak_rss <= 536870912
        and wall_seconds <= 45.0
        and max_candidates <= 16
        and max_graph_bytes <= 262144
        and max_hypothesis_reads <= 3
        and max_quality_reads <= 10
        and max_factor_reads <= 2048
        and max_interaction_reads <= 4096
    )
    report = {
        "stage": "SPARC-highschool-general-001-r27-factor-interaction",
        "baseline": {
            "axes": baseline_axes,
            "total_correct": expanded_baseline_correct,
            "total": expanded_baseline_total,
            "overall_accuracy": expanded_baseline_correct / expanded_baseline_total,
            "new_axis_correct": baseline_correct,
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
        "combined_model_and_interaction_graph_bytes": combined_model_bytes,
        "peak_rss_bytes": peak_rss,
        "training_seconds": training_seconds,
        "inference_seconds_total": inference_seconds,
        "mean_inference_seconds": inference_seconds / 20,
        "max_candidates": max_candidates,
        "max_feature_reads": max_feature_reads,
        "max_hypothesis_reads": max_hypothesis_reads,
        "max_quality_reads": max_quality_reads,
        "max_factor_reads": max_factor_reads,
        "max_interaction_reads": max_interaction_reads,
        "max_interaction_graph_bytes": max_graph_bytes,
        "estimated_sparse_operations": estimated_ops,
        "wall_seconds": wall_seconds,
        "examples": examples,
        "structural_integration_passed": improved and efficient,
        "highschool_level_passed": False,
        "passed": improved and efficient,
        "claim_boundary": "The same verified latent-world model now learns bounded pairwise context for source factors and can transfer an XOR-like reliability relation that marginal factor scores cannot represent. The material remains controlled synthetic Japanese; autonomous semantic concept formation, real textbooks, unrestricted reasoning and natural free dialogue remain unproven.",
    }
    (output / "SPARC-highschool-general-factor-interaction.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output / "SPARC-highschool-general-factor-interaction.model.zlib").write_bytes(
        learner.to_bytes()
    )
    (output / "SPARC-highschool-general-factor-interaction.graph.json").write_bytes(
        learner.factor_interaction_graph_bytes()
    )
    if not report["passed"]:
        raise SystemExit("conditional source-factor interaction integrated gate failed")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
