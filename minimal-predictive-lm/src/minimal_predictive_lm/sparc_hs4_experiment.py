from __future__ import annotations

import json
import resource
import time
from pathlib import Path

from .sparc_raw_induction import RawCurriculumModel


def bootstrap_corpus() -> list[str]:
    return [
        "東京は日本の首都です",
        "パリはフランスの首都です",
        "ローマはイタリアの首都です",
        "ベルリンはドイツの首都です",
        "マドリードはスペインの首都です",
        "猫は哺乳類に分類されます",
        "哺乳類は動物に分類されます",
        "猫は動物に分類されます",
        "犬は哺乳類に分類されます",
        "犬は動物に分類されます",
        "動物は生物に分類されます",
        "猫は生物に分類されます",
        "犬は生物に分類されます",
        "落雷によって停電が発生します",
        "停電によって冷却停止が発生します",
        "冷却停止によって装置停止が発生します",
        "落雷によって冷却停止が発生します",
        "停電によって装置停止が発生します",
        "落雷によって装置停止が発生します",
    ]


def configured_model() -> RawCurriculumModel:
    model = RawCurriculumModel().fit_raw(bootstrap_corpus())
    assert model.align_qa("日本の首都は何ですか？", "東京")
    assert model.align_qa("フランスの首都は何ですか？", "パリ")
    assert model.align_qa("猫は生物に分類されますか？", "はい")
    assert model.align_qa("落雷は装置停止につながりますか？", "はい")
    return model


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model = configured_model()
    capital = model.reply("イタリアの首都は何ですか？")
    taxonomy = model.reply("犬は生物に分類されますか？")
    causality = model.reply("落雷は装置停止につながりますか？")
    unknown = model.reply("未知国の首都は何ですか？")
    restored = RawCurriculumModel.from_bytes(model.to_bytes())
    persistence = restored.reply("イタリアの首都は何ですか？")

    checks = {
        "raw_multi_relation_discovery": model.miner.report.schemas >= 3,
        "weak_qa_alignment": model.qa_alignments == 4,
        "held_out_capital": capital.text == "ローマです。",
        "learned_transitivity": taxonomy.text.startswith("犬は生物の関係"),
        "raw_causal_reasoning": causality.text.startswith("落雷は装置停止の関係"),
        "calibrated_unknown": "教えて" in unknown.text,
        "persistence": persistence.text == "ローマです。",
        "no_structured_labels_for_raw_fit": (
            model.report()["structured_subject_object_labels_required_for_raw_fit"]
            is False
        ),
    }

    scale_start = time.perf_counter()
    relation_families = 20_000
    examples_per_family = 5
    raw_sentences = [
        f"要素{family}_{example}は集合{family}_{example}の分類コード{family}です"
        for family in range(relation_families)
        for example in range(examples_per_family)
    ]
    large = RawCurriculumModel(
        reasoning_profile="desktop-large",
        max_schemas=50_000,
    ).fit_raw(raw_sentences)

    correct = 0
    max_candidates = 0
    max_anchor_reads = 0
    sample_queries = 512
    for sample in range(sample_queries):
        family = (sample * 7919) % relation_families
        reply = large.reply(
            f"新要素{sample}は新集合{sample}の分類コード{family}です"
        )
        if reply.mechanism == "learned-surface-schema":
            correct += 1
        max_candidates = max(
            max_candidates,
            large.model.schemas.last_candidates_inspected,
        )
        max_anchor_reads = max(
            max_anchor_reads,
            large.model.schemas.last_anchor_reads,
        )

    large_report = large.report()
    large_report.update(
        {
            "raw_sentences": len(raw_sentences),
            "relation_families": relation_families,
            "sample_queries": sample_queries,
            "correct_queries": correct,
            "max_schema_candidates_observed": max_candidates,
            "max_anchor_reads_observed": max_anchor_reads,
            "build_and_query_seconds": time.perf_counter() - scale_start,
            "entities": len(large.cortex.labels),
            "relation_edges": large.cortex.edge_count,
        }
    )

    result: dict[str, object] = {
        "capability_id": "SPARC-HS4-RAW-INDUCTION",
        "transformer_used": False,
        "softmax_attention_used": False,
        "growing_kv_cache_used": False,
        "raw_unlabeled_sentence_fit": True,
        "weak_qa_relation_alignment": True,
        "interactive_chat": True,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "compact_model": model.report(),
        "large_raw_curriculum": large_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS4 discovers repeated two-slot surface relations from unlabeled Japanese "
            "sentence groups and aligns them with weak QA examples. It does not yet "
            "perform unrestricted semantic role discovery, mathematical program induction, "
            "or high-school-level general intelligence."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and large.miner.report.sentences == 100_000
        and large.miner.report.schemas == relation_families
        and large.miner.report.facts == 100_000
        and len(large.cortex.labels) == 200_000 + sample_queries * 2
        and large.cortex.edge_count == 200_000 + sample_queries
        and correct == sample_queries
        and max_candidates <= 64
        and max_anchor_reads <= 256
        and large_report["serialized_bytes"] <= 10_000_000
        and result["peak_process_kib"] <= 1_500_000
        and result["elapsed_seconds"] <= 120.0
    )

    (output_dir / "sparc_hs4_raw_curriculum.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-HS4-compact.model.zlib").write_bytes(model.to_bytes())
    (output_dir / "SPARC-HS4-large-raw.model.zlib").write_bytes(large.to_bytes())
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
