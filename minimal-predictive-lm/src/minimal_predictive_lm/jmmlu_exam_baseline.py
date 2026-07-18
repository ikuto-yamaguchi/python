from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import resource
import time
from typing import Iterable

from .cic_choice_data import ChoiceExample, load_choice_dataset
from .cic_choice_model import choice_accuracy
from .cic_multidomain_train import train_multidomain
from .mobile_sparse_core import MAX_MODEL_PACKAGE_BYTES, MOBILE_1GB_PROFILE
from .university_exam_mastery_contract import UniversityExamMasteryContract


CAPABILITY_ID = "UNIVERSITY-EXAM-MASTERY-BASELINE-001"

HIGH_SCHOOL_SUBJECT_PREFIXES = (
    "high_school_",
    "japanese_",
)
HIGH_SCHOOL_SUBJECTS = {
    "world_history",
    "formal_logic",
    "elementary_mathematics",
    "conceptual_physics",
    "global_facts",
    "world_religions",
}


def _raw_prompt(question: str, options: tuple[str, ...]) -> str:
    return "問題：" + question.strip() + "\n" + "\n".join(
        f"({index}){option.strip()}" for index, option in enumerate(options)
    )


def _answer_index(value: str) -> int:
    normalized = value.strip().upper().strip("()[]{} .")
    if normalized in {"A", "B", "C", "D"}:
        return ord(normalized) - ord("A")
    if normalized in {"0", "1", "2", "3"}:
        return int(normalized)
    raise ValueError(f"unsupported JMMLU answer: {value!r}")


def _subject_name(path: Path) -> str:
    return path.stem.removesuffix("_test")


def load_jmmlu(root: str | Path) -> dict[str, list[ChoiceExample]]:
    base = Path(root)
    candidates = list(base.glob("JMMLU/test/*.csv"))
    if not candidates:
        candidates = list(base.glob("test/*.csv"))
    if not candidates:
        candidates = list(base.rglob("*.csv"))
    grouped: dict[str, list[ChoiceExample]] = defaultdict(list)
    for path in sorted(candidates):
        subject = _subject_name(path)
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"question", "A", "B", "C", "D", "answer"}
            if reader.fieldnames is None or not required.issubset(reader.fieldnames):
                continue
            for row in reader:
                options = tuple(str(row[key]) for key in ("A", "B", "C", "D"))
                prompt = _raw_prompt(str(row["question"]), options)
                grouped[subject].append(
                    ChoiceExample(
                        raw_question=prompt,
                        stem=str(row["question"]).strip(),
                        options=options,
                        answer_index=_answer_index(str(row["answer"])),
                    )
                )
    if len(grouped) < 50:
        raise ValueError(f"JMMLU subject coverage unexpectedly small: {len(grouped)}")
    return dict(grouped)


def _hashes(rows: Iterable[ChoiceExample]) -> set[str]:
    return {
        hashlib.sha256(row.raw_question.encode("utf-8")).hexdigest()
        for row in rows
    }


def run_baseline(
    mawps_path: str | Path,
    commonsense_train_path: str | Path,
    commonsense_test_path: str | Path,
    jnli_train_path: str | Path,
    jnli_test_path: str | Path,
    jmmlu_root: str | Path,
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
    subjects = load_jmmlu(jmmlu_root)
    training_rows = (
        load_choice_dataset(commonsense_train_path)
        + load_choice_dataset(jnli_train_path)
    )
    training_hashes = _hashes(training_rows)
    jmmlu_hashes = _hashes(row for rows in subjects.values() for row in rows)
    exact_overlap = len(training_hashes & jmmlu_hashes)

    subject_scores: dict[str, dict[str, object]] = {}
    total_correct = 0
    total_items = 0
    high_school_correct = 0
    high_school_items = 0
    for subject, rows in sorted(subjects.items()):
        correct, total, work = choice_accuracy(trained.artifact.choice, rows)
        accuracy = correct / total if total else 0.0
        is_high_school = subject.startswith(HIGH_SCHOOL_SUBJECT_PREFIXES) or subject in HIGH_SCHOOL_SUBJECTS
        subject_scores[subject] = {
            "correct": correct,
            "total": total,
            "accuracy": accuracy,
            "work": work,
            "high_school_or_entrance_relevant": is_high_school,
        }
        total_correct += correct
        total_items += total
        if is_high_school:
            high_school_correct += correct
            high_school_items += total

    overall_accuracy = total_correct / total_items if total_items else 0.0
    high_school_accuracy = (
        high_school_correct / high_school_items if high_school_items else 0.0
    )
    weakest = sorted(
        (
            (subject, float(row["accuracy"]), int(row["correct"]), int(row["total"]))
            for subject, row in subject_scores.items()
        ),
        key=lambda item: (item[1], item[0]),
    )[:10]
    artifact_bytes = len(trained.artifact.to_bytes())
    planned_package = MOBILE_1GB_PROFILE.package_bytes() + artifact_bytes + 128 * 1024
    contract = UniversityExamMasteryContract.evaluate({})
    checks = {
        "jmmlu_56_subjects_present": len(subject_scores) == 56,
        "jmmlu_7536_items_present": total_items == 7_536,
        "jmmlu_test_targets_used_for_training_zero": True,
        "jmmlu_used_for_configuration_selection_false": True,
        "exact_training_prompt_overlap_zero": exact_overlap == 0,
        "subject_name_not_supplied_to_model": True,
        "complete_package_below_decimal_1gb": planned_package <= MAX_MODEL_PACKAGE_BYTES,
        "completion_remains_false_until_all_exam_domains_are_perfect": (
            contract["completion_allowed"] is False
        ),
    }
    result = {
        "capability_id": CAPABILITY_ID,
        "purpose": (
            "Measure the existing shared non-Transformer mobile learner on all JMMLU "
            "subjects without using any JMMLU target for training or model selection."
        ),
        "protocol": {
            "subjects": len(subject_scores),
            "items": total_items,
            "jmmlu_test_targets_used_for_training": 0,
            "jmmlu_examples_used_for_configuration_selection": 0,
            "subject_name_visible_to_model": False,
            "exact_training_prompt_overlap": exact_overlap,
        },
        "overall": {
            "correct": total_correct,
            "total": total_items,
            "accuracy": overall_accuracy,
        },
        "high_school_and_entrance_subset": {
            "correct": high_school_correct,
            "total": high_school_items,
            "accuracy": high_school_accuracy,
        },
        "subject_scores": subject_scores,
        "weakest_subjects": [
            {
                "subject": subject,
                "accuracy": accuracy,
                "correct": correct,
                "total": total,
            }
            for subject, accuracy, correct, total in weakest
        ],
        "training_reference": {
            "selected_config": trained.selected_config,
            "jcommonsenseqa_correct": trained.commonsense_correct,
            "jcommonsenseqa_total": trained.commonsense_test_rows,
            "jnli_correct": trained.jnli_correct,
            "jnli_total": trained.jnli_test_rows,
            "mawps_correct": trained.math_correct,
            "mawps_total": trained.math_total,
        },
        "resources": {
            "recurrent_profile_bytes": MOBILE_1GB_PROFILE.package_bytes(),
            "reasoning_artifact_bytes": artifact_bytes,
            "planned_complete_package_bytes": planned_package,
            "decimal_1gb_limit": MAX_MODEL_PACKAGE_BYTES,
            "active_weight_bytes_per_step": MOBILE_1GB_PROFILE.active_weight_bytes_per_step(),
            "macs_per_byte_step": MOBILE_1GB_PROFILE.macs_per_byte_step(),
            "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "elapsed_seconds": time.perf_counter() - started,
        },
        "checks": checks,
        "baseline_experiment_passed": all(checks.values()),
        "university_exam_mastery": contract,
        "university_exam_mastery_passed": False,
        "highschool_level_passed": False,
        "mobile_device_gate_passed": False,
        "claim_boundary": (
            "JMMLU is only a multiple-choice academic diagnostic. Even a perfect JMMLU "
            "score would not satisfy the required Common Test, every university exam, "
            "constructed responses, listening, essays, interviews, and communication."
        ),
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "jmmlu_exam_baseline.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not result["baseline_experiment_passed"]:
        raise SystemExit("JMMLU baseline protocol failed")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mawps")
    parser.add_argument("commonsense_train")
    parser.add_argument("commonsense_test")
    parser.add_argument("jnli_train")
    parser.add_argument("jnli_test")
    parser.add_argument("jmmlu_root")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()
    print(
        json.dumps(
            run_baseline(
                args.mawps,
                args.commonsense_train,
                args.commonsense_test,
                args.jnli_train,
                args.jnli_test,
                args.jmmlu_root,
                output_dir=args.output_dir,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
