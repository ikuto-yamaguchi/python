from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_discourse_focus import DiscourseFocusLearner
from .sparc_open_textbook_gate import QUERIES, RELATIONS, base_training, jpnum, train_queries
from .sparc_zero_subject import ZeroSubjectLearner
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
    model = train(IndexedZeroSubjectLearner)
    scan_baseline = train(ZeroSubjectLearner)
    incapable_baseline = train(DiscourseFocusLearner)

    indexed_initial_bytes = len(model.to_bytes())
    scan_initial_bytes = len(scan_baseline.to_bytes())
    overhead = indexed_initial_bytes - scan_initial_bytes

    model.zero_subject_template_reads = 0
    scan_baseline.zero_subject_template_reads = 0
    indexed_correct = 0
    scan_correct = 0
    incapable_correct = 0
    max_candidates = 0
    feature_reads = 0

    for index in range(80):
        suffix = jpnum(800 + index)
        subject = "索引主題" + suffix
        category = "索引分類" + suffix
        result = "索引結果" + suffix
        passage = RELATIONS["tax"][3].format(a=subject, b=category) + result + "を引き起こす。"

        accepted = model.read_passage(passage, f"索引資料-{index:02d}")
        answer = model.ask(QUERIES["cause"]["direct"][0].format(a=subject))
        indexed_correct += int(
            all(ok for ok, _ in accepted)
            and answer.value == result
            and answer.sources == (f"索引資料-{index:02d}:2",)
        )
        feature_reads += model.last_feature_reads
        max_candidates = max(max_candidates, model.last_candidates)

        scan_baseline.read_passage(passage, f"走査資料-{index:02d}")
        scan_answer = scan_baseline.ask(QUERIES["cause"]["direct"][0].format(a=subject))
        scan_correct += int(scan_answer.value == result)

        incapable_baseline.read_passage(passage, f"未拡張資料-{index:02d}")
        incapable_answer = incapable_baseline.ask(QUERIES["cause"]["direct"][0].format(a=subject))
        incapable_correct += int(incapable_answer.value == result)

    indexed_reads = model.zero_subject_template_reads
    scan_reads = scan_baseline.zero_subject_template_reads

    model.reset_discourse()
    before = (len(model.facts), len(model.entities))
    unknown = [model.read_discourse_sentence("孤立結果を引き起こす。", f"孤立-{i}") for i in range(10)]
    after = (len(model.facts), len(model.entities))

    blob = model.to_bytes()
    restored = IndexedZeroSubjectLearner.from_bytes(blob)
    restored.read_passage(
        RELATIONS["tax"][3].format(a="復元主題", b="復元分類") + "復元結果を引き起こす。",
        "復元資料",
    )
    restored_answer = restored.ask(QUERIES["cause"]["direct"][0].format(a="復元主題"))

    elapsed = time.perf_counter() - started
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    reduction = 1.0 - (indexed_reads / scan_reads if scan_reads else 1.0)

    checks = {
        "indexed_zero_subject_80_of_80": indexed_correct == 80,
        "scan_baseline_same_capability_80_of_80": scan_correct == 80,
        "unextended_baseline_zero_of_80": incapable_correct == 0,
        "template_reads_reduced_by_at_least_70_percent": reduction >= 0.70,
        "learned_index_has_entries": model.report()["zero_subject_suffix_index_entries"] > 0,
        "no_handwritten_suffixes": model.report()["handwritten_suffixes_used"] is False,
        "no_additional_state_slots": model.report()["state_slots_added"] == 0,
        "unbound_10_of_10_abstained": all(not ok for ok, _ in unknown),
        "unbound_preserved_graph": before == after,
        "save_restore_preserves_indexed_recovery": restored_answer.value == "復元結果",
        "implementation_overhead_at_most_2048_bytes": overhead <= 2048,
        "peak_rss_below_64_mib": peak_rss < 64 * 1024 * 1024,
        "wall_time_below_2_seconds": elapsed < 2.0,
        "max_candidates_at_most_11": max_candidates <= 11,
        "estimated_operations_below_60000": feature_reads + indexed_reads < 60000,
    }
    report = {
        "experiment": "SPARC-zero-subject-index-001",
        "passed": all(checks.values()),
        "checks": checks,
        "metrics": {
            "indexed_correct": indexed_correct,
            "scan_baseline_correct": scan_correct,
            "unextended_baseline_correct": incapable_correct,
            "indexed_template_reads": indexed_reads,
            "scan_template_reads": scan_reads,
            "template_read_reduction": reduction,
            "scan_initial_serialized_bytes": scan_initial_bytes,
            "indexed_initial_serialized_bytes": indexed_initial_bytes,
            "implementation_overhead_bytes": overhead,
            "serialized_bytes_after_80_new_facts": len(blob),
            "peak_rss_bytes": peak_rss,
            "wall_seconds": elapsed,
            "max_candidates": max_candidates,
            "query_feature_reads": feature_reads,
            "estimated_operations": feature_reads + indexed_reads,
            "state_slots_added": 0,
        },
        "model": model.report(),
        "claim_boundary": (
            "Preserves paragraph-local learned-template zero-subject recovery while replacing a full relation-surface scan with a learned sparse suffix index. "
            "It does not establish unrestricted Japanese ellipsis resolution, ordinary textbook comprehension, or high-school-level intelligence."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "SPARC-zero-subject-index-001.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-zero-subject-index-001.model.zlib").write_bytes(blob)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = run_gate(args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
