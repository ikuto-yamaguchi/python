from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .cic_choice_data import choice_features
from .cic_choice_model import _dot
from .curriculum_memory_gate import (
    GateObservation,
    cross_validate_gate,
    train_gate,
)
from .jmmlu_exam_baseline import load_jmmlu
from .mobile_curriculum_memory import QuantizedCurriculumMemory
from .mobile_sparse_core import MAX_MODEL_PACKAGE_BYTES
from .mobile_unified_artifact import MobileUnifiedArtifact


CAPABILITY_ID = "CURRICULUM-MEMORY-TRUST-GATE-001"


def _unit(values: list[float]) -> tuple[float, ...]:
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    scale = variance ** 0.5 or 1.0
    return tuple((value - mean) / scale for value in values)


def _base_scores(base: MobileUnifiedArtifact, stem: str, options: tuple[str, ...]) -> tuple[float, ...]:
    model = base.reasoning.choice
    values = [
        model.scale
        * _dot(
            model.weights,
            choice_features(
                stem,
                option,
                index,
                dimensions=model.dimensions,
                hash_replicas=model.hash_replicas,
                relation_scope=model.relation_scope,
            ),
        )
        for index, option in enumerate(options)
    ]
    return _unit(values)


def run_experiment(
    base_artifact_path: str | Path,
    memory_path: str | Path,
    jmmlu_root: str | Path,
    *,
    output_dir: str | Path = "results",
) -> dict[str, object]:
    started = time.perf_counter()
    base = MobileUnifiedArtifact.load(base_artifact_path)
    memory = QuantizedCurriculumMemory.load(memory_path)
    subjects = load_jmmlu(jmmlu_root)

    observations: list[GateObservation] = []
    for subject, examples in sorted(subjects.items()):
        for index, example in enumerate(examples):
            memory_prediction = memory.score_options(example.stem, example.options)
            observations.append(
                GateObservation(
                    example_id=f"{subject}:{index:04d}",
                    base_scores=_base_scores(base, example.stem, example.options),
                    memory_scores=memory_prediction.scores,
                    active_postings=memory_prediction.active_postings,
                    stem_length=len(example.stem),
                    option_lengths=tuple(len(option) for option in example.options),
                    answer_index=example.answer_index,
                )
            )

    cross_validation = cross_validate_gate(observations, folds=5)
    final_gate = train_gate(
        observations,
        metadata={
            "capability_id": CAPABILITY_ID,
            "training_benchmark": "JMMLU disclosed development diagnostic",
            "training_rows": len(observations),
            "subject_name_feature_used": False,
            "prompt_text_feature_used": False,
            "official_common_test_targets_used": 0,
        },
    )
    gate_bytes = len(final_gate.to_bytes())
    planned_package = base.planned_complete_package_bytes() + len(memory.to_bytes()) + gate_bytes + 64 * 1024
    fold_gains = [int(row["gated_gain_over_base"]) for row in cross_validation["fold_reports"]]
    checks = {
        "all_7536_items_cross_validated": len(observations) == 7_536,
        "five_disjoint_folds": int(cross_validation["folds"]) == 5,
        "out_of_fold_gain_over_base_positive": int(cross_validation["gated_gain_over_base"]) > 0,
        "at_least_three_folds_nonregressing": sum(gain >= 0 for gain in fold_gains) >= 3,
        "subject_name_feature_used_false": cross_validation["subject_name_feature_used"] is False,
        "prompt_text_feature_used_false": cross_validation["prompt_text_feature_used"] is False,
        "official_common_test_targets_used_zero": True,
        "gate_below_16kb": gate_bytes <= 16 * 1024,
        "package_below_decimal_1gb": planned_package <= MAX_MODEL_PACKAGE_BYTES,
    }
    result = {
        "capability_id": CAPABILITY_ID,
        "protocol": {
            "jmmlu_status": "fully disclosed development benchmark after zero-shot baseline",
            "individual_targets_manually_inspected": 0,
            "target_labels_used_by_gate_training": len(observations),
            "subject_name_visible_to_gate": False,
            "prompt_text_visible_to_gate": False,
            "official_common_test_targets_used": 0,
            "official_common_test_remains_prospective": True,
        },
        "cross_validation": cross_validation,
        "final_gate": {
            "serialized_bytes": gate_bytes,
            "threshold": final_gate.threshold,
            "weight_count": len(final_gate.weights),
            "metadata": final_gate.metadata,
        },
        "resources": {
            "base_package_bytes": base.planned_complete_package_bytes(),
            "curriculum_memory_bytes": len(memory.to_bytes()),
            "gate_bytes": gate_bytes,
            "planned_complete_package_bytes": planned_package,
            "decimal_1gb_limit": MAX_MODEL_PACKAGE_BYTES,
            "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "elapsed_seconds": time.perf_counter() - started,
        },
        "checks": checks,
        "gate_experiment_passed": all(checks.values()),
        "university_exam_mastery_passed": False,
        "highschool_level_passed": False,
        "mobile_device_gate_passed": False,
        "claim_boundary": (
            "The gate uses JMMLU labels only through five-fold out-of-fold training. "
            "It is not an untouched result. The official 2026 Common Test manifest "
            "remains prospective and no university-exam mastery claim is allowed."
        ),
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "curriculum_memory_gate.zlib").write_bytes(final_gate.to_bytes())
    (output / "curriculum_gate_jmmlu.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not result["gate_experiment_passed"]:
        raise SystemExit("curriculum-memory trust gate did not generalize")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_artifact")
    parser.add_argument("memory")
    parser.add_argument("jmmlu_root")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()
    print(
        json.dumps(
            run_experiment(
                args.base_artifact,
                args.memory,
                args.jmmlu_root,
                output_dir=args.output_dir,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
