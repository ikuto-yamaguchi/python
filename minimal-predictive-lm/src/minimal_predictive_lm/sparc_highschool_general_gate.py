from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_highschool_general import SparseGeneralLearner, World


def _world(*facts, numbers=None):
    return World.from_parts(facts, numbers or {})


def run_gate(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    learner = SparseGeneralLearner()

    training_started = time.perf_counter()
    fact_train = [
        ("水は物質である", ("水", "R-kind", "物質")),
        ("鉄というものは金属に分類される", ("鉄", "R-kind", "金属")),
        ("歴史上の江戸幕府は一つの政権だった", ("江戸幕府", "R-kind", "政権")),
        ("三角形は図形の仲間に数えられる", ("三角形", "R-kind", "図形")),
        ("哺乳類を分類すると動物に入る", ("哺乳類", "R-kind", "動物")),
    ]
    for text, fact in fact_train:
        learner.teach(text, _world(), _world(fact))
    for text, subject, old, new in [
        ("箱Aに3個加える", "箱A", 2, 5),
        ("箱Bに3個加える", "箱B", 4, 7),
    ]:
        learner.teach(text, _world(numbers={(subject, "count"): old}), _world(numbers={(subject, "count"): new}))
    for text, subject, old, new in [
        ("箱Aを2倍にする", "箱A", 3, 6),
        ("箱Bを2倍にする", "箱B", 5, 10),
    ]:
        learner.teach(text, _world(numbers={(subject, "count"): old}), _world(numbers={(subject, "count"): new}))
    for text, subject, old, new in [
        ("試料Aの温度を5度上げる", "試料A", 10, 15),
        ("試料Bの温度を5度上げる", "試料B", 20, 25),
    ]:
        learner.teach(text, _world(numbers={(subject, "temperature"): old}), _world(numbers={(subject, "temperature"): new}))
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

    fact_cases = [
        ("酸素は気体である", ("酸素", "R-kind", "気体")),
        ("鎌倉幕府は政権である", ("鎌倉幕府", "R-kind", "政権")),
        ("正方形は図形である", ("正方形", "R-kind", "図形")),
        ("銅は金属である", ("銅", "R-kind", "金属")),
    ] * 10
    correct = 0
    for text, expected in fact_cases:
        result = apply(text, _world())
        correct += int(result.accepted and expected in result.world.facts)
    axes["cross_domain_fact_transfer"] = {"correct": correct, "total": len(fact_cases)}

    numeric_cases = [(f"箱{index}に3個加える", f"箱{index}", index, index + 3) for index in range(10, 30)]
    numeric_cases += [(f"箱{index}を2倍にする", f"箱{index}", index, index * 2) for index in range(10, 30)]
    correct = 0
    for text, subject, old, expected in numeric_cases:
        result = apply(text, _world(numbers={(subject, "count"): old}))
        correct += int(result.accepted and result.world.number_map().get((subject, "count")) == expected)
    axes["numeric_program_transfer"] = {"correct": correct, "total": len(numeric_cases)}

    causal_correct = 0
    for index in range(20):
        subject = f"試料{index + 20}"
        world = _world(numbers={(subject, "temperature"): 10 + index})
        first = apply(f"{subject}の温度を5度上げる", world)
        second = apply(f"{subject}の温度を5度上げる", first.world)
        causal_correct += int(second.accepted and second.world.number_map()[(subject, "temperature")] == 20 + index)
    axes["causal_state_simulation"] = {"correct": causal_correct, "total": 20}

    planning_correct = 0
    planning_expanded = 0
    for index in range(20):
        subject = f"計画箱{index}"
        start = _world(numbers={(subject, "count"): 1})
        goal = _world(numbers={(subject, "count"): 8})
        plan_started = time.perf_counter()
        plan = learner.plan(start, goal, [f"{subject}に3個加える", f"{subject}を2倍にする"], max_depth=3)
        inference_seconds += time.perf_counter() - plan_started
        planning_correct += int(plan.found and plan.actions == (f"{subject}に3個加える", f"{subject}を2倍にする"))
        planning_expanded += plan.expanded
        max_candidates = max(max_candidates, learner.last_candidates)
        max_feature_reads = max(max_feature_reads, learner.last_feature_reads)
    axes["goal_directed_planning"] = {"correct": planning_correct, "total": 20}

    learner.teach("水から物質という分類を外す", _world(("水", "R-kind", "物質")), _world())
    continual_correct = 0
    for index in range(20):
        subject = f"対象{index}"
        initial = _world((subject, "R-kind", "分類"))
        removed = apply(f"{subject}から分類という分類を外す", initial)
        retained = apply(f"箱継続{index}に3個加える", _world(numbers={(f"箱継続{index}", "count"): index}))
        continual_correct += int(removed.accepted and not removed.world.facts and retained.accepted)
    axes["continual_program_growth"] = {"correct": continual_correct, "total": 20}

    unknown_correct = 0
    for text in ["今日は静かな雨が降る", "この意見を詳しく論証せよ", "未知の規則で変換する"] * 10:
        before = _world(("保持", "R", "知識"))
        result = apply(text, before)
        unknown_correct += int(not result.accepted and result.world == before)
    axes["unknown_abstention"] = {"correct": unknown_correct, "total": 30}

    paraphrases = [
        ("酸素は気体に分類される", ("酸素", "R-kind", "気体")),
        ("歴史上の鎌倉幕府は政権の仲間に数えられる", ("鎌倉幕府", "R-kind", "政権")),
        ("正方形というものは図形である", ("正方形", "R-kind", "図形")),
        ("銅を分類すると金属だった", ("銅", "R-kind", "金属")),
    ] * 5
    paraphrase_correct = 0
    paraphrase_mechanisms: dict[str, int] = {}
    for text, expected in paraphrases:
        result = apply(text, _world())
        paraphrase_mechanisms[result.mechanism] = paraphrase_mechanisms.get(result.mechanism, 0) + 1
        paraphrase_correct += int(result.accepted and expected in result.world.facts)
    axes["untouched_paraphrase_transfer"] = {"correct": paraphrase_correct, "total": len(paraphrases)}

    explanation_cases = [
        (("酸素", "R-kind", "気体"), ("酸素", "気体")),
        (("鎌倉幕府", "R-kind", "政権"), ("鎌倉幕府", "政権")),
        (("正方形", "R-kind", "図形"), ("正方形", "図形")),
        (("銅", "R-kind", "金属"), ("銅", "金属")),
    ] * 5
    explanation_correct = 0
    explanation_samples: list[str] = []
    for fact, required in explanation_cases:
        explain_started = time.perf_counter()
        text = learner.explain(_world(fact))
        inference_seconds += time.perf_counter() - explain_started
        explanation_samples.append(text)
        explanation_correct += int(all(token in text for token in required) and text.endswith("。"))
    axes["free_form_explanation"] = {"correct": explanation_correct, "total": len(explanation_cases)}

    dialogue_correct = 0
    for index in range(20):
        subject = f"対話箱{index}"
        world = _world(numbers={(subject, "count"): 1})
        for _ in range(4):
            world = apply(f"{subject}に3個加える", world).world
            world = apply(f"{subject}を2倍にする", world).world
        dialogue_correct += int(world.number_map()[(subject, "count")] == 106)
    axes["bounded_long_dialogue_state"] = {"correct": dialogue_correct, "total": 20}

    total_correct = sum(row["correct"] for row in axes.values())
    total = sum(row["total"] for row in axes.values())
    percentages = {name: row["correct"] / row["total"] for name, row in axes.items()}
    minimum_axis = min(percentages, key=percentages.get)
    (output / "SPARC-highschool-general-001.model.zlib").write_bytes(learner.to_bytes())
    wall = time.perf_counter() - started
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    model_report = learner.report()
    estimated_ops = max_feature_reads * max(1, total_queries) + planning_expanded * len(learner.programs)
    structural = (
        all(percentages[name] >= 0.95 for name in [
            "cross_domain_fact_transfer", "numeric_program_transfer", "causal_state_simulation",
            "goal_directed_planning", "continual_program_growth", "unknown_abstention",
            "free_form_explanation", "bounded_long_dialogue_state",
        ])
        and percentages["untouched_paraphrase_transfer"] >= 0.50
        and total_correct / total > 190 / 230
        and model_report["serialized_bytes"] <= 65536
        and peak_rss <= 536870912
        and wall <= 5.0
    )
    highschool = total_correct / total >= 0.80 and min(percentages.values()) >= 0.60
    report = {
        "stage": "SPARC-highschool-general-001-r2",
        "axes": axes,
        "total_correct": total_correct,
        "total": total,
        "overall_accuracy": total_correct / total,
        "minimum_axis": minimum_axis,
        "minimum_axis_accuracy": percentages[minimum_axis],
        "planning_expanded": planning_expanded,
        "model": model_report,
        "peak_rss_bytes": peak_rss,
        "wall_seconds": wall,
        "training_seconds": training_seconds,
        "inference_seconds_total": inference_seconds,
        "mean_inference_seconds": inference_seconds / max(1, total_queries + len(explanation_cases) + 20),
        "max_candidates": max_candidates,
        "max_feature_reads": max_feature_reads,
        "estimated_sparse_operations": estimated_ops,
        "paraphrase_mechanisms": paraphrase_mechanisms,
        "free_dialogue_samples": explanation_samples[:4],
        "structural_integration_passed": structural,
        "highschool_level_passed": highschool,
        "claim_boundary": (
            "Bidirectional surface schemas now compose learned fragments and verbalize facts, but training still receives grounded before/after worlds and relation identifiers. "
            "The gate remains synthetic and does not establish Japanese high-school-level general intelligence."
        ),
        "passed": structural,
    }
    (output / "SPARC-highschool-general-001.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# SPARC high-school general integrated gate r2", "",
        f"- structural integration: {structural}",
        f"- high-school level: {highschool}",
        f"- overall: {total_correct}/{total} ({report['overall_accuracy']:.2%})",
        f"- minimum axis: {minimum_axis} ({report['minimum_axis_accuracy']:.2%})",
        f"- model bytes: {model_report['serialized_bytes']}",
        f"- peak RSS: {peak_rss}",
        f"- training seconds: {training_seconds:.6f}",
        f"- mean inference seconds: {report['mean_inference_seconds']:.9f}",
        f"- max candidates / feature reads: {max_candidates} / {max_feature_reads}",
        f"- estimated sparse operations: {estimated_ops}", "", "## Axes",
    ]
    for name, row in axes.items():
        lines.append(f"- {name}: {row['correct']}/{row['total']}")
    lines += ["", "## Claim boundary", report["claim_boundary"]]
    (output / "SPARC-highschool-general-001.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="artifacts/sparc-highschool-general-001")
    args = parser.parse_args()
    print(json.dumps(run_gate(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
