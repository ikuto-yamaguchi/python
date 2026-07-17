from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_general import World
from .sparc_highschool_text_observation import TextObservationLearner


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    learner = TextObservationLearner()

    training_started = time.perf_counter()
    fact_relations = [
        learner.learn_fact_observation_group([
            "水は物質である",
            "物質に分類されるものの一つが水だ",
            "水という対象は物質の仲間に入る",
        ]),
        learner.learn_fact_observation_group([
            "鉄というものは金属に分類される",
            "金属の一つとして鉄が知られる",
            "鉄を分類すると金属に入る",
        ]),
        learner.learn_fact_observation_group([
            "歴史上の江戸幕府は一つの政権だった",
            "政権に数えられる組織の例が江戸幕府だ",
            "江戸幕府という幕府は政権の仲間だ",
        ]),
    ]
    count_relation = learner.learn_numeric_observation_group([
        "箱Aには2個ある",
        "2個入っている箱は箱Aだ",
        "箱Aの個数は2である",
    ])
    temperature_relation = learner.learn_numeric_observation_group([
        "試料Aの温度は10度である",
        "10度を示すのは試料Aだ",
        "試料Aは温度10度の状態にある",
    ])
    for text, before, after in [
        ("箱Aに3個加える", "箱Aには2個ある", "箱Aには5個ある"),
        ("箱Bに3個加える", "箱Bには4個ある", "箱Bには7個ある"),
        ("箱Aを2倍にする", "箱Aには3個ある", "箱Aには6個ある"),
        ("箱Bを2倍にする", "箱Bには5個ある", "箱Bには10個ある"),
        ("試料Aの温度を5度上げる", "試料Aの温度は10度である", "試料Aの温度は15度である"),
        ("試料Bの温度を5度上げる", "試料Bの温度は20度である", "試料Bの温度は25度である"),
    ]:
        learner.teach_event_from_text(text, [before], [after])
    training_seconds = time.perf_counter() - training_started

    axes: dict[str, dict[str, int]] = {}
    inference_seconds = 0.0
    total_queries = 0
    max_candidates = 0
    max_feature_reads = 0

    def apply(text: str, world: World):
        nonlocal inference_seconds, total_queries, max_candidates, max_feature_reads
        query_started = time.perf_counter()
        result = learner.apply(text, world)
        inference_seconds += time.perf_counter() - query_started
        total_queries += 1
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
        return result

    clustered = len(set(fact_relations)) == 1 and learner.fact_relation_merges == 2
    axes["autonomous_relation_clustering"] = {"correct": 3 if clustered else 0, "total": 3}

    values = [("酸素", "気体"), ("鎌倉幕府", "政権"), ("正方形", "図形"), ("銅", "金属")]
    learned_surfaces = [
        lambda s, o: f"{s}は{o}である",
        lambda s, o: f"{o}に分類されるものの一つが{s}だ",
        lambda s, o: f"{s}という対象は{o}の仲間に入る",
        lambda s, o: f"{s}というものは{o}に分類される",
        lambda s, o: f"{s}を分類すると{o}に入る",
        lambda s, o: f"歴史上の{s}は一つの{o}だった",
    ]
    correct = 0
    induced_relations = set()
    for index in range(36):
        subject, obj = values[index % len(values)]
        text = learned_surfaces[index % len(learned_surfaces)](subject, obj)
        result = apply(text, World())
        matching = [fact for fact in result.world.facts if fact[0] == subject and fact[2] == obj]
        correct += int(result.accepted and len(matching) == 1)
        induced_relations.update(fact[1] for fact in matching)
    axes["raw_fact_relation_induction"] = {"correct": correct, "total": 36}

    correct = 0
    for index in range(20, 40):
        for text, subject, relation, value in [
            (f"箱{index}には{index}個ある", f"箱{index}", count_relation, index),
            (f"試料{index}の温度は{index}度である", f"試料{index}", temperature_relation, index),
        ]:
            query_started = time.perf_counter()
            result = learner.observe_world([text])
            inference_seconds += time.perf_counter() - query_started
            total_queries += 1
            max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
            correct += int(result.accepted == 1 and result.world.number_map().get((subject, relation)) == value)
    axes["raw_numeric_world_induction"] = {"correct": correct, "total": 40}

    correct = 0
    for index in range(10, 30):
        subject = f"箱{index}"
        for text, expected in [(f"{subject}に3個加える", index + 3), (f"{subject}を2倍にする", index * 2)]:
            before = learner.observe_world([f"{subject}には{index}個ある"]).world
            result = apply(text, before)
            correct += int(result.accepted and result.world.number_map().get((subject, count_relation)) == expected)
    axes["text_only_event_program_transfer"] = {"correct": correct, "total": 40}

    correct = 0
    for index in range(20):
        subject = f"試料{index + 40}"
        world = learner.observe_world([f"{subject}の温度は{10 + index}度である"]).world
        world = apply(f"{subject}の温度を5度上げる", world).world
        result = apply(f"{subject}の温度を5度上げる", world)
        correct += int(result.accepted and result.world.number_map().get((subject, temperature_relation)) == 20 + index)
    axes["causal_state_simulation"] = {"correct": correct, "total": 20}

    planning_correct = 0
    planning_expanded = 0
    for index in range(20):
        subject = f"計画箱{index}"
        start = learner.observe_world([f"{subject}には1個ある"]).world
        goal = learner.observe_world([f"{subject}には8個ある"]).world
        plan_started = time.perf_counter()
        plan = learner.plan(start, goal, [f"{subject}に3個加える", f"{subject}を2倍にする"], max_depth=3)
        inference_seconds += time.perf_counter() - plan_started
        planning_correct += int(plan.found and plan.actions == (f"{subject}に3個加える", f"{subject}を2倍にする"))
        planning_expanded += plan.expanded
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
    axes["goal_directed_planning"] = {"correct": planning_correct, "total": 20}

    learner.teach_event_from_text("箱Aから3個取り除く", ["箱Aには5個ある"], ["箱Aには2個ある"])
    correct = 0
    for index in range(20):
        subject = f"継続箱{index}"
        before = learner.observe_world([f"{subject}には{index + 5}個ある"]).world
        removed = apply(f"{subject}から3個取り除く", before)
        retained = apply(f"{subject}に3個加える", before)
        correct += int(
            removed.accepted and removed.world.number_map().get((subject, count_relation)) == index + 2
            and retained.accepted and retained.world.number_map().get((subject, count_relation)) == index + 8
        )
    axes["continual_program_growth"] = {"correct": correct, "total": 20}

    paraphrases = [
        ("酸素は気体に分類される", "酸素", "気体"),
        ("歴史上の鎌倉幕府は政権の仲間に数えられる", "鎌倉幕府", "政権"),
        ("正方形というものは図形である", "正方形", "図形"),
        ("銅を分類すると金属だった", "銅", "金属"),
    ] * 5
    correct = 0
    for text, subject, obj in paraphrases:
        result = apply(text, World())
        correct += int(result.accepted and any(f[0] == subject and f[2] == obj for f in result.world.facts))
    axes["untouched_paraphrase_transfer"] = {"correct": correct, "total": 20}

    relation = fact_relations[0] if clustered else ""
    explanation_samples = []
    correct = 0
    for subject, obj in values * 5:
        explain_started = time.perf_counter()
        text = learner.explain(World.from_parts([(subject, relation, obj)]))
        inference_seconds += time.perf_counter() - explain_started
        explanation_samples.append(text)
        correct += int(subject in text and obj in text and text.endswith("。"))
    axes["free_form_explanation"] = {"correct": correct, "total": 20}

    correct = 0
    for text in ["今日は静かな雨が降る", "この意見を詳しく論証せよ", "未知の規則で変換する"] * 10:
        before = learner.observe_world(["箱Aには2個ある"]).world
        result = apply(text, before)
        observation = learner.observe_world([text])
        correct += int(not result.accepted and result.world == before and observation.abstained == 1)
    axes["unknown_abstention"] = {"correct": correct, "total": 30}

    correct = 0
    for index in range(20):
        subject = f"対話箱{index}"
        world = learner.observe_world([f"{subject}には1個ある"]).world
        for _ in range(4):
            world = apply(f"{subject}に3個加える", world).world
            world = apply(f"{subject}を2倍にする", world).world
        correct += int(world.number_map().get((subject, count_relation)) == 106)
    axes["bounded_long_dialogue_state"] = {"correct": correct, "total": 20}

    model = learner.report()
    caller_scaffolds = int(not model["relation_ids_supplied_by_caller"]) + int(not model["grounded_worlds_supplied_by_caller"])
    axes["caller_scaffolds_removed"] = {"correct": caller_scaffolds, "total": 2}

    total_correct = sum(row["correct"] for row in axes.values())
    total = sum(row["total"] for row in axes.values())
    percentages = {name: row["correct"] / row["total"] for name, row in axes.items()}
    minimum_axis = min(percentages, key=percentages.get)
    wall = time.perf_counter() - started
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    estimated_ops = max_feature_reads * max(1, total_queries) + planning_expanded * max(1, len(learner.programs))
    structural = (
        all(percentages[name] >= 0.95 for name in [
            "autonomous_relation_clustering", "raw_fact_relation_induction",
            "raw_numeric_world_induction", "text_only_event_program_transfer",
            "causal_state_simulation", "goal_directed_planning",
            "continual_program_growth", "free_form_explanation",
            "unknown_abstention", "bounded_long_dialogue_state",
            "caller_scaffolds_removed",
        ])
        and percentages["untouched_paraphrase_transfer"] >= 0.50
        and model["serialized_bytes"] <= 65536
        and peak_rss <= 536870912
        and wall <= 5.0
    )
    report = {
        "stage": "SPARC-highschool-general-001-r3-text-observation",
        "axes": axes,
        "total_correct": total_correct,
        "total": total,
        "overall_accuracy": total_correct / total,
        "minimum_axis": minimum_axis,
        "minimum_axis_accuracy": percentages[minimum_axis],
        "model": model,
        "opaque_fact_relations": sorted(set(fact_relations)),
        "opaque_numeric_relations": [count_relation, temperature_relation],
        "planning_expanded": planning_expanded,
        "peak_rss_bytes": peak_rss,
        "wall_seconds": wall,
        "training_seconds": training_seconds,
        "inference_seconds_total": inference_seconds,
        "mean_inference_seconds": inference_seconds / max(1, total_queries + 40),
        "max_candidates": max_candidates,
        "max_feature_reads": max_feature_reads,
        "estimated_sparse_operations": estimated_ops,
        "free_dialogue_samples": explanation_samples[:4],
        "structural_integration_passed": structural,
        "highschool_level_passed": False,
        "passed": structural,
        "claim_boundary": (
            "Caller relation IDs and World objects are removed on the text path, and separate raw paraphrase groups are clustered into one opaque relation. "
            "Repeated co-denotation groups and generated corpora remain; ordinary textbooks, broad curriculum, and open dialogue are still outside this gate."
        ),
    }
    (output / "SPARC-highschool-general-text-observation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "SPARC-highschool-general-text-observation.model.zlib").write_bytes(learner.to_bytes())
    lines = [
        "# SPARC high-school general text-observation gate", "",
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
    (output / "SPARC-highschool-general-text-observation.md").write_text("\n".join(lines), encoding="utf-8")
    if not structural:
        raise SystemExit("text-observation integration gate failed")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
