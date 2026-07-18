from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_discourse_workspace_gate import run_gate as run_previous_gate
from .sparc_highschool_document_stream_gate import _corpus
from .sparc_highschool_evidence_revision import EvidenceRevisionWorkspaceLearner
from .sparc_highschool_long_temporal_gate import _long_corpus
from .sparc_highschool_numeric_stream_gate import _numeric_corpus


def _narrative(target: str, initial: int, add: int) -> str:
    observed = initial + add
    return (
        f"{target}に{add}個加える。資料の順序を確認した。{target}には{observed}個ある。"
        f"{target}を2倍にする。{target}について不足する状態を根拠付きで説明してください。"
    )


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    previous = run_previous_gate(output / "previous-gate")
    started = time.perf_counter()
    learner = EvidenceRevisionWorkspaceLearner(max_evidence_components=4)
    training_started = time.perf_counter()
    learner.learn_independent_documents(_corpus(), min_support=4)
    learner.learn_independent_numeric_documents(_numeric_corpus())
    learner.learn_long_chronological_documents(_long_corpus())
    training_seconds = time.perf_counter() - training_started

    correct = 0
    inference_seconds = 0.0
    max_candidates = 0
    max_feature_reads = 0
    max_ledger_bytes = 0
    max_component_reads = 0
    examples = []
    for index in range(20):
        learner.reset_evidence_ledger()
        first = f"継続論点{index}A"
        second = f"継続論点{index}B"
        first_initial = 7 + index
        second_initial = 4 + index
        add = 2 + index % 4
        stamp = time.perf_counter()
        initial_first = learner.ingest_verified_evidence(_narrative(first, first_initial, add))
        initial_second = learner.ingest_verified_evidence(_narrative(second, second_initial, add + 1))
        before_reads = learner.evidence_component_reads
        recalled_first = learner.answer_from_evidence_ledger(f"{first}の根拠を説明してください。")
        revised_first = learner.ingest_verified_evidence(_narrative(first, first_initial + 5, add))
        updated_first = learner.answer_from_evidence_ledger(f"{first}の現在の結論を説明してください。")
        unchanged_second = learner.answer_from_evidence_ledger(f"{second}の現在の結論を説明してください。")
        inference_seconds += time.perf_counter() - stamp
        reads = learner.evidence_component_reads - before_reads
        max_component_reads = max(max_component_reads, reads)
        max_ledger_bytes = max(max_ledger_bytes, len(learner.evidence_ledger_bytes()))
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)

        first_before = {(row[2], row[3]) for row in recalled_first.selected_states}
        first_after = {(row[2], row[3]) for row in updated_first.selected_states}
        second_after = {(row[2], row[3]) for row in unchanged_second.selected_states}
        passed = (
            initial_first.accepted
            and initial_second.accepted
            and recalled_first.accepted
            and (0, first_initial) in first_before
            and revised_first.accepted
            and revised_first.revised
            and revised_first.version == 2
            and updated_first.accepted
            and (0, first_initial + 5) in first_after
            and (0, first_initial) not in first_after
            and unchanged_second.accepted
            and (0, second_initial) in second_after
            and updated_first.mechanism == "shared-bounded-verified-evidence-revision-ledger"
            and len(learner._evidence_ledger) == 2
            and max_ledger_bytes <= 4096
        )
        correct += int(passed)
        examples.append({
            "first": first,
            "second": second,
            "revision_version": revised_first.version,
            "component_reads": reads,
            "ledger_bytes": len(learner.evidence_ledger_bytes()),
            "passed": passed,
        })

    axis_name = "bounded_verified_evidence_revision"
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
        + learner.evidence_component_reads
        + learner.evidence_component_writes
        + learner.evidence_revisions
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
        and max_ledger_bytes <= 4096
        and max_component_reads <= 8
    )
    report = {
        "stage": "SPARC-highschool-general-001-r19-shared-evidence-revision-ledger",
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
        "max_evidence_component_reads": max_component_reads,
        "max_evidence_ledger_bytes": max_ledger_bytes,
        "estimated_sparse_operations": estimated_ops,
        "wall_seconds": wall_seconds,
        "examples": examples,
        "structural_integration_passed": improved and efficient,
        "highschool_level_passed": False,
        "passed": improved and efficient,
        "claim_boundary": "The same verified world learner now keeps multiple bounded evidence components and replaces one component only after a newly verified world supports the revision. Evaluation remains controlled synthetic Japanese; real textbooks, broad knowledge transfer, and natural free dialogue remain unproven.",
    }
    (output / "SPARC-highschool-general-evidence-revision.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "SPARC-highschool-general-evidence-revision.model.zlib").write_bytes(learner.to_bytes())
    (output / "SPARC-highschool-general-evidence-revision.ledger.json").write_bytes(learner.evidence_ledger_bytes())
    if not report["passed"]:
        raise SystemExit("shared evidence-revision integrated gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
