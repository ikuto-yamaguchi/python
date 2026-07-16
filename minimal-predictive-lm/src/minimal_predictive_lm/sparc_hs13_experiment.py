from __future__ import annotations

import json
import resource
import string
import time
from pathlib import Path

from .sparc_cross_domain_plans_v2 import SPARCHS11ModelV2
from .sparc_goal_rules import SPARCHS13Model
from .sparc_hs12_experiment_v2 import configured_model as configured_hs12
from .sparc_relational_plans import SPARCHS12Model


def _alpha_code(index: int) -> str:
    alphabet = string.ascii_uppercase
    output: list[str] = []
    value = index
    while True:
        output.append(alphabet[value % 26])
        value = value // 26 - 1
        if value < 0:
            break
    return "".join(reversed(output))


def configured_model() -> SPARCHS13Model:
    model = SPARCHS13Model(configured_hs12())
    animals = ("ツバメ", "ハト", "カラス")
    for animal in animals:
        model.ingest_fact(
            f"{animal}の体温特性は一定である。",
            source_id=f"{animal}直接体温結論",
        )
        model.ingest_fact(
            f"{animal}の生理区分は恒温型である。",
            source_id=f"{animal}直接生理結論",
        )
    model.ingest_fact(
        "一定の代謝分類は恒温型である。", source_id="代謝分類資料"
    )
    rule_temperature = model.teach_rule(
        [
            ("ツバメの体温特性は何ですか？", "一定です"),
            ("ハトの体温特性は何ですか？", "一定です"),
            ("カラスの体温特性は何ですか？", "一定です"),
        ]
    )
    model.link_rule_surface(
        "ツバメは恒温ですか？", "ツバメ", rule_temperature.head_relation, support=3
    )
    model.teach_rule(
        [
            ("ツバメの生理区分は何ですか？", "恒温型です"),
            ("ハトの生理区分は何ですか？", "恒温型です"),
            ("カラスの生理区分は何ですか？", "恒温型です"),
        ]
    )
    return model


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = configured_model()

    model.ingest_fact(
        "ハヤブサの分類は鳥類である。", source_id="ハヤブサ分類資料"
    )
    answers = {
        "conversation": model.reply("こんにちは"),
        "hs12": model.reply("現象Aの最終結果は何ですか？"),
        "derived_head": model.reply("ハヤブサの体温特性は何ですか？"),
        "linked_surface": model.reply("ハヤブサは恒温ですか？"),
        "nested_rule": model.reply("ハヤブサの生理区分は何ですか？"),
    }

    model.ingest_fact("未知生物の分類は鳥類である。", source_id="分類資料1")
    model.ingest_fact("未知生物の分類は爬虫類である。", source_id="分類資料2")
    model.ingest_fact("爬虫類の体温は変温である。", source_id="爬虫類生理資料")
    conflict = model.reply("未知生物の体温特性は何ですか？")
    model.ingest_fact(
        "最新情報:未知生物の分類は鳥類である。",
        source_id="訂正分類資料",
        revision=True,
    )
    revised = model.reply("未知生物の生理区分は何ですか？")

    compact_bytes = model.to_bytes()
    restored = SPARCHS13Model.from_bytes(compact_bytes)
    persistence = restored.reply("ハヤブサの生理区分は何ですか？")
    rule_report = model.goal_rules.report()

    checks = {
        "conversation_retained": answers["conversation"].text.startswith("こんにちは"),
        "hs12_relation_plan_retained": answers["hs12"].text.startswith("結果Aです"),
        "derived_missing_head": (
            answers["derived_head"].text.startswith("一定です")
            and "体温特性(x,z) <- 分類 -> 体温" in answers["derived_head"].text
        ),
        "derived_sources": (
            "ハヤブサ分類資料" in answers["derived_head"].text
            and "鳥類" in answers["derived_head"].text
        ),
        "linked_question_surface": answers["linked_surface"].text.startswith("一定です"),
        "nested_rule_reuse": (
            answers["nested_rule"].text.startswith("恒温型です")
            and "生理区分(x,z) <- 体温特性 -> 代謝分類" in answers["nested_rule"].text
            and "体温特性(x,z) <- 分類 -> 体温" in answers["nested_rule"].text
            and "代謝分類資料" in answers["nested_rule"].text
        ),
        "conflict_refusal": (
            conflict.mechanism == "goal-rule-evidence-conflict"
            and "確定できません" in conflict.text
        ),
        "revision_reenables_nested_rule": revised.text.startswith("恒温型です"),
        "two_induced_rules": rule_report["rules"] == 2,
        "goal_directed_only": rule_report["forward_materialisation_used"] is False,
        "save_load_rules": (
            persistence.text.startswith("恒温型です")
            and restored.goal_rules.report()["rules"] == 2
        ),
        "no_global_scans": (
            rule_report["global_entity_scan_used"] is False
            and rule_report["global_edge_scan_used"] is False
            and rule_report["global_rule_scan_used"] is False
        ),
    }

    scale_start = time.perf_counter()
    large = SPARCHS13Model(SPARCHS12Model(SPARCHS11ModelV2()))
    training_indices = (50_000, 50_001, 50_002)
    for index in training_indices:
        code = _alpha_code(index)
        subject = f"対象{code}"
        group = f"群{code}"
        value = f"帰結{index}"
        large.ingest_fact(
            f"{subject}の分類は{group}である。", source_id=f"訓練分類{code}"
        )
        large.ingest_fact(
            f"{group}の特性は{value}である。", source_id=f"訓練特性{code}"
        )
        large.ingest_fact(
            f"{subject}の最終特性は{value}である。", source_id=f"訓練結論{code}"
        )
    scale_rule = large.teach_rule(
        [
            (
                f"対象{_alpha_code(index)}の最終特性は何ですか？",
                f"帰結{index}です",
            )
            for index in training_indices
        ]
    )

    subject_count = 50_000
    for index in range(subject_count):
        code = _alpha_code(index)
        subject = f"対象{code}"
        group = f"群{code}"
        value = f"帰結{index % 2003}"
        large.ingest_fact(
            f"{subject}の分類は{group}である。", source_id=f"分類資料{code}"
        )
        large.ingest_fact(
            f"{group}の特性は{value}である。", source_id=f"特性資料{code}"
        )

    sample_queries = 512
    correct = 0
    max_rule_candidates = 0
    max_schema_reads = 0
    max_rule_reads = 0
    max_edge_reads = 0
    max_nodes = 0
    max_recursive_goals = 0
    max_operations = 0
    for sample in range(sample_queries):
        index = (sample * 7919) % subject_count
        code = _alpha_code(index)
        reply = large.reply(f"対象{code}の最終特性は何ですか？")
        if reply.text.startswith(f"帰結{index % 2003}です"):
            correct += 1
        max_rule_candidates = max(
            max_rule_candidates, large.goal_rules.last_rule_candidates
        )
        max_schema_reads = max(max_schema_reads, large.goal_rules.last_schema_reads)
        max_rule_reads = max(max_rule_reads, large.goal_rules.last_rule_reads)
        max_edge_reads = max(max_edge_reads, large.goal_rules.last_edge_reads)
        max_nodes = max(max_nodes, large.goal_rules.last_nodes_activated)
        max_recursive_goals = max(
            max_recursive_goals, large.goal_rules.last_recursive_goals
        )
        max_operations = max(max_operations, reply.estimated_sparse_operations)

    large_bytes = large.to_bytes()
    large_report = large.goal_rules.report()
    scale_report = {
        "primary_subjects": subject_count,
        "training_subjects": len(training_indices),
        "episodes": len(large.episodic.episodes),
        "indexed_relation_slots": large.graph.report()["indexed_relation_slots"],
        "rules": large_report["rules"],
        "schemas": large_report["schemas"],
        "sample_queries": sample_queries,
        "correct_queries": correct,
        "max_rule_candidates": max_rule_candidates,
        "max_schema_reads": max_schema_reads,
        "max_rule_reads": max_rule_reads,
        "max_edge_reads": max_edge_reads,
        "max_nodes_activated": max_nodes,
        "max_recursive_goals": max_recursive_goals,
        "max_estimated_operations": max_operations,
        "rule_body_hops": len(scale_rule.body_relations),
        "induction_states": large.goal_rules.last_induction_states,
        "serialized_bytes": len(large_bytes),
        "build_and_query_seconds": time.perf_counter() - scale_start,
        "forward_materialisation_used": False,
        "global_entity_scan_used": False,
        "global_edge_scan_used": False,
        "global_rule_scan_used": False,
    }

    result: dict[str, object] = {
        "capability_id": "SPARC-HS13-GOAL-DIRECTED-RULE-INDUCTION",
        "transformer_used": False,
        "softmax_attention_used": False,
        "growing_kv_cache_used": False,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "answers": {
            key: {"text": value.text, "mechanism": value.mechanism}
            for key, value in answers.items()
        },
        "conflict": {"text": conflict.text, "mechanism": conflict.mechanism},
        "revised": {"text": revised.text, "mechanism": revised.mechanism},
        "compact_model": model.report(),
        "large_goal_rule_memory": scale_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS13 induces chain-shaped Horn-style rules from redundant source-grounded "
            "conclusions and executes them goal-first. It does not learn arbitrary logical "
            "forms, quantifiers, theorem proofs or open-ended research strategies and is "
            "not Japanese high-school-level general intelligence."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and correct == sample_queries
        and scale_report["episodes"] == 100_009
        and scale_report["indexed_relation_slots"] == 100_009
        and scale_report["rules"] == 1
        and scale_report["schemas"] == 1
        and scale_report["rule_body_hops"] == 2
        and max_rule_candidates <= 1
        and max_schema_reads <= 16
        and max_rule_reads <= 1
        and max_edge_reads <= 2
        and max_nodes <= 4
        and max_recursive_goals <= 3
        and max_operations <= 32
        and len(large_bytes) <= 10_000_000
        and result["peak_process_kib"] <= 1_200_000
        and result["elapsed_seconds"] <= 120.0
    )

    (output_dir / "sparc_hs13_goal_rules.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-HS13-compact.model.zlib").write_bytes(compact_bytes)
    (output_dir / "SPARC-HS13-goal-rules-large.model.zlib").write_bytes(large_bytes)
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
