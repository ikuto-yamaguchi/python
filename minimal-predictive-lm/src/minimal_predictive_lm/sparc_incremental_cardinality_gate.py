from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_cardinality_induction import CardinalityInductionLearner
from .sparc_incremental_cardinality import IncrementalCardinalityLearner
from .sparc_open_textbook_gate import RELATIONS, base_training, jpnum, paragraph, train_queries


def train(cls):
    model = cls()
    records, _, chains = base_training()
    model.learn_paragraphs(records)
    evidence = []
    for index in range(8):
        suffix = jpnum(1400 + index)
        evidence.append((paragraph("produce", "工程" + suffix, "生成物" + suffix), f"単値-{index}"))
        part = "共通部品" + suffix
        for side in ("装置甲", "装置乙"):
            evidence.append((paragraph("part", part, side + suffix), f"多値-{index}-{side}"))
    model.learn_paragraphs(evidence)
    model.induce_rules(min_support=6)
    train_queries(model, chains)
    return model


def run_gate(output_dir: Path) -> dict[str, object]:
    started = time.perf_counter()
    model = train(IncrementalCardinalityLearner)
    baseline = train(CardinalityInductionLearner)
    baseline_bytes = len(baseline.to_bytes())
    incremental_initial_bytes = len(model.to_bytes())

    model.cardinality_local_updates = 0
    model.cardinality_rebuilds_avoided = 0
    baseline.cardinality_rebuild_reads = 0

    functional_rejected = 0
    functional_preserved = 0
    multivalue_accepted = 0
    baseline_functional_rejected = 0
    baseline_multivalue_accepted = 0
    feature_reads = 0
    max_candidates = 0

    for index in range(80):
        suffix = jpnum(1500 + index)
        subject = "評価工程" + suffix
        first = "正生成物" + suffix
        second = "誤生成物" + suffix
        sentence1 = RELATIONS["produce"][0].format(a=subject, b=first)
        sentence2 = RELATIONS["produce"][0].format(a=subject, b=second)
        model.read_discourse_sentence(sentence1, f"正-{index}")
        accepted, reason = model.read_discourse_sentence(sentence2, f"誤-{index}")
        relation = model._match_sentence(sentence1)[0][1]
        values = model.out_index.get(subject, {}).get(relation, set())
        functional_rejected += int(not accepted and reason == "abstain-functional-conflict")
        functional_preserved += int(values == {first})
        feature_reads += model.last_feature_reads
        max_candidates = max(max_candidates, model.last_candidates)

        baseline.read_discourse_sentence(sentence1, f"基準正-{index}")
        baccepted, breason = baseline.read_discourse_sentence(sentence2, f"基準誤-{index}")
        baseline_functional_rejected += int(not baccepted and breason == "abstain-functional-conflict")

    for index in range(80):
        suffix = jpnum(1700 + index)
        part = "評価共通部品" + suffix
        left = RELATIONS["part"][3].format(a=part, b="全体甲" + suffix)
        right = RELATIONS["part"][3].format(a=part, b="全体乙" + suffix)
        ok1 = model.read_discourse_sentence(left, f"左-{index}")[0]
        ok2 = model.read_discourse_sentence(right, f"右-{index}")[0]
        multivalue_accepted += int(ok1 and ok2)
        b1 = baseline.read_discourse_sentence(left, f"基準左-{index}")[0]
        b2 = baseline.read_discourse_sentence(right, f"基準右-{index}")[0]
        baseline_multivalue_accepted += int(b1 and b2)

    blob = model.to_bytes()
    restored = IncrementalCardinalityLearner.from_bytes(blob)
    elapsed = time.perf_counter() - started
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    baseline_reads = baseline.cardinality_rebuild_reads
    incremental_reads = model.cardinality_local_updates
    reduction = 1.0 - (incremental_reads / baseline_reads if baseline_reads else 1.0)
    overhead = incremental_initial_bytes - baseline_bytes
    estimated_operations = feature_reads + incremental_reads + model.conflict_checks

    checks = {
        "functional_conflicts_80_of_80_rejected": functional_rejected == 80,
        "functional_prior_80_of_80_preserved": functional_preserved == 80,
        "multivalue_80_of_80_accepted": multivalue_accepted == 80,
        "capability_matches_rebuild_baseline": baseline_functional_rejected == 80 and baseline_multivalue_accepted == 80,
        "online_full_rebuilds_are_zero": model.report()["cardinality_full_rebuilds_after_online_addition"] == 0,
        "rebuild_reads_reduced_by_at_least_95_percent": reduction >= 0.95,
        "save_restore_preserves_incremental_state": restored.cardinality_subjects == model.cardinality_subjects and restored.cardinality_multi_subjects == model.cardinality_multi_subjects,
        "no_additional_discourse_slots": model.report()["incremental_cardinality_state_slots_added"] == 0,
        "implementation_overhead_at_most_2048_bytes": overhead <= 2048,
        "peak_rss_below_64_mib": peak_rss < 64 * 1024 * 1024,
        "wall_time_below_2_seconds": elapsed < 2.0,
        "max_candidates_at_most_11": max_candidates <= 11,
        "estimated_operations_below_90000": estimated_operations < 90000,
    }
    report = {
        "experiment": "SPARC-incremental-cardinality-001",
        "passed": all(checks.values()),
        "checks": checks,
        "metrics": {
            "functional_conflicts_rejected": functional_rejected,
            "functional_prior_preserved": functional_preserved,
            "multivalue_accepted": multivalue_accepted,
            "baseline_functional_conflicts_rejected": baseline_functional_rejected,
            "baseline_multivalue_accepted": baseline_multivalue_accepted,
            "baseline_online_rebuild_reads": baseline_reads,
            "incremental_local_updates": incremental_reads,
            "rebuild_read_reduction": reduction,
            "rebuilds_avoided": model.cardinality_rebuilds_avoided,
            "baseline_initial_serialized_bytes": baseline_bytes,
            "incremental_initial_serialized_bytes": incremental_initial_bytes,
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
            "Preserves induced functional-versus-multivalued relation behavior while replacing every online full-graph cardinality rebuild with a local counter update. "
            "It does not infer truth, temporal revisions, unrestricted textbook semantics, free conversation, or high-school-level intelligence."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "SPARC-incremental-cardinality-001.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "SPARC-incremental-cardinality-001.model.zlib").write_bytes(blob)
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
