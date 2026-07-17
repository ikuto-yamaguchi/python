from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_cardinality_induction import CardinalityInductionLearner
from .sparc_conflict_guard import ConflictGuardLearner
from .sparc_open_textbook_gate import RELATIONS, base_training, jpnum, paragraph, train_queries


def train(cls):
    model = cls()
    records, _, chains = base_training()
    model.learn_paragraphs(records)
    cardinality_records = []
    for index in range(8):
        suffix = jpnum(1100 + index)
        cardinality_records.append(
            (paragraph("produce", "生産工程" + suffix, "生成物" + suffix), f"単値根拠-{index}")
        )
        part = "共通部品" + suffix
        for side in ("左装置", "右装置"):
            cardinality_records.append(
                (paragraph("part", part, side + suffix), f"多値根拠-{index}-{side}")
            )
    model.learn_paragraphs(cardinality_records)
    model.induce_rules(min_support=6)
    train_queries(model, chains)
    return model


def run_gate(output_dir: Path) -> dict[str, object]:
    started = time.perf_counter()
    model = train(CardinalityInductionLearner)
    baseline = train(ConflictGuardLearner)
    baseline_bytes = len(baseline.to_bytes())
    adaptive_initial_bytes = len(model.to_bytes())

    functional_probe = model._match_sentence(
        RELATIONS["produce"][0].format(a="判定工程", b="判定生成物")
    )[0][1]
    part_probe = model._match_sentence(
        RELATIONS["part"][3].format(a="判定部品", b="判定全体")
    )[0][1]

    functional_conflicts_rejected = 0
    functional_prior_preserved = 0
    legitimate_multi_accepted = 0
    old_guard_false_rejections = 0
    feature_reads = 0
    max_candidates = 0

    for index in range(40):
        suffix = jpnum(1200 + index)
        subject = "評価工程" + suffix
        first = "正生成物" + suffix
        second = "誤生成物" + suffix
        sentence1 = RELATIONS["produce"][0].format(a=subject, b=first)
        sentence2 = RELATIONS["produce"][0].format(a=subject, b=second)
        model.read_discourse_sentence(sentence1, f"生成正-{index}")
        accepted, reason = model.read_discourse_sentence(sentence2, f"生成誤-{index}")
        relation = model._match_sentence(sentence1)[0][1]
        values = model.out_index.get(subject, {}).get(relation, set())
        functional_conflicts_rejected += int(
            not accepted and reason == "abstain-functional-conflict"
        )
        functional_prior_preserved += int(values == {first})
        feature_reads += model.last_feature_reads
        max_candidates = max(max_candidates, model.last_candidates)

    for index in range(40):
        suffix = jpnum(1300 + index)
        part = "評価共通部品" + suffix
        whole_left = "評価全体甲" + suffix
        whole_right = "評価全体乙" + suffix
        first = RELATIONS["part"][3].format(a=part, b=whole_left)
        second = RELATIONS["part"][3].format(a=part, b=whole_right)

        ok1, _ = model.read_discourse_sentence(first, f"多値左-{index}")
        ok2, _ = model.read_discourse_sentence(second, f"多値右-{index}")
        relation = model._match_sentence(first)[0][1]
        values = model.out_index.get(part, {}).get(relation, set())
        legitimate_multi_accepted += int(ok1 and ok2 and values == {whole_left, whole_right})

        baseline_relation = baseline._match_sentence(first)[0][1]
        base_first, _ = baseline.read_discourse_sentence(first, f"基準左-{index}")
        base_second, _ = baseline.read_discourse_sentence(second, f"基準右-{index}")
        baseline_values = baseline.out_index.get(part, {}).get(baseline_relation, set())
        old_guard_false_rejections += int(
            base_first and not base_second and baseline_values == {whole_left}
        )

    blob = model.to_bytes()
    restored = CardinalityInductionLearner.from_bytes(blob)
    elapsed = time.perf_counter() - started
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    overhead = adaptive_initial_bytes - baseline_bytes
    estimated_operations = feature_reads + model.cardinality_rebuild_reads + model.conflict_checks

    checks = {
        "functional_relation_induced_without_name": functional_probe in model.functional_relations,
        "multivalued_relation_induced_without_name": part_probe in model.nonfunctional_relations,
        "functional_conflicts_40_of_40_rejected": functional_conflicts_rejected == 40,
        "functional_prior_40_of_40_preserved": functional_prior_preserved == 40,
        "legitimate_multivalue_40_of_40_accepted": legitimate_multi_accepted == 40,
        "previous_guard_false_rejections_40_of_40": old_guard_false_rejections == 40,
        "save_restore_preserves_cardinality": (
            functional_probe in restored.functional_relations
            and part_probe in restored.nonfunctional_relations
        ),
        "no_supplied_relation_cardinalities": model.report()["relation_cardinalities_supplied"] is False,
        "no_additional_discourse_slots": model.report()["cardinality_state_slots_added"] == 0,
        "implementation_overhead_at_most_2048_bytes": overhead <= 2048,
        "peak_rss_below_64_mib": peak_rss < 64 * 1024 * 1024,
        "wall_time_below_2_seconds": elapsed < 2.0,
        "max_candidates_at_most_11": max_candidates <= 11,
        "estimated_operations_below_150000": estimated_operations < 150000,
    }
    report = {
        "experiment": "SPARC-cardinality-induction-001",
        "passed": all(checks.values()),
        "checks": checks,
        "metrics": {
            "functional_conflicts_rejected": functional_conflicts_rejected,
            "functional_prior_preserved": functional_prior_preserved,
            "legitimate_multivalue_accepted": legitimate_multi_accepted,
            "old_guard_false_rejections": old_guard_false_rejections,
            "functional_relations_induced": len(model.functional_relations),
            "nonfunctional_relations_induced": len(model.nonfunctional_relations),
            "baseline_initial_serialized_bytes": baseline_bytes,
            "adaptive_initial_serialized_bytes": adaptive_initial_bytes,
            "implementation_overhead_bytes": overhead,
            "serialized_bytes_after_evaluation": len(blob),
            "peak_rss_bytes": peak_rss,
            "wall_seconds": elapsed,
            "max_candidates": max_candidates,
            "query_feature_reads": feature_reads,
            "cardinality_rebuild_reads": model.cardinality_rebuild_reads,
            "conflict_checks": model.conflict_checks,
            "estimated_operations": estimated_operations,
            "state_slots_added": 0,
        },
        "claim_boundary": (
            "Infers whether an anonymous relation behaves functionally or permits several objects from observed graph cardinality, then applies contradiction guarding only to supported functional relations. "
            "It does not decide source truth, model temporal change, understand unrestricted textbooks, or establish high-school-level intelligence."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "SPARC-cardinality-induction-001.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-cardinality-induction-001.model.zlib").write_bytes(blob)
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
