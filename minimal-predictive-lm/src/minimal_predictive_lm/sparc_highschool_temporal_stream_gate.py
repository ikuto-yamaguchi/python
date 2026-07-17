from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_document_stream_gate import _corpus, _orient, _oriented_fact
from .sparc_highschool_general import World
from .sparc_highschool_numeric_stream_gate import _numeric_corpus
from .sparc_highschool_temporal_stream import TemporalNarrativeLearner


def _temporal_corpus():
    return [
        ("箱Aには2個ある。箱Aに3個加える。箱Aには5個ある。", "T1"),
        ("箱Bには4個ある。箱Bに3個加える。箱Bには7個ある。", "T2"),
        ("箱Aには3個ある。箱Aを2倍にする。箱Aには6個ある。", "T3"),
        ("箱Bには5個ある。箱Bを2倍にする。箱Bには10個ある。", "T4"),
        ("試料Aの温度は10度である。試料Aの温度を5度上げる。試料Aの温度は15度である。", "T5"),
        ("試料Bの温度は20度である。試料Bの温度を5度上げる。試料Bの温度は25度である。", "T6"),
    ]


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    learner = TemporalNarrativeLearner()

    training_started = time.perf_counter()
    fact_stream = learner.learn_independent_documents(_corpus(), min_support=4)
    numeric_stream = learner.learn_independent_numeric_documents(_numeric_corpus())
    temporal = learner.learn_chronological_documents(_temporal_corpus())
    training_seconds = time.perf_counter() - training_started

    axes: dict[str, dict[str, int]] = {}
    inference_seconds = 0.0
    total_queries = 0
    max_candidates = 0
    max_feature_reads = 0

    def apply(text: str, world: World):
        nonlocal inference_seconds, total_queries, max_candidates, max_feature_reads
        stamp = time.perf_counter()
        result = learner.apply(text, world)
        inference_seconds += time.perf_counter() - stamp
        total_queries += 1
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        return result

    temporal_correct = (
        int(temporal.documents == 6)
        + int(temporal.transitions_found == 6)
        + int(len(learner.temporal_program_sources) == 3)
        + int(sum(len(sources) for sources in learner.temporal_program_sources.values()) == 6)
    )
    axes["unlabeled_temporal_program_induction"] = {"correct": temporal_correct, "total": 4}

    numeric_world = learner.learned_numeric_world().number_map()
    count_subjects = {"青箱", "赤容器", "大型倉庫", "小型ケース"}
    temperature_subjects = {"試料甲", "検体乙", "素材丙", "サンプル丁"}
    count_relations = {relation for subject, relation in numeric_world if subject in count_subjects}
    temperature_relations = {relation for subject, relation in numeric_world if subject in temperature_subjects}
    count_relation = next(iter(count_relations)) if len(count_relations) == 1 else ""
    temperature_relation = next(iter(temperature_relations)) if len(temperature_relations) == 1 else ""
    axes["independent_numeric_relations"] = {
        "correct": 2 if numeric_stream.relation_clusters == 2 and count_relation and temperature_relation and count_relation != temperature_relation else 0,
        "total": 2,
    }

    event_correct = 0
    for index in range(10, 30):
        subject = f"箱{index}"
        before = learner.observe_world([f"{subject}には{index}個ある"]).world
        added = apply(f"{subject}に3個加える", before)
        doubled = apply(f"{subject}を2倍にする", before)
        event_correct += int(added.accepted and added.world.number_map().get((subject, count_relation)) == index + 3)
        event_correct += int(doubled.accepted and doubled.world.number_map().get((subject, count_relation)) == index * 2)
    axes["chronological_event_transfer"] = {"correct": event_correct, "total": 40}

    causal_correct = 0
    for index in range(20):
        subject = f"試料{index + 30}"
        state = learner.observe_world([f"{subject}の温度は{10 + index}度である"]).world
        state = apply(f"{subject}の温度を5度上げる", state).world
        result = apply(f"{subject}の温度を5度上げる", state)
        causal_correct += int(result.accepted and result.world.number_map().get((subject, temperature_relation)) == 20 + index)
    axes["causal_state_simulation"] = {"correct": causal_correct, "total": 20}

    planning_correct = 0
    planning_expanded = 0
    for index in range(20):
        subject = f"計画箱{index}"
        start = learner.observe_world([f"{subject}には1個ある"]).world
        goal = learner.observe_world([f"{subject}には8個ある"]).world
        stamp = time.perf_counter()
        plan = learner.plan(start, goal, [f"{subject}に3個加える", f"{subject}を2倍にする"], max_depth=3)
        inference_seconds += time.perf_counter() - stamp
        planning_correct += int(plan.found and plan.actions == (f"{subject}に3個加える", f"{subject}を2倍にする"))
        planning_expanded += plan.expanded
    axes["goal_directed_planning"] = {"correct": planning_correct, "total": 20}

    learner.learn_chronological_document("箱Aには5個ある。箱Aから3個取り除く。箱Aには2個ある。", "T7")
    continual_correct = 0
    for index in range(20):
        subject = f"継続箱{index}"
        before = learner.observe_world([f"{subject}には{index + 5}個ある"]).world
        removed = apply(f"{subject}から3個取り除く", before)
        retained = apply(f"{subject}に3個加える", before)
        continual_correct += int(
            removed.accepted and removed.world.number_map().get((subject, count_relation)) == index + 2
            and retained.accepted and retained.world.number_map().get((subject, count_relation)) == index + 8
        )
    axes["continual_program_growth"] = {"correct": continual_correct, "total": 20}

    fact_world = learner.learned_document_world()
    kind_reference = _oriented_fact(fact_world, "水", "物質")
    location_reference = _oriented_fact(fact_world, "東京", "日本")
    fact_correct = int(fact_stream.relation_clusters == 2 and kind_reference is not None and location_reference is not None) * 2
    axes["independent_fact_relations"] = {"correct": fact_correct, "total": 2}

    paraphrase_correct = 0
    paraphrases = [
        ("酸素は気体に分類される", _orient(kind_reference, "酸素", "気体")),
        ("歴史上の鎌倉幕府は政権の仲間に数えられる", _orient(kind_reference, "鎌倉幕府", "政権")),
        ("正方形というものは図形である", _orient(kind_reference, "正方形", "図形")),
        ("銅を分類すると金属だった", _orient(kind_reference, "銅", "金属")),
    ] * 5
    for text, expected in paraphrases:
        result = apply(text, World())
        paraphrase_correct += int(result.accepted and expected in result.world.facts)
    axes["untouched_compositional_paraphrase"] = {"correct": paraphrase_correct, "total": 20}

    explanation_correct = 0
    explanation_samples = []
    for left, right in [("酸素", "気体"), ("鎌倉幕府", "政権"), ("正方形", "図形"), ("銅", "金属")] * 5:
        fact = _orient(kind_reference, left, right)
        stamp = time.perf_counter()
        text = learner.explain(World.from_parts([fact] if fact else []))
        inference_seconds += time.perf_counter() - stamp
        explanation_samples.append(text)
        explanation_correct += int(left in text and right in text and text.endswith("。"))
    axes["free_form_explanation"] = {"correct": explanation_correct, "total": 20}

    unknown_correct = 0
    for text in ["今日はとても静かだ", "この主張を詳しく論証せよ", "未知の規則で変換する"] * 10:
        before = learner.observe_world(["箱Aには2個ある"]).world
        result = apply(text, before)
        unknown_correct += int(not result.accepted and result.world == before)
    axes["unknown_abstention"] = {"correct": unknown_correct, "total": 30}

    dialogue_correct = 0
    for index in range(20):
        subject = f"対話箱{index}"
        state = learner.observe_world([f"{subject}には1個ある"]).world
        for _ in range(4):
            state = apply(f"{subject}に3個加える", state).world
            state = apply(f"{subject}を2倍にする", state).world
        dialogue_correct += int(state.number_map().get((subject, count_relation)) == 106)
    axes["bounded_long_dialogue_state"] = {"correct": dialogue_correct, "total": 20}

    model = learner.report()
    scaffold_keys = [
        "paraphrase_group_labels_supplied", "entity_spans_supplied", "document_relation_labels_supplied",
        "numeric_paraphrase_group_labels_supplied", "numeric_relation_labels_supplied", "numeric_entity_spans_supplied",
        "relation_ids_supplied_by_caller", "grounded_worlds_supplied_by_caller",
        "before_after_worlds_supplied", "event_sentence_labels_supplied", "chronology_labels_supplied",
    ]
    axes["caller_scaffolds_removed"] = {"correct": sum(int(not model[key]) for key in scaffold_keys), "total": len(scaffold_keys)}

    total_correct = sum(row["correct"] for row in axes.values())
    total = sum(row["total"] for row in axes.values())
    percentages = {name: row["correct"] / row["total"] for name, row in axes.items()}
    minimum_axis = min(percentages, key=percentages.get)
    wall = time.perf_counter() - started
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    estimated_ops = max_feature_reads * max(1, total_queries) + planning_expanded * max(1, len(learner.programs))
    structural = (
        all(value >= 0.95 for name, value in percentages.items() if name != "untouched_compositional_paraphrase")
        and percentages["untouched_compositional_paraphrase"] >= 0.50
        and model["serialized_bytes"] <= 131072
        and peak_rss <= 536870912
        and wall <= 8.0
    )
    report = {
        "stage": "SPARC-highschool-general-001-r6-unlabeled-temporal-documents",
        "axes": axes,
        "total_correct": total_correct,
        "total": total,
        "overall_accuracy": total_correct / total,
        "minimum_axis": minimum_axis,
        "minimum_axis_accuracy": percentages[minimum_axis],
        "fact_stream": fact_stream.__dict__,
        "numeric_stream": numeric_stream.__dict__,
        "temporal_stream": temporal.__dict__,
        "model": model,
        "count_relation": count_relation,
        "temperature_relation": temperature_relation,
        "planning_expanded": planning_expanded,
        "peak_rss_bytes": peak_rss,
        "wall_seconds": wall,
        "training_seconds": training_seconds,
        "inference_seconds_total": inference_seconds,
        "mean_inference_seconds": inference_seconds / max(1, total_queries + 60),
        "max_candidates": max_candidates,
        "max_feature_reads": max_feature_reads,
        "estimated_sparse_operations": estimated_ops,
        "free_dialogue_samples": explanation_samples[:4],
        "structural_integration_passed": structural,
        "highschool_level_passed": False,
        "passed": structural,
        "claim_boundary": (
            "Event programs are induced from complete chronological passages without before/after state arguments or event-position labels. "
            "Passages still use a short observation-event-observation structure; unrestricted narrative causality, broad textbooks, and open dialogue remain outside this gate."
        ),
    }
    (output / "SPARC-highschool-general-temporal-stream.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "SPARC-highschool-general-temporal-stream.model.zlib").write_bytes(learner.to_bytes())
    lines = [
        "# SPARC unlabeled temporal-document integrated gate", "",
        f"- structural integration: {structural}",
        f"- overall: {total_correct}/{total} ({report['overall_accuracy']:.2%})",
        f"- minimum axis: {minimum_axis} ({report['minimum_axis_accuracy']:.2%})",
        f"- model bytes: {model['serialized_bytes']}",
        f"- peak RSS: {peak_rss}",
        f"- training seconds: {training_seconds:.6f}",
        f"- mean inference seconds: {report['mean_inference_seconds']:.9f}",
        f"- max candidates / feature reads: {max_candidates} / {max_feature_reads}",
        "", "## Axes",
    ]
    for name, row in axes.items():
        lines.append(f"- {name}: {row['correct']}/{row['total']}")
    lines += ["", "## Claim boundary", report["claim_boundary"]]
    (output / "SPARC-highschool-general-temporal-stream.md").write_text("\n".join(lines), encoding="utf-8")
    if not structural:
        raise SystemExit("temporal stream integration gate failed")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
