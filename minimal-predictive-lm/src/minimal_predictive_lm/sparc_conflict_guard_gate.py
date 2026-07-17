from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_conflict_guard import ConflictGuardLearner
from .sparc_open_textbook_gate import QUERIES, RELATIONS, base_training, jpnum, train_queries
from .sparc_zero_subject_index import IndexedZeroSubjectLearner


def train(cls):
    model = cls()
    records, _, chains = base_training()
    model.learn_paragraphs(records)
    model.induce_rules(min_support=6)
    train_queries(model, chains)
    return model


def run_gate(output_dir: Path) -> dict[str, object]:
    started = time.perf_counter()
    model = train(ConflictGuardLearner)
    baseline = train(IndexedZeroSubjectLearner)
    baseline_bytes = len(baseline.to_bytes())
    guarded_initial_bytes = len(model.to_bytes())

    ordinary_correct = 0
    conflicts_rejected = 0
    conflicts_preserved = 0
    baseline_corrupted = 0
    duplicate_support = 0
    feature_reads = 0
    max_candidates = 0

    for index in range(80):
        suffix = jpnum(900 + index)
        subject = "整合主題" + suffix
        expected = "整合分類" + suffix
        sentence = RELATIONS["tax"][3].format(a=subject, b=expected)
        accepted, _ = model.read_discourse_sentence(sentence, f"正常-{index}")
        answer = model.ask(QUERIES["tax"]["direct"][0].format(a=subject))
        ordinary_correct += int(accepted and answer.value == expected)
        feature_reads += model.last_feature_reads
        max_candidates = max(max_candidates, model.last_candidates)

    for index in range(40):
        suffix = jpnum(980 + index)
        subject = "矛盾主題" + suffix
        first = "正分類" + suffix
        second = "誤分類" + suffix
        initial = RELATIONS["tax"][3].format(a=subject, b=first)
        conflict = RELATIONS["tax"][3].format(a=subject, b=second)
        model.read_discourse_sentence(initial, f"正資料-{index}")
        before = (len(model.facts), len(model.entities))
        accepted, reason = model.read_discourse_sentence(conflict, f"誤資料-{index}")
        after = (len(model.facts), len(model.entities))
        answer = model.ask(QUERIES["tax"]["direct"][0].format(a=subject))
        conflicts_rejected += int(not accepted and reason == "abstain-conflicting-fact")
        conflicts_preserved += int(before == after and answer.value == first)

        baseline.read_discourse_sentence(initial, f"基準正-{index}")
        baseline.read_discourse_sentence(conflict, f"基準誤-{index}")
        baseline_answer = baseline.ask(QUERIES["tax"]["direct"][0].format(a=subject))
        baseline_corrupted += int(baseline_answer.value is None)

    for index in range(20):
        suffix = jpnum(850 + index)
        subject = "重複主題" + suffix
        obj = "重複分類" + suffix
        sentence = RELATIONS["tax"][3].format(a=subject, b=obj)
        first = model.read_discourse_sentence(sentence, f"重複一-{index}")[0]
        second = model.read_discourse_sentence(sentence, f"重複二-{index}")[0]
        duplicate_support += int(first and second)

    blob = model.to_bytes()
    restored = ConflictGuardLearner.from_bytes(blob)
    restore_subject = "復元矛盾主題"
    restored.read_discourse_sentence(RELATIONS["tax"][3].format(a=restore_subject, b="復元正分類"), "復元正")
    restored_result = restored.read_discourse_sentence(RELATIONS["tax"][3].format(a=restore_subject, b="復元誤分類"), "復元誤")
    restored_answer = restored.ask(QUERIES["tax"]["direct"][0].format(a=restore_subject))

    elapsed = time.perf_counter() - started
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    overhead = guarded_initial_bytes - baseline_bytes
    estimated_operations = feature_reads + model.conflict_checks

    checks = {
        "ordinary_learning_80_of_80": ordinary_correct == 80,
        "conflicts_40_of_40_rejected": conflicts_rejected == 40,
        "conflicts_40_of_40_preserve_prior_knowledge": conflicts_preserved == 40,
        "unguarded_baseline_40_of_40_becomes_ambiguous": baseline_corrupted == 40,
        "duplicate_support_20_of_20_accepted": duplicate_support == 20,
        "save_restore_preserves_guard": restored_result == (False, "abstain-conflicting-fact") and restored_answer.value == "復元正分類",
        "no_additional_state_slots": model.report()["conflict_state_slots_added"] == 0,
        "implementation_overhead_at_most_1024_bytes": overhead <= 1024,
        "peak_rss_below_64_mib": peak_rss < 64 * 1024 * 1024,
        "wall_time_below_2_seconds": elapsed < 2.0,
        "max_candidates_at_most_11": max_candidates <= 11,
        "estimated_operations_below_90000": estimated_operations < 90000,
    }
    report = {
        "experiment": "SPARC-conflict-guard-001",
        "passed": all(checks.values()),
        "checks": checks,
        "metrics": {
            "ordinary_correct": ordinary_correct,
            "conflicts_rejected": conflicts_rejected,
            "conflicts_preserved": conflicts_preserved,
            "unguarded_baseline_corrupted": baseline_corrupted,
            "duplicate_support_accepted": duplicate_support,
            "baseline_initial_serialized_bytes": baseline_bytes,
            "guarded_initial_serialized_bytes": guarded_initial_bytes,
            "implementation_overhead_bytes": overhead,
            "serialized_bytes_after_evaluation": len(blob),
            "peak_rss_bytes": peak_rss,
            "wall_seconds": elapsed,
            "max_candidates": max_candidates,
            "query_feature_reads": feature_reads,
            "conflict_checks": model.conflict_checks,
            "estimated_operations": estimated_operations,
            "state_slots_added": 0,
        },
        "claim_boundary": (
            "Prevents a newly read sentence from assigning a second object to an already functional subject-relation pair. "
            "It does not decide which conflicting source is true, revise beliefs over time, understand unrestricted textbooks, or establish high-school-level intelligence."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "SPARC-conflict-guard-001.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "SPARC-conflict-guard-001.model.zlib").write_bytes(blob)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = run_gate(args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
