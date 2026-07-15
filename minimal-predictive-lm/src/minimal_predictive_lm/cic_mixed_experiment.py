from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

from .cic_mixed_train import train_mixed


def run_mixed_experiment(
    mawps_path: str | Path,
    commonsense_path: str | Path,
    output: str | Path | None = None,
) -> dict[str, object]:
    start = time.perf_counter()
    row = train_mixed(mawps_path, commonsense_path)
    artifact_bytes = len(row.artifact.to_bytes())
    math_accuracy = row.math_correct / row.math_total if row.math_total else 0.0
    choice_accuracy = (
        row.choice_correct / row.choice_test_rows if row.choice_test_rows else 0.0
    )
    legacy_accuracy = (
        row.legacy_correct / row.choice_test_rows if row.choice_test_rows else 0.0
    )
    majority_accuracy = (
        row.majority_correct / row.choice_test_rows if row.choice_test_rows else 0.0
    )
    result: dict[str, object] = {
        "capability_id": "CIC-004-MARGIN",
        "neural_network_used": False,
        "gradient_training_used": False,
        "task_id_input_used": False,
        "same_artifact_for_both_capabilities": True,
        "arithmetic": {
            "correct": row.math_correct,
            "total": row.math_total,
            "accuracy": math_accuracy,
            "mechanisms": row.math_mechanisms,
            "mean_checked_mechanisms": row.math_work,
            "selected_epochs": row.math_epochs,
            "inner_validation_accuracy_by_epoch": row.math_validation,
        },
        "commonsense_choice": {
            "public_rows": row.choice_rows,
            "train_rows": row.choice_train_rows,
            "untouched_test_rows": row.choice_test_rows,
            "correct": row.choice_correct,
            "accuracy": choice_accuracy,
            "cic_003_baseline_correct": row.legacy_correct,
            "cic_003_baseline_accuracy": legacy_accuracy,
            "absolute_gain_over_cic_003": choice_accuracy - legacy_accuracy,
            "majority_baseline_accuracy": majority_accuracy,
            "mean_checked_options": row.choice_work,
            "selected_epochs": row.choice_epochs,
            "inner_validation_accuracy_by_epoch": row.choice_validation,
            "baseline_selected_epochs": row.legacy_epochs,
            "baseline_inner_validation_accuracy_by_epoch": row.legacy_validation,
            "test_used_for_selection": False,
            "learner": "averaged_passive_aggressive_relational_ranker",
        },
        "artifact": {
            "bytes": artifact_bytes,
            "choice_nonzero_weights": row.choice_nonzero_weights,
            "format": "cic-mixed-002",
        },
        "resources": {
            "arithmetic_synthesis_expansions": row.math_expansions,
            "elapsed_seconds": time.perf_counter() - start,
            "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "claim_boundary": (
            "This tests whether a margin-trained task-ID-free relational memory "
            "improves the same untouched Japanese commonsense holdout while "
            "retaining arithmetic. It is not free-form general dialogue and not "
            "Japanese high-school-level intelligence."
        ),
    }
    result["passed"] = bool(
        math_accuracy >= 0.58
        and choice_accuracy >= legacy_accuracy
        and choice_accuracy >= majority_accuracy + 0.03
        and artifact_bytes <= 250_000
        and row.math_mechanisms <= 100
    )
    if output is not None:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        row.artifact.save(path.with_suffix(".mixed.cic"))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CIC mixed-capability experiment")
    parser.add_argument("mawps")
    parser.add_argument("commonsense")
    parser.add_argument("--output", default="results/cic_004_margin.json")
    args = parser.parse_args()
    print(
        json.dumps(
            run_mixed_experiment(args.mawps, args.commonsense, args.output),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
