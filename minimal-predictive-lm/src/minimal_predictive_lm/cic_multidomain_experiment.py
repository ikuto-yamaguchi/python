from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

from .cic_multidomain_train import train_multidomain


def run_multidomain_experiment(
    mawps_path: str | Path,
    commonsense_train_path: str | Path,
    commonsense_test_path: str | Path,
    jnli_train_path: str | Path,
    jnli_test_path: str | Path,
    output: str | Path | None = None,
) -> dict[str, object]:
    start = time.perf_counter()
    row = train_multidomain(
        mawps_path,
        commonsense_train_path,
        commonsense_test_path,
        jnli_train_path,
        jnli_test_path,
    )
    artifact_bytes = len(row.artifact.to_bytes())
    math_accuracy = row.math_correct / row.math_total if row.math_total else 0.0
    commonsense_accuracy = (
        row.commonsense_correct / row.commonsense_test_rows
        if row.commonsense_test_rows
        else 0.0
    )
    cic_006_accuracy = (
        row.cic_006_commonsense_correct / row.commonsense_test_rows
        if row.commonsense_test_rows
        else 0.0
    )
    commonsense_majority_accuracy = (
        row.commonsense_majority_correct / row.commonsense_test_rows
        if row.commonsense_test_rows
        else 0.0
    )
    jnli_accuracy = row.jnli_correct / row.jnli_test_rows if row.jnli_test_rows else 0.0
    jnli_majority_accuracy = (
        row.jnli_majority_correct / row.jnli_test_rows if row.jnli_test_rows else 0.0
    )
    result: dict[str, object] = {
        "capability_id": "CIC-007-MULTIDOMAIN",
        "neural_network_used": False,
        "gradient_training_used": False,
        "task_id_input_used": False,
        "same_choice_mechanism_for_both_domains": True,
        "same_artifact_for_all_capabilities": True,
        "jnli_validation_new_to_research_sequence": True,
        "arithmetic": {
            "correct": row.math_correct,
            "total": row.math_total,
            "accuracy": math_accuracy,
            "mechanisms": row.math_mechanisms,
            "mean_checked_mechanisms": row.math_work,
            "selected_epochs": row.math_epochs,
            "inner_validation_accuracy_by_epoch": row.math_validation,
        },
        "shared_choice_mechanism": {
            "selected_config_name": row.selected_config_name,
            "selected_config": row.selected_config,
            "candidate_configs": row.candidate_configs,
            "inner_multidomain_validation": row.inner_validation,
            "joint_train_rows": row.joint_train_rows,
            "choice_nonzero_weights": row.choice_nonzero_weights,
            "test_used_for_selection": False,
        },
        "jcommonsenseqa": {
            "official_train_rows": row.commonsense_train_rows,
            "validation_rows": row.commonsense_test_rows,
            "joint_correct": row.commonsense_correct,
            "joint_accuracy": commonsense_accuracy,
            "cic_006_single_domain_correct": row.cic_006_commonsense_correct,
            "cic_006_single_domain_accuracy": cic_006_accuracy,
            "absolute_change_from_cic_006": commonsense_accuracy - cic_006_accuracy,
            "majority_accuracy": commonsense_majority_accuracy,
            "mean_checked_options": row.commonsense_work,
            "role": "regression_check_after_prior_validation_use",
        },
        "jnli": {
            "official_train_rows": row.jnli_train_rows,
            "untouched_validation_rows": row.jnli_test_rows,
            "correct": row.jnli_correct,
            "accuracy": jnli_accuracy,
            "majority_accuracy": jnli_majority_accuracy,
            "gain_over_majority": jnli_accuracy - jnli_majority_accuracy,
            "mean_checked_options": row.jnli_work,
            "role": "new_domain_primary_evaluation",
        },
        "artifact": {
            "bytes": artifact_bytes,
            "format": "cic-mixed-003",
        },
        "resources": {
            "arithmetic_synthesis_expansions": row.math_expansions,
            "elapsed_seconds": time.perf_counter() - start,
            "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "claim_boundary": (
            "CIC-007 demonstrates one sparse candidate-selection mechanism "
            "trained jointly on Japanese commonsense QA and natural-language "
            "inference without a task-ID input. Candidate labels are supplied "
            "in the input format. This is not open-ended dialogue or general "
            "high-school-level intelligence."
        ),
    }
    result["passed"] = bool(
        math_accuracy >= 0.58
        and jnli_accuracy >= jnli_majority_accuracy + 0.05
        and commonsense_accuracy >= cic_006_accuracy - 0.02
        and commonsense_accuracy >= commonsense_majority_accuracy + 0.03
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
    parser = argparse.ArgumentParser(description="Run CIC multidomain experiment")
    parser.add_argument("mawps")
    parser.add_argument("commonsense_train")
    parser.add_argument("commonsense_test")
    parser.add_argument("jnli_train")
    parser.add_argument("jnli_test")
    parser.add_argument("--output", default="results/cic_007_multidomain.json")
    args = parser.parse_args()
    print(
        json.dumps(
            run_multidomain_experiment(
                args.mawps,
                args.commonsense_train,
                args.commonsense_test,
                args.jnli_train,
                args.jnli_test,
                args.output,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
