from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

from .cic_mixed_train import train_mixed


def run_mixed_experiment(
    mawps_path: str | Path,
    commonsense_train_path: str | Path,
    commonsense_test_path: str | Path | None = None,
    output: str | Path | None = None,
) -> dict[str, object]:
    start = time.perf_counter()
    row = train_mixed(
        mawps_path,
        commonsense_train_path,
        commonsense_test_path,
    )
    artifact_bytes = len(row.artifact.to_bytes())
    math_accuracy = row.math_correct / row.math_total if row.math_total else 0.0
    selected_accuracy = (
        row.choice_correct / row.choice_test_rows if row.choice_test_rows else 0.0
    )
    baseline_accuracy = (
        row.cic_005_correct / row.choice_test_rows if row.choice_test_rows else 0.0
    )
    majority_accuracy = (
        row.majority_correct / row.choice_test_rows if row.choice_test_rows else 0.0
    )
    result: dict[str, object] = {
        "capability_id": "CIC-006-DUALHASH",
        "neural_network_used": False,
        "gradient_training_used": False,
        "task_id_input_used": False,
        "same_artifact_for_both_capabilities": True,
        "official_train_to_validation_transfer": commonsense_test_path is not None,
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
            "official_train_rows": row.choice_train_rows,
            "untouched_validation_rows": row.choice_test_rows,
            "selected_config_name": row.selected_config_name,
            "selected_config": row.selected_config,
            "candidate_configs": row.candidate_configs,
            "inner_dual_hash_validation": row.inner_dual_hash_validation,
            "selected_correct": row.choice_correct,
            "selected_accuracy": selected_accuracy,
            "cic_005_baseline_correct": row.cic_005_correct,
            "cic_005_baseline_accuracy": baseline_accuracy,
            "absolute_gain_over_cic_005": selected_accuracy - baseline_accuracy,
            "majority_baseline_accuracy": majority_accuracy,
            "mean_checked_options": row.choice_work,
            "test_used_for_selection": False,
        },
        "artifact": {
            "bytes": artifact_bytes,
            "choice_nonzero_weights": row.choice_nonzero_weights,
            "hash_replicas": int(row.selected_config["hash_replicas"]),
            "format": "cic-mixed-002",
        },
        "resources": {
            "arithmetic_synthesis_expansions": row.math_expansions,
            "elapsed_seconds": time.perf_counter() - start,
            "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "claim_boundary": (
            "CIC-006 selects single- versus dual-hash sparse mechanisms using "
            "only an inner split of the official JGLUE training data, then "
            "compares once against frozen CIC-005 on untouched validation. It "
            "is not free-form dialogue or Japanese high-school-level intelligence."
        ),
    }
    result["passed"] = bool(
        math_accuracy >= 0.58
        and int(row.selected_config["hash_replicas"]) == 2
        and selected_accuracy > baseline_accuracy
        and selected_accuracy >= majority_accuracy + 0.03
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
    parser.add_argument("commonsense_train")
    parser.add_argument("commonsense_test", nargs="?", default=None)
    parser.add_argument("--output", default="results/cic_006_dualhash.json")
    args = parser.parse_args()
    print(
        json.dumps(
            run_mixed_experiment(
                args.mawps,
                args.commonsense_train,
                args.commonsense_test,
                args.output,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
