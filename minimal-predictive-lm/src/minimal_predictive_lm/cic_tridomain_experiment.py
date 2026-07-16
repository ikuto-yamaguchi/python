from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

from .cic_tridomain_train import (
    CIC007_COMMONSENSE_CORRECT,
    CIC007_COMMONSENSE_TOTAL,
    CIC007_JNLI_CORRECT,
    CIC007_JNLI_TOTAL,
    train_tridomain,
)


def run_tridomain_experiment(
    mawps_path: str | Path,
    commonsense_train_path: str | Path,
    commonsense_test_path: str | Path,
    jnli_train_path: str | Path,
    jnli_test_path: str | Path,
    jsts_train_path: str | Path,
    jsts_test_path: str | Path,
    output: str | Path | None = None,
) -> dict[str, object]:
    start = time.perf_counter()
    row = train_tridomain(
        mawps_path,
        commonsense_train_path,
        commonsense_test_path,
        jnli_train_path,
        jnli_test_path,
        jsts_train_path,
        jsts_test_path,
    )
    artifact_bytes = len(row.artifact.to_bytes())
    math_accuracy = row.math_correct / row.math_total if row.math_total else 0.0
    commonsense_accuracy = row.commonsense_correct / row.commonsense_test_rows
    jnli_accuracy = row.jnli_correct / row.jnli_test_rows
    cic007_commonsense_accuracy = CIC007_COMMONSENSE_CORRECT / CIC007_COMMONSENSE_TOTAL
    cic007_jnli_accuracy = CIC007_JNLI_CORRECT / CIC007_JNLI_TOTAL
    elapsed = time.perf_counter() - start
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    result: dict[str, object] = {
        "capability_id": "CIC-008-TRIDOMAIN",
        "neural_network_used": False,
        "gradient_training_used": False,
        "task_id_input_used": False,
        "same_choice_mechanism_for_all_three_domains": True,
        "same_artifact_for_all_capabilities": True,
        "jsts_validation_new_to_research_sequence": True,
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
            "inner_tridomain_validation": row.inner_validation,
            "joint_train_rows": row.joint_train_rows,
            "choice_nonzero_weights": row.choice_nonzero_weights,
            "test_used_for_selection": False,
        },
        "jcommonsenseqa": {
            "official_train_rows": row.commonsense_train_rows,
            "validation_rows": row.commonsense_test_rows,
            "correct": row.commonsense_correct,
            "accuracy": commonsense_accuracy,
            "cic_007_reference_accuracy": cic007_commonsense_accuracy,
            "change_from_cic_007": commonsense_accuracy - cic007_commonsense_accuracy,
            "majority_accuracy": row.commonsense_majority_correct / row.commonsense_test_rows,
            "mean_checked_options": row.commonsense_work,
            "role": "regression_check",
        },
        "jnli": {
            "official_train_rows": row.jnli_train_rows,
            "validation_rows": row.jnli_test_rows,
            "correct": row.jnli_correct,
            "accuracy": jnli_accuracy,
            "cic_007_reference_accuracy": cic007_jnli_accuracy,
            "change_from_cic_007": jnli_accuracy - cic007_jnli_accuracy,
            "majority_accuracy": row.jnli_majority_correct / row.jnli_test_rows,
            "mean_checked_options": row.jnli_work,
            "role": "regression_check",
        },
        "jsts": {
            "official_train_rows": row.jsts_train_rows,
            "untouched_validation_rows": row.jsts_test_rows,
            "prediction_grid": "0.0 to 5.0 in 0.5 increments",
            **row.jsts_metrics,
            "mean_baseline": row.jsts_baseline_metrics,
            "mae_improvement_over_mean": row.jsts_baseline_metrics["mae"] - row.jsts_metrics["mae"],
            "role": "new_domain_primary_evaluation",
        },
        "artifact": {
            "bytes": artifact_bytes,
            "format": "cic-mixed-003",
        },
        "resources": {
            "arithmetic_synthesis_expansions": row.math_expansions,
            "elapsed_seconds": elapsed,
            "peak_process_kib": peak,
        },
        "claim_boundary": (
            "CIC-008 tests one sparse candidate-selection mechanism on Japanese "
            "commonsense QA, NLI and half-step semantic similarity. JSTS is "
            "discretized to eleven candidates; this is not exact continuous "
            "regression, open-ended dialogue or general intelligence."
        ),
    }
    result["passed"] = bool(
        math_accuracy >= 0.58
        and commonsense_accuracy >= cic007_commonsense_accuracy - 0.02
        and jnli_accuracy >= cic007_jnli_accuracy - 0.02
        and row.jsts_metrics["pearson"] >= 0.45
        and row.jsts_metrics["mae"] <= row.jsts_baseline_metrics["mae"] - 0.15
        and artifact_bytes <= 250_000
        and peak <= 2_500_000
        and elapsed <= 1_200
    )
    if output is not None:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        row.artifact.save(path.with_suffix(".mixed.cic"))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CIC tri-domain experiment")
    parser.add_argument("mawps")
    parser.add_argument("commonsense_train")
    parser.add_argument("commonsense_test")
    parser.add_argument("jnli_train")
    parser.add_argument("jnli_test")
    parser.add_argument("jsts_train")
    parser.add_argument("jsts_test")
    parser.add_argument("--output", default="results/cic_008_tridomain.json")
    args = parser.parse_args()
    print(
        json.dumps(
            run_tridomain_experiment(
                args.mawps,
                args.commonsense_train,
                args.commonsense_test,
                args.jnli_train,
                args.jnli_test,
                args.jsts_train,
                args.jsts_test,
                args.output,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
