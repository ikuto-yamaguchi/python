from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_latent_state_graph_gate import run_gate as run_previous_gate
from .sparc_highschool_long_temporal_gate import _long_corpus
from .sparc_highschool_numeric_stream_gate import _numeric_corpus
from .sparc_highschool_question_grounding import QuestionGroundedWorldLearner


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    previous = run_previous_gate(output / "previous-gate")
    started = time.perf_counter()
    learner = QuestionGroundedWorldLearner()
    training_started = time.perf_counter()
    learner.learn_independent_documents(_corpus(), min_support=4)
    learner.learn_independent_numeric_documents(_numeric_corpus())
    learner.learn_long_chronological_documents(_long_corpus())
    training_seconds = time.perf_counter() - training_started

    correct = 0
    inference_seconds = 0.0
    max_candidates = 0
    max_feature_reads = 0
    max_entity_reads = 0
    examples = []
    for index in range(20):
        asked = f"質問対象{index}"
        distractor = f"別対象{index}"
        asked_initial = 8 + index
        asked_add = 2 + index % 3
        asked_middle = asked_initial + asked_add
        distractor_initial = 5 + index
        distractor_middle = distractor_initial * 3
        text = (
            f"{asked}に{asked_add}個加える。補足資料も確認した。{asked}には{asked_middle}個ある。{asked}を2倍にする。"
            f"{distractor}を3倍にする。{distractor}には{distractor_middle}個ある。{distractor}に2個加える。"
            f"以上を踏まえ、{asked}について本文から不足する状態だけを根拠付きで説明してください。"
        )
        before_reads = learner.question_entity_reads
        stamp = time.perf_counter()
        result = learner.answer_question_grounded_world(text)
        inference_seconds += time.perf_counter() - stamp
        reads = learner.question_entity_reads - before_reads
        max_entity_reads = max(max_entity_reads, reads)
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        selected = {(subject, node, value) for subject, _relation, node, value in result.selected_states}
        passed = (
            result.accepted
            and result.targets == (asked,)
            and (asked, 0, asked_initial) in selected
            and all(subject == asked for subject, _node, _value in selected)
            and result.mechanism == "shared-question-grounded-world-graph"
            and "検算" in result.answer
            and distractor not in result.answer
            and reads <= 4
        )
        correct += int(passed)
        examples.append({"text": text, "targets": result.targets, "selected_states": result.selected_states, "entity_reads": reads, "passed": passed})

    axis_name = "question_grounded_world_selection"
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
    estimated_ops = previous["estimated_sparse_operations"] + max_feature_reads * 20 + learner.question_entity_reads + learner.question_selected_states
    no_regression = all(axes[name]["correct"] >= row["correct"] and axes[name]["total"] == row["total"] for name, row in previous["axes"].items())
    improved = total_correct / total > baseline_correct / baseline_total and percentages[axis_name] > 0 and no_regression
    efficient = model["serialized_bytes"] <= 131072 and peak_rss <= 536870912 and wall_seconds <= 20.0 and max_candidates <= 16 and max_entity_reads <= 4
    report = {
        "stage": "SPARC-highschool-general-001-r17-shared-question-grounding",
        "baseline": {"axes": baseline_axes, "total_correct": baseline_correct, "total": baseline_total, "overall_accuracy": baseline_correct / baseline_total, "minimum_axis": axis_name, "minimum_axis_accuracy": 0.0, "model_bytes": previous["model"]["serialized_bytes"]},
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
        "max_question_entity_reads": max_entity_reads,
        "estimated_sparse_operations": estimated_ops,
        "wall_seconds": wall_seconds,
        "examples": examples,
        "structural_integration_passed": improved and efficient,
        "highschool_level_passed": False,
        "passed": improved and efficient,
        "claim_boundary": "The shared learner now grounds an unlabeled Japanese question to exactly one evidence-supported world component and returns only verified latent states. Evaluation remains controlled synthetic Japanese; real textbooks and natural open dialogue remain unproven.",
    }
    (output / "SPARC-highschool-general-question-grounding.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "SPARC-highschool-general-question-grounding.model.zlib").write_bytes(learner.to_bytes())
    if not report["passed"]:
        raise SystemExit("shared question-grounding integrated gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
