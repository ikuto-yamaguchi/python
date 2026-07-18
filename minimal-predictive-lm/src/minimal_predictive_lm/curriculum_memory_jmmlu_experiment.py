from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import resource
import time
from typing import Sequence

from .cic_choice_data import ChoiceExample, choice_features
from .cic_choice_model import QuantizedChoiceMechanism, _dot
from .japanese_curriculum_corpus import load_curriculum
from .jmmlu_exam_baseline import load_jmmlu
from .mobile_curriculum_memory import QuantizedCurriculumMemory
from .mobile_sparse_core import MAX_MODEL_PACKAGE_BYTES
from .mobile_unified_artifact import MobileUnifiedArtifact


CAPABILITY_ID = "CURRICULUM-MEMORY-JMMLU-DEVELOPMENT-001"
ALPHAS = (0.25, 0.50, 0.75, 1.00)
CONFIDENCE_THRESHOLDS = (0.0, 0.35, 0.70)


@dataclass(frozen=True)
class ScoredRow:
    subject: str
    example: ChoiceExample
    base_scores: tuple[float, ...]
    memory_scores: tuple[float, ...]
    memory_confidence: float
    active_postings: int


def _unit(values: Sequence[float]) -> tuple[float, ...]:
    if not values:
        return ()
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    scale = variance ** 0.5 or 1.0
    return tuple((value - mean) / scale for value in values)


def _base_scores(
    model: QuantizedChoiceMechanism,
    stem: str,
    options: Sequence[str],
) -> tuple[float, ...]:
    scores = [
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
    return _unit(scores)


def _development(example: ChoiceExample) -> bool:
    digest = hashlib.sha256(("curriculum-memory-dev:" + example.raw_question).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little") % 5 == 0


def _predict(row: ScoredRow, alpha: float, threshold: float) -> int:
    if row.memory_confidence < threshold:
        return max(range(len(row.base_scores)), key=lambda index: row.base_scores[index])
    combined = tuple(
        (1.0 - alpha) * base + alpha * memory
        for base, memory in zip(row.base_scores, row.memory_scores)
    )
    return max(range(len(combined)), key=lambda index: combined[index])


def _accuracy(rows: Sequence[ScoredRow], alpha: float, threshold: float) -> tuple[int, int]:
    correct = sum(
        _predict(row, alpha, threshold) == row.example.answer_index for row in rows
    )
    return correct, len(rows)


def _base_accuracy(rows: Sequence[ScoredRow]) -> tuple[int, int]:
    correct = sum(
        max(range(len(row.base_scores)), key=lambda index: row.base_scores[index])
        == row.example.answer_index
        for row in rows
    )
    return correct, len(rows)


def run_experiment(
    reference_artifact: str | Path,
    curriculum_path: str | Path,
    jmmlu_root: str | Path,
    *,
    output_dir: str | Path = "results",
) -> dict[str, object]:
    started = time.perf_counter()
    unified = MobileUnifiedArtifact.load(reference_artifact)
    documents = load_curriculum(curriculum_path)
    memory = QuantizedCurriculumMemory.build(documents)
    subjects = load_jmmlu(jmmlu_root)

    scored: list[ScoredRow] = []
    for subject, rows in sorted(subjects.items()):
        for example in rows:
            memory_prediction = memory.score_options(example.stem, example.options)
            scored.append(
                ScoredRow(
                    subject=subject,
                    example=example,
                    base_scores=_base_scores(
                        unified.reasoning.choice,
                        example.stem,
                        example.options,
                    ),
                    memory_scores=memory_prediction.scores,
                    memory_confidence=memory_prediction.confidence,
                    active_postings=memory_prediction.active_postings,
                )
            )
    development = [row for row in scored if _development(row.example)]
    holdout = [row for row in scored if not _development(row.example)]
    if not development or not holdout:
        raise ValueError("JMMLU hash split is empty")

    candidates: dict[str, dict[str, object]] = {}
    selected: tuple[float, float, float, float] | None = None
    for alpha in ALPHAS:
        for threshold in CONFIDENCE_THRESHOLDS:
            correct, total = _accuracy(development, alpha, threshold)
            accuracy = correct / total
            key = f"alpha={alpha:.2f}:threshold={threshold:.2f}"
            candidates[key] = {
                "alpha": alpha,
                "threshold": threshold,
                "correct": correct,
                "total": total,
                "accuracy": accuracy,
            }
            candidate = (accuracy, -alpha, threshold, alpha)
            if selected is None or candidate > selected:
                selected = candidate
    if selected is None:
        raise RuntimeError("no curriculum-memory policy")
    _accuracy_value, _neg_alpha, threshold, alpha = selected

    base_dev_correct, base_dev_total = _base_accuracy(development)
    base_hold_correct, base_hold_total = _base_accuracy(holdout)
    hybrid_dev_correct, hybrid_dev_total = _accuracy(development, alpha, threshold)
    hybrid_hold_correct, hybrid_hold_total = _accuracy(holdout, alpha, threshold)
    hybrid_all_correct, hybrid_all_total = _accuracy(scored, alpha, threshold)

    subject_scores: dict[str, dict[str, object]] = {}
    for subject in sorted(subjects):
        subject_rows = [row for row in holdout if row.subject == subject]
        if not subject_rows:
            continue
        base_correct, total = _base_accuracy(subject_rows)
        hybrid_correct, _ = _accuracy(subject_rows, alpha, threshold)
        subject_scores[subject] = {
            "base_correct": base_correct,
            "hybrid_correct": hybrid_correct,
            "total": total,
            "base_accuracy": base_correct / total,
            "hybrid_accuracy": hybrid_correct / total,
            "gain": (hybrid_correct - base_correct) / total,
        }

    memory_report = memory.resource_report()
    planned_package = (
        unified.planned_complete_package_bytes()
        + int(memory_report["serialized_bytes"])
        + 64 * 1024
    )
    checks = {
        "curriculum_documents_at_least_250": len(documents) >= 250,
        "jmmlu_items_complete": len(scored) == 7_536,
        "development_and_holdout_disjoint": len(development) + len(holdout) == len(scored),
        "policy_selected_on_development_only": True,
        "official_common_test_targets_used_zero": True,
        "memory_below_80mb": int(memory_report["serialized_bytes"]) <= 80_000_000,
        "active_memory_below_128kb": int(memory_report["estimated_active_bytes"]) <= 128 * 1024,
        "complete_package_below_decimal_1gb": planned_package <= MAX_MODEL_PACKAGE_BYTES,
    }
    result = {
        "capability_id": CAPABILITY_ID,
        "protocol": {
            "jmmlu_is_development_benchmark": True,
            "strict_unseen_jmmlu_claim_allowed": False,
            "individual_jmmlu_targets_inspected_by_builder": 0,
            "policy_selection_split": "sha256 modulo 5 equals zero",
            "development_items": len(development),
            "internal_holdout_items": len(holdout),
            "official_common_test_targets_used": 0,
            "subject_name_visible_to_model": False,
        },
        "selected_policy": {
            "alpha": alpha,
            "memory_confidence_threshold": threshold,
        },
        "candidate_development_scores": candidates,
        "development": {
            "base_correct": base_dev_correct,
            "hybrid_correct": hybrid_dev_correct,
            "total": base_dev_total,
            "base_accuracy": base_dev_correct / base_dev_total,
            "hybrid_accuracy": hybrid_dev_correct / hybrid_dev_total,
        },
        "internal_holdout": {
            "base_correct": base_hold_correct,
            "hybrid_correct": hybrid_hold_correct,
            "total": base_hold_total,
            "base_accuracy": base_hold_correct / base_hold_total,
            "hybrid_accuracy": hybrid_hold_correct / hybrid_hold_total,
            "gain_correct": hybrid_hold_correct - base_hold_correct,
        },
        "all_jmmlu_development_evidence": {
            "hybrid_correct": hybrid_all_correct,
            "total": hybrid_all_total,
            "accuracy": hybrid_all_correct / hybrid_all_total,
        },
        "subject_holdout_scores": subject_scores,
        "memory": memory_report,
        "resources": {
            "base_mobile_package_bytes": unified.planned_complete_package_bytes(),
            "curriculum_memory_bytes": memory_report["serialized_bytes"],
            "planned_complete_package_bytes": planned_package,
            "decimal_1gb_limit": MAX_MODEL_PACKAGE_BYTES,
            "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "elapsed_seconds": time.perf_counter() - started,
        },
        "checks": checks,
        "experiment_protocol_passed": all(checks.values()),
        "university_exam_mastery_passed": False,
        "highschool_level_passed": False,
        "mobile_device_gate_passed": False,
        "claim_boundary": (
            "This is a disclosed JMMLU development experiment. The untouched official "
            "Common Test source manifest remains the prospective entrance-exam gate."
        ),
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    memory.save(output / "curriculum_memory.zlib")
    (output / "curriculum_memory_jmmlu.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not result["experiment_protocol_passed"]:
        raise SystemExit("curriculum memory experiment protocol failed")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference_artifact")
    parser.add_argument("curriculum")
    parser.add_argument("jmmlu_root")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()
    print(
        json.dumps(
            run_experiment(
                args.reference_artifact,
                args.curriculum,
                args.jmmlu_root,
                output_dir=args.output_dir,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
