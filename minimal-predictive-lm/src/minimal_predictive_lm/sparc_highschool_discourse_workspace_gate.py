from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_discourse_workspace import DiscourseEvidenceWorkspaceLearner
from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_long_temporal_gate import _long_corpus
from .sparc_highschool_numeric_stream_gate import _numeric_corpus
from .sparc_highschool_question_grounding_gate import run_gate as run_previous_gate


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    previous = run_previous_gate(output / "previous-gate")
    started = time.perf_counter()
    learner = DiscourseEvidenceWorkspaceLearner()
    training_started = time.perf_counter()
    learner.learn_independent_documents(_corpus(), min_support=4)
    learner.learn_independent_numeric_documents(_numeric_corpus())
    learner.learn_long_chronological_documents(_long_corpus())
    training_seconds = time.perf_counter() - training_started

    correct = 0
    inference_seconds = 0.0
    max_candidates = 0
    max_feature_reads = 0
    max_evidence_reads = 0
    examples = []
    for index in range(20):
        learner.reset_discourse()
        first = f"談話対象{index}"
        second = f"比較対象{index}"
        first_initial = 7 + index
        first_add = 2 + index % 4
        first_observed = first_initial + first_add
        second_initial = 4 + index
        second_observed = second_initial * 3
        body = (
            f"{first}に{first_add}個加える。資料の順序を確認した。{first}には{first_observed}個ある。{first}を2倍にする。"
            f"{second}を3倍にする。{second}には{second_observed}個ある。{second}に2個加える。"
        )

        stamp = time.perf_counter()
        opening = learner.answer_discourse_grounded_world(
            body + f"まず{first}について不足する状態を根拠付きで説明してください。"
        )
        before_reads = learner.discourse_evidence_reads
        follow = learner.answer_discourse_grounded_world(
            body + "続けて、この計算が観測と一致する理由を説明してください。"
        )
        reads = learner.discourse_evidence_reads - before_reads
        switched = learner.answer_discourse_grounded_world(
            body + f"次は{second}について同じ方法で説明してください。"
        )
        switch_follow = learner.answer_discourse_grounded_world(
            body + "その結果も同じ世界遷移で確かめてください。"
        )
        inference_seconds += time.perf_counter() - stamp
        max_evidence_reads = max(max_evidence_reads, reads)
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)

        selected = {(subject, node, value) for subject, _relation, node, value in follow.selected_states}
        passed = (
            opening.accepted
            and opening.targets == (first,)
            and follow.accepted
            and follow.targets == (first,)
            and follow.focus_reused
            and (first, 0, first_initial) in selected
            and f"{second}の" not in follow.answer
            and switched.accepted
            and switched.targets == (second,)
            and switch_follow.accepted
            and switch_follow.targets == (second,)
            and switch_follow.focus_reused
            and follow.mechanism == "shared-bounded-discourse-evidence-workspace"
            and reads <= 4
        )
        correct += int(passed)
        examples.append({
            "opening_target": opening.targets,
            "follow_target": follow.targets,
            "switch_target": switched.targets,
            "switch_follow_target": switch_follow.targets,
            "follow_focus_reused": follow.focus_reused,
            "switch_follow_focus_reused": switch_follow.focus_reused,
            "evidence_reads": reads,
            "passed": passed,
        })

    axis_name = "bounded_discourse_evidence_workspace"
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
        + learner.discourse_evidence_reads
        + learner.question_entity_reads
        + learner.question_selected_states
        + learner.latent_constraint_reads
        + learner.latent_forward_checks
        + learner.latent_state_nodes_recovered
    )
    no_regression = all(
        axes[name]["correct"] >= row["correct"] and axes[name]["total"] == row["total"]
        for name, row in previous["axes"].items()
    )
    improved = total_correct / total > baseline_correct / baseline_total and percentages[axis_name] > 0 and no_regression
    efficient = (
        model["serialized_bytes"] <= 131072
        and peak_rss <= 536870912
        and wall_seconds <= 20.0
        and max_candidates <= 16
        and max_evidence_reads <= 4
    )
    report = {
        "stage": "SPARC-highschool-general-001-r18-shared-discourse-evidence-workspace",
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
        "max_discourse_evidence_reads": max_evidence_reads,
        "estimated_sparse_operations": estimated_ops,
        "wall_seconds": wall_seconds,
        "examples": examples,
        "structural_integration_passed": improved and efficient,
        "highschool_level_passed": False,
        "passed": improved and efficient,
        "claim_boundary": "The same verified world model now carries one bounded evidence focus across dialogue turns, supports explicit focus switching, and clears stale focus on ambiguity. Evaluation remains controlled synthetic Japanese; real textbooks and natural long dialogue remain unproven.",
    }
    (output / "SPARC-highschool-general-discourse-workspace.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "SPARC-highschool-general-discourse-workspace.model.zlib").write_bytes(learner.to_bytes())
    if not report["passed"]:
        raise SystemExit("shared discourse-workspace integrated gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
