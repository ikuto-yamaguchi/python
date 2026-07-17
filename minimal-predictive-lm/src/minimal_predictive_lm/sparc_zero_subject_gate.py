from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_zero_subject import ZeroSubjectLearner
from .sparc_discourse_focus import DiscourseFocusLearner
from .sparc_open_textbook_gate import RELATIONS, QUERIES, base_training, train_queries, jpnum


def train(cls):
    model = cls()
    records, _, chains = base_training()
    model.learn_paragraphs(records)
    model.induce_rules(min_support=6)
    train_queries(model, chains)
    return model


def run_gate(output_dir: Path) -> dict[str, object]:
    started = time.perf_counter()
    model = train(ZeroSubjectLearner)
    baseline = train(DiscourseFocusLearner)
    baseline_bytes = len(baseline.to_bytes())
    extension_initial_bytes = len(model.to_bytes())
    overhead = extension_initial_bytes - baseline_bytes

    correct = 0
    baseline_correct = 0
    feature_reads = 0
    max_candidates = 0

    for index in range(60):
        suffix = jpnum(700 + index)
        subject = "省略主題" + suffix
        category = "省略分類" + suffix
        result = "省略結果" + suffix
        passage = RELATIONS["tax"][3].format(a=subject, b=category) + result + "を引き起こす。"
        accepted = model.read_passage(passage, f"省略資料-{index:02d}")
        answer = model.ask(QUERIES["cause"]["direct"][0].format(a=subject))
        correct += int(
            all(ok for ok, _ in accepted)
            and answer.value == result
            and answer.sources == (f"省略資料-{index:02d}:2",)
        )
        feature_reads += model.last_feature_reads
        max_candidates = max(max_candidates, model.last_candidates)

        baseline.read_passage(passage, f"基準資料-{index:02d}")
        baseline_answer = baseline.ask(QUERIES["cause"]["direct"][0].format(a=subject))
        baseline_correct += int(baseline_answer.value == result)

    model.reset_discourse()
    before_unbound = (len(model.facts), len(model.entities))
    unbound = [model.read_discourse_sentence("孤立結果を引き起こす。", f"孤立-{i}") for i in range(10)]
    after_unbound = (len(model.facts), len(model.entities))

    model.read_discourse_sentence(RELATIONS["tax"][3].format(a="未知主題", b="未知分類"), "未知:1")
    before_unknown = (len(model.facts), len(model.entities))
    unknown = [model.read_discourse_sentence("まったく未知の記述である。", f"未知-{i}") for i in range(10)]
    after_unknown = (len(model.facts), len(model.entities))

    blob = model.to_bytes()
    restored = ZeroSubjectLearner.from_bytes(blob)
    elapsed = time.perf_counter() - started
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024

    checks = {
        "zero_subject_60_of_60": correct == 60,
        "baseline_zero_subject_0_of_60": baseline_correct == 0,
        "unbound_10_of_10_abstained": all(not ok for ok, _ in unbound),
        "unbound_preserved_graph": before_unbound == after_unbound,
        "unknown_10_of_10_abstained": all(not ok for ok, _ in unknown),
        "unknown_preserved_graph": before_unknown == after_unknown,
        "round_trip_preserved": restored.report()["zero_subject_resolutions"] == 60,
        "no_additional_state_slots": model.report()["zero_subject_state_slots_added"] == 0,
        "implementation_overhead_at_most_1024_bytes": overhead <= 1024,
        "peak_rss_below_64_mib": peak_rss < 64 * 1024 * 1024,
        "wall_time_below_2_seconds": elapsed < 2.0,
        "max_candidates_at_most_11": max_candidates <= 11,
        "estimated_operations_below_180000": feature_reads < 180000,
    }
    report = {
        "experiment": "SPARC-zero-subject-001",
        "passed": all(checks.values()),
        "checks": checks,
        "metrics": {
            "zero_subject_correct": correct,
            "baseline_zero_subject_correct": baseline_correct,
            "serialized_bytes_after_60_new_facts": len(blob),
            "baseline_initial_serialized_bytes": baseline_bytes,
            "extension_initial_serialized_bytes": extension_initial_bytes,
            "implementation_overhead_bytes": overhead,
            "peak_rss_bytes": peak_rss,
            "wall_seconds": elapsed,
            "max_candidates": max_candidates,
            "feature_reads": feature_reads,
            "estimated_operations": feature_reads,
            "state_slots_added": 0,
        },
        "claim_boundary": (
            "Recovers paragraph-local omitted subjects only when the previous subject plus the fragment uniquely matches an already learned relation template. "
            "It is not unrestricted Japanese ellipsis resolution, ordinary textbook comprehension, or high-school-level intelligence."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "SPARC-zero-subject-001.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    (output_dir / "SPARC-zero-subject-001.model.zlib").write_bytes(blob)
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
