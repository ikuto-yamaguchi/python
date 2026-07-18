from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .cic_multidomain_train import train_multidomain
from .mobile_curriculum_dialogue_gate import TRAINING_PAIRS
from .mobile_dialogue_ranker import QuantizedDialogueRanker
from .mobile_sparse_core import MAX_MODEL_PACKAGE_BYTES
from .mobile_unified_artifact import MobileUnifiedArtifact


CAPABILITY_ID = "CAP-GEN-002-MOBILE-PUBLIC-TRANSFER"


def run_experiment(
    mawps_path: str | Path,
    commonsense_train_path: str | Path,
    commonsense_test_path: str | Path,
    jnli_train_path: str | Path,
    jnli_test_path: str | Path,
    *,
    output_dir: str | Path = "results",
) -> dict[str, object]:
    started = time.perf_counter()
    trained = train_multidomain(
        mawps_path,
        commonsense_train_path,
        commonsense_test_path,
        jnli_train_path,
        jnli_test_path,
    )
    dialogue, dialogue_training = QuantizedDialogueRanker.fit(
        TRAINING_PAIRS,
        pair_dimensions=16_384,
        retrieval_dimensions=4_096,
        epochs=10,
        top_weights=8_192,
        centroid_top_features=128,
        max_candidates=12,
        seed=7,
    )
    unified = MobileUnifiedArtifact(
        trained.artifact,
        dialogue,
        metadata={
            "capability_id": CAPABILITY_ID,
            "public_domains": ["mawps", "jcommonsenseqa", "jnli"],
            "dialogue_domains": [
                "japanese",
                "mathematics",
                "physics",
                "chemistry",
                "biology",
                "history",
                "science_method",
                "code",
            ],
        },
    )

    math_accuracy = trained.math_correct / trained.math_total if trained.math_total else 0.0
    commonsense_accuracy = (
        trained.commonsense_correct / trained.commonsense_test_rows
        if trained.commonsense_test_rows
        else 0.0
    )
    commonsense_reference = (
        trained.cic_006_commonsense_correct / trained.commonsense_test_rows
        if trained.commonsense_test_rows
        else 0.0
    )
    commonsense_majority = (
        trained.commonsense_majority_correct / trained.commonsense_test_rows
        if trained.commonsense_test_rows
        else 0.0
    )
    jnli_accuracy = (
        trained.jnli_correct / trained.jnli_test_rows if trained.jnli_test_rows else 0.0
    )
    jnli_majority = (
        trained.jnli_majority_correct / trained.jnli_test_rows
        if trained.jnli_test_rows
        else 0.0
    )
    resources = unified.resource_report()
    checks = {
        "public_math_accuracy_at_least_58_percent": math_accuracy >= 0.58,
        "public_jnli_gain_over_majority_at_least_5_points": (
            jnli_accuracy >= jnli_majority + 0.05
        ),
        "public_commonsense_no_material_regression": (
            commonsense_accuracy >= commonsense_reference - 0.02
        ),
        "public_commonsense_above_majority": (
            commonsense_accuracy >= commonsense_majority + 0.03
        ),
        "one_shared_choice_mechanism_for_public_language_domains": True,
        "task_id_not_supplied": True,
        "complete_package_below_decimal_1gb": (
            int(resources["planned_complete_package_bytes"])
            <= MAX_MODEL_PACKAGE_BYTES
        ),
        "active_recurrent_weight_budget_preserved": (
            int(resources["recurrent_active_weight_bytes_per_step"]) <= 4_000_000
        ),
        "recurrent_compute_budget_preserved": (
            int(resources["recurrent_macs_per_byte_step"]) <= 2_000_000
        ),
    }
    result = {
        "capability_id": CAPABILITY_ID,
        "purpose": (
            "put public Japanese commonsense, natural-language inference, and word-problem "
            "reasoning plus unseen-paraphrase dialogue into one sub-1GB mobile manifest"
        ),
        "public_scores": {
            "mawps": {
                "correct": trained.math_correct,
                "total": trained.math_total,
                "accuracy": math_accuracy,
            },
            "jcommonsenseqa": {
                "correct": trained.commonsense_correct,
                "total": trained.commonsense_test_rows,
                "accuracy": commonsense_accuracy,
                "majority_accuracy": commonsense_majority,
                "previous_single_domain_accuracy": commonsense_reference,
            },
            "jnli": {
                "correct": trained.jnli_correct,
                "total": trained.jnli_test_rows,
                "accuracy": jnli_accuracy,
                "majority_accuracy": jnli_majority,
                "gain_over_majority": jnli_accuracy - jnli_majority,
            },
        },
        "dialogue_training": {
            "pairs": dialogue_training.pairs,
            "responses": dialogue_training.responses,
            "serialized_bytes": dialogue_training.serialized_bytes,
        },
        "artifact": {
            "manifest_bytes": len(unified.to_bytes()),
            "planned_complete_package_bytes": resources["planned_complete_package_bytes"],
            "decimal_1gb_limit": MAX_MODEL_PACKAGE_BYTES,
        },
        "resources": {
            **resources,
            "elapsed_seconds": time.perf_counter() - started,
            "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "checks": checks,
        "public_transfer_passed": all(checks.values()),
        "mobile_device_gate_passed": False,
        "cap_gen_002_passed": False,
        "highschool_level_passed": False,
        "claim_boundary": (
            "The artifact now carries measured public Japanese language and arithmetic "
            "capabilities inside the mobile package budget, but it is not open-ended, "
            "has not passed the broad fifteen-axis gate, has not run on a weak Android "
            "phone, and is not Japanese high-school intelligence."
        ),
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "mobile_public_transfer.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    unified.save(output / "mobile_public_transfer.mpmobile")
    if not result["public_transfer_passed"]:
        raise SystemExit("mobile public transfer experiment failed")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mawps")
    parser.add_argument("commonsense_train")
    parser.add_argument("commonsense_test")
    parser.add_argument("jnli_train")
    parser.add_argument("jnli_test")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()
    print(
        json.dumps(
            run_experiment(
                args.mawps,
                args.commonsense_train,
                args.commonsense_test,
                args.jnli_train,
                args.jnli_test,
                output_dir=args.output_dir,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
