from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_discourse_focus import DiscourseFocusLearner
from .sparc_open_textbook_learner import OpenTextbookLearner
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
    model = train(DiscourseFocusLearner)
    baseline = train(OpenTextbookLearner)
    baseline_bytes = len(baseline.to_bytes())

    subject_correct = 0
    object_correct = 0
    baseline_subject_correct = 0
    feature_reads = 0
    candidates = 0

    for index in range(50):
        suffix = jpnum(500 + index)
        subject = "談話主題" + suffix
        category = "談話分類" + suffix
        result = "談話結果" + suffix
        passage = (
            RELATIONS["tax"][3].format(a=subject, b=category)
            + "これは" + result + "を引き起こす。"
        )
        accepted = model.read_passage(passage, f"主語資料-{index:02d}")
        answer = model.ask(QUERIES["cause"]["direct"][0].format(a=subject))
        subject_correct += int(
            all(ok for ok, _ in accepted)
            and answer.value == result
            and answer.sources == (f"主語資料-{index:02d}:2",)
        )
        feature_reads += model.last_feature_reads
        candidates = max(candidates, model.last_candidates)

        baseline.read_sentence(RELATIONS["tax"][3].format(a=subject, b=category), f"基準-{index}:1")
        baseline.read_sentence("これは" + result + "を引き起こす。", f"基準-{index}:2")
        baseline_answer = baseline.ask(QUERIES["cause"]["direct"][0].format(a=subject))
        baseline_subject_correct += int(baseline_answer.value == result)

    for index in range(50):
        suffix = jpnum(600 + index)
        part = "談話部品" + suffix
        whole = "談話全体" + suffix
        place = "談話場所" + suffix
        passage = (
            RELATIONS["part"][3].format(a=part, b=whole)
            + "その対象は" + place + "に位置する。"
        )
        accepted = model.read_passage(passage, f"目的語資料-{index:02d}")
        answer = model.ask(QUERIES["loc"]["direct"][0].format(a=whole))
        object_correct += int(
            all(ok for ok, _ in accepted)
            and answer.value == place
            and answer.sources == (f"目的語資料-{index:02d}:2",)
        )
        feature_reads += model.last_feature_reads
        candidates = max(candidates, model.last_candidates)

    before_unknown = (len(model.facts), len(model.entities))
    unknown = [model.read_discourse_sentence("これは未知結果を引き起こす。", f"未知-{i}") for i in range(10)]
    after_unknown = (len(model.facts), len(model.entities))

    blob = model.to_bytes()
    restored = DiscourseFocusLearner.from_bytes(blob)
    elapsed = time.perf_counter() - started
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    estimated_operations = feature_reads

    checks = {
        "subject_anaphora_50_of_50": subject_correct == 50,
        "object_anaphora_50_of_50": object_correct == 50,
        "baseline_cannot_bind_subject": baseline_subject_correct == 0,
        "unbound_anaphora_10_of_10_abstained": all(not ok and mechanism.startswith("abstain-unbound") for ok, mechanism in unknown),
        "unknown_input_preserved_graph": before_unknown == after_unknown,
        "round_trip_preserved": restored.report()["discourse_resolutions"] == 100,
        "two_state_slots_only": model.report()["discourse_state_slots"] == 2,
        "model_growth_at_most_1024_bytes": len(blob) <= baseline_bytes + 1024,
        "peak_rss_below_64_mib": peak_rss < 64 * 1024 * 1024,
        "wall_time_below_2_seconds": elapsed < 2.0,
        "max_candidates_at_most_11": candidates <= 11,
        "estimated_operations_below_120000": estimated_operations < 120000,
    }
    report = {
        "experiment": "SPARC-discourse-focus-001",
        "passed": all(checks.values()),
        "checks": checks,
        "metrics": {
            "subject_anaphora_correct": subject_correct,
            "object_anaphora_correct": object_correct,
            "baseline_subject_anaphora_correct": baseline_subject_correct,
            "serialized_bytes": len(blob),
            "baseline_serialized_bytes": baseline_bytes,
            "model_growth_bytes": len(blob) - baseline_bytes,
            "peak_rss_bytes": peak_rss,
            "wall_seconds": elapsed,
            "max_candidates": candidates,
            "feature_reads": feature_reads,
            "estimated_operations": estimated_operations,
            "discourse_state_slots": 2,
        },
        "claim_boundary": (
            "Resolves paragraph-local Japanese demonstrative subjects and objects using two focus slots. "
            "It does not establish unrestricted coreference, ellipsis recovery, or high-school-level intelligence."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "SPARC-discourse-focus-001.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    (output_dir / "SPARC-discourse-focus-001.model.zlib").write_bytes(blob)
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
