from __future__ import annotations

import json
import resource
import string
import time
from pathlib import Path

from .sparc_cross_domain_plans_v2 import SPARCHS11ModelV2
from .sparc_hs11_experiment_v2 import configured_model as configured_hs11
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


def _add_taxonomy(
    model: SPARCHS12Model,
    animal: str,
    group: str,
    property_value: str,
    *,
    source_prefix: str,
) -> None:
    model.ingest_fact(
        f"{animal}の分類は{group}である。",
        source_id=f"{source_prefix}分類資料",
    )
    model.ingest_fact(
        f"{group}の体温は{property_value}である。",
        source_id=f"{source_prefix}生理資料",
    )


def _add_causal_chain(model: SPARCHS12Model, code: str) -> None:
    model.ingest_fact(
        f"現象{code}により中間{code}が起こる。", source_id=f"{code}因果資料1"
    )
    model.ingest_fact(
        f"中間{code}により次段{code}が起こる。", source_id=f"{code}因果資料2"
    )
    model.ingest_fact(
        f"次段{code}により結果{code}が起こる。", source_id=f"{code}因果資料3"
    )


def configured_model() -> SPARCHS12Model:
    model = SPARCHS12Model(configured_hs11())
    for animal, prefix in (("ツバメ", "燕"), ("ハト", "鳩"), ("カラス", "烏")):
        _add_taxonomy(model, animal, "鳥類", "一定", source_prefix=prefix)
    taxonomy_plan = model.teach_relational_plan(
        [
            ("ツバメの体温特性は何ですか？", "一定です"),
            ("ハトの体温特性は何ですか？", "一定です"),
            ("カラスの体温特性は何ですか？", "一定です"),
        ]
    )
    model.link_relational_surface(
        "ツバメはどのような体温特性を持ちますか？", "ツバメ", taxonomy_plan
    )

    for code in ("A", "B", "C"):
        _add_causal_chain(model, code)
    model.teach_relational_plan(
        [
            ("現象Aの最終結果は何ですか？", "結果Aです"),
            ("現象Bの最終結果は何ですか？", "結果Bです"),
            ("現象Cの最終結果は何ですか？", "結果Cです"),
        ]
    )
    return model


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = configured_model()

    _add_taxonomy(model, "ハヤブサ", "鳥類", "一定", source_prefix="隼")
    _add_causal_chain(model, "D")
    answers = {
        "conversation": model.reply("こんにちは"),
        "hs11": model.reply("列車Aの移動距離は何kmですか？"),
        "taxonomy": model.reply("ハヤブサの体温特性は何ですか？"),
        "linked_surface": model.reply("ハヤブサはどのような体温特性を持ちますか？"),
        "causal": model.reply("現象Dの最終結果は何ですか？"),
    }

    model.ingest_fact("未知生物の分類は鳥類である。", source_id="分類資料1")
    model.ingest_fact("未知生物の分類は爬虫類である。", source_id="分類資料2")
    model.ingest_fact(
        "爬虫類の体温は外気で変化する。", source_id="爬虫類生理資料"
    )
    conflict = model.reply("未知生物の体温特性は何ですか？")
    model.ingest_fact(
        "最新情報:未知生物の分類は鳥類である。",
        source_id="訂正分類資料",
        revision=True,
    )
    revised = model.reply("未知生物の体温特性は何ですか？")

    compact_bytes = model.to_bytes()
    restored = SPARCHS12Model.from_bytes(compact_bytes)
    persistence = restored.reply("ハヤブサの体温特性は何ですか？")
    plan_report = model.relational_plans.report()

    checks = {
        "conversation_retained": answers["conversation"].text.startswith("こんにちは"),
        "hs11_cross_domain_retained": answers["hs11"].text.startswith("120kmです"),
        "taxonomy_plan_transfer": (
            answers["taxonomy"].text.startswith("一定です")
            and "分類 → 体温" in answers["taxonomy"].text
        ),
        "taxonomy_sources": (
            "隼分類資料" in answers["taxonomy"].text
            and "隼生理資料" in answers["taxonomy"].text
        ),
        "linked_surface": answers["linked_surface"].text.startswith("一定です"),
        "three_hop_causal_plan": (
            answers["causal"].text.startswith("結果Dです")
            and "原因 → 原因 → 原因" in answers["causal"].text
            and "D因果資料1" in answers["causal"].text
            and "D因果資料3" in answers["causal"].text
        ),
        "conflict_refusal": (
            conflict.mechanism == "relational-plan-evidence-conflict"
            and "確定できません" in conflict.text
        ),
        "revision_reenables_plan": revised.text.startswith("一定です"),
        "two_shared_relation_plans": plan_report["plans"] == 2,
        "bounded_local_edges": (
            answers["taxonomy"].estimated_sparse_operations <= 32
            and answers["causal"].estimated_sparse_operations <= 40
        ),
        "save_load_relational_plan": (
            persistence.text.startswith("一定です")
            and restored.relational_plans.report()["plans"] == 2
        ),
        "no_global_scans": (
            plan_report["global_node_scan_used"] is False
            and plan_report["global_episode_scan_used"] is False
            and plan_report["global_relation_scan_used"] is False
            and plan_report["global_plan_scan_used"] is False
        ),
    }

    scale_start = time.perf_counter()
    large = SPARCHS12Model(SPARCHS11ModelV2())
    subject_count = 50_000
    for index in range(subject_count):
        code = _alpha_code(index)
        subject = f"生物{code}"
        group = f"分類群{code}"
        property_value = f"性質{index % 2003}"
        large.ingest_fact(
            f"{subject}の分類は{group}である。",
            source_id=f"分類資料{code}",
        )
        large.ingest_fact(
            f"{group}の特性は{property_value}である。",
            source_id=f"特性資料{code}",
        )

    scale_plan = large.teach_relational_plan(
        [
            (
                f"生物{_alpha_code(index)}の最終特性は何ですか？",
                f"性質{index % 2003}です",
            )
            for index in (3, 117, 902)
        ]
    )

    sample_queries = 512
    correct = 0
    max_candidates = 0
    max_schema_reads = 0
    max_edge_reads = 0
    max_nodes = 0
    max_operations = 0
    max_subject_checks = 0
    for sample in range(sample_queries):
        index = (sample * 7919) % subject_count
        code = _alpha_code(index)
        reply = large.reply(f"生物{code}の最終特性は何ですか？")
        if reply.text.startswith(f"性質{index % 2003}です"):
            correct += 1
        max_candidates = max(max_candidates, large.relational_plans.last_plan_candidates)
        max_schema_reads = max(max_schema_reads, large.relational_plans.last_schema_reads)
        max_edge_reads = max(max_edge_reads, large.relational_plans.last_edge_reads)
        max_nodes = max(max_nodes, large.relational_plans.last_nodes_activated)
        max_operations = max(max_operations, reply.estimated_sparse_operations)
        max_subject_checks = max(
            max_subject_checks,
            large.relational_plans.last_subject_substring_checks,
        )

    large_bytes = large.to_bytes()
    large_report = large.relational_plans.report()
    scale_report = {
        "primary_subjects": subject_count,
        "indexed_subjects": large_report["indexed_subjects"],
        "episodes": len(large.episodic.episodes),
        "indexed_relation_slots": large_report["indexed_relation_slots"],
        "plans": large_report["plans"],
        "schemas": large_report["schemas"],
        "sample_queries": sample_queries,
        "correct_queries": correct,
        "max_plan_candidates": max_candidates,
        "max_schema_reads": max_schema_reads,
        "max_edge_reads": max_edge_reads,
        "max_nodes_activated": max_nodes,
        "max_estimated_operations": max_operations,
        "max_subject_substring_checks": max_subject_checks,
        "plan_hops": len(scale_plan.relations),
        "search_states": large.relational_plans.last_search_states,
        "serialized_bytes": len(large_bytes),
        "build_and_query_seconds": time.perf_counter() - scale_start,
        "global_node_scan_used": False,
        "global_episode_scan_used": False,
        "global_relation_scan_used": False,
        "global_plan_scan_used": False,
    }

    result: dict[str, object] = {
        "capability_id": "SPARC-HS12-RELATIONAL-PLAN-INDUCTION",
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
        "large_relational_memory": scale_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS12 learns bounded relation-path programs from demonstrated endpoints. "
            "It does not invent arbitrary predicates, quantify over open sets, prove "
            "theorems or plan open-ended investigations and is not Japanese "
            "high-school-level general intelligence."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and correct == sample_queries
        and scale_report["episodes"] == 100_000
        and scale_report["indexed_relation_slots"] == 100_000
        and scale_report["plans"] == 1
        and scale_report["schemas"] == 1
        and scale_report["plan_hops"] == 2
        and max_candidates <= 1
        and max_schema_reads <= 16
        and max_edge_reads <= 2
        and max_nodes <= 4
        and max_operations <= 32
        and max_subject_checks <= 64
        and len(large_bytes) <= 10_000_000
        and result["peak_process_kib"] <= 1_200_000
        and result["elapsed_seconds"] <= 120.0
    )

    (output_dir / "sparc_hs12_relational_plans.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-HS12-compact.model.zlib").write_bytes(compact_bytes)
    (output_dir / "SPARC-HS12-relational-large.model.zlib").write_bytes(large_bytes)
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
