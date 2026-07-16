from __future__ import annotations

import json
import resource
import time
from pathlib import Path

from .sparc_abstraction_topic import SPARCHS9Model
from .sparc_episodic_focus import SPARCHS8Model
from .sparc_hs8_focus_experiment import configured_model as configured_hs8


def configured_model() -> SPARCHS9Model:
    model = SPARCHS9Model(configured_hs8())
    model.ingest_document(
        "被子植物の分類は種子植物である。"
        "被子植物の胚珠は子房に包まれている。\n\n"
        "裸子植物の分類は種子植物である。"
        "裸子植物の胚珠はむき出しである。",
        source_id="植物比較資料",
    )
    model.ingest_document(
        "オオカナダモの代謝は光合成を行う。"
        "アオミドロの代謝は光合成を行う。"
        "シアノバクテリアの代謝は光合成を行う。",
        source_id="光合成資料",
    )
    model.ingest_document(
        "青葉地域の主要産業は稲作である。"
        "青葉地域の気候は夏に高温多湿である。",
        source_id="青葉産業資料",
    )
    model.ingest_document(
        "青葉地域の水資源は河川灌漑である。",
        source_id="青葉水資源資料",
    )
    model.ingest_document(
        "主張は地域交通への投資が必要である。"
        "理由は高齢者の移動手段が不足しているためである。"
        "根拠は住民調査で通院困難の回答が増加したことである。",
        source_id="交通論説",
    )
    return model


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = configured_model()

    answers = {
        "conversation": model.reply("こんにちは"),
        "units": model.reply("時速90kmで40分進む距離は何kmですか？"),
        "revision": model.reply("青葉市の人口は何人ですか？"),
        "regional_summary": model.reply("青葉地域について要約してください。"),
        "plant_comparison": model.reply("被子植物と裸子植物を比較してください。"),
        "photosynthesis_common": model.reply(
            "オオカナダモとアオミドロの共通点を教えてください。"
        ),
        "argument": model.reply("交通論説の主張と根拠を説明してください。"),
    }
    followup_first = model.reply("青葉地域について要約してください。")
    followup = model.reply("それについてもう少し教えてください。")

    restored = SPARCHS9Model.from_bytes(model.to_bytes())
    persistence = restored.reply("被子植物と裸子植物の違いを比較してください。")

    checks = {
        "conversation_retained": answers["conversation"].text.startswith("こんにちは"),
        "unit_planning_retained": answers["units"].text.startswith("60kmです"),
        "revision_retained": answers["revision"].text.startswith("十三万人です"),
        "source_grounded_summary": (
            "稲作" in answers["regional_summary"].text
            and "河川灌漑" in answers["regional_summary"].text
            and "青葉産業資料" in answers["regional_summary"].text
            and "青葉水資源資料" in answers["regional_summary"].text
        ),
        "comparison_commonality": (
            "種子植物" in answers["plant_comparison"].text
            and "共通点" in answers["plant_comparison"].text
        ),
        "comparison_difference": (
            "子房に包まれている" in answers["plant_comparison"].text
            and "むき出し" in answers["plant_comparison"].text
        ),
        "learned_abstraction": (
            "光合成を行う" in answers["photosynthesis_common"].text
            and answers["photosynthesis_common"].mechanism
            == "local-relation-alignment-comparison"
        ),
        "argument_structure": (
            answers["argument"].mechanism == "explicit-argument-frame"
            and "地域交通への投資" in answers["argument"].text
            and "住民調査" in answers["argument"].text
        ),
        "hs8_followup_retained": (
            "青葉地域" in followup_first.text
            and ("青葉地域" in followup.text or "稲作" in followup.text)
        ),
        "save_load_abstraction": (
            "種子植物" in persistence.text
            and "子房に包まれている" in persistence.text
        ),
    }

    scale_start = time.perf_counter()
    large = SPARCHS9Model(SPARCHS8Model())
    paragraph_count = 50_000
    for index in range(paragraph_count):
        large.ingest_document(
            f"地域{index}の主要産業は産業{index % 2003}である。"
            f"地域{index}の気候は気候{index % 97}である。",
            source_id=f"地域資料{index}",
        )

    sample_queries = 512
    correct = 0
    max_candidates = 0
    max_anchor_reads = 0
    max_operations = 0
    for sample in range(sample_queries):
        index = (sample * 7919) % paragraph_count
        reply = large.reply(f"地域{index}について要約してください。")
        if (
            f"産業{index % 2003}" in reply.text
            and f"気候{index % 97}" in reply.text
        ):
            correct += 1
        max_candidates = max(max_candidates, reply.candidates_inspected)
        max_anchor_reads = max(max_anchor_reads, large.abstraction.last_anchor_reads)
        max_operations = max(max_operations, reply.estimated_sparse_operations)

    large_bytes = large.to_bytes()
    abstraction_report = large.abstraction.report()
    scale_report = {
        "paragraphs": paragraph_count,
        "episodes": len(large.base.episodic.episodes),
        "subjects": abstraction_report["subjects"],
        "abstraction_nodes": abstraction_report["abstraction_nodes"],
        "sample_queries": sample_queries,
        "correct_queries": correct,
        "max_candidates_observed": max_candidates,
        "max_anchor_reads_observed": max_anchor_reads,
        "max_estimated_operations": max_operations,
        "serialized_bytes": len(large_bytes),
        "build_and_query_seconds": time.perf_counter() - scale_start,
        "full_history_scan_used": False,
        "growing_kv_cache_used": False,
    }

    compact_bytes = model.to_bytes()
    result: dict[str, object] = {
        "capability_id": "SPARC-HS9-SPARSE-ABSTRACTION",
        "transformer_used": False,
        "softmax_attention_used": False,
        "growing_kv_cache_used": False,
        "full_history_scan_used": False,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "answers": {
            key: {"text": value.text, "mechanism": value.mechanism}
            for key, value in answers.items()
        },
        "compact_model": model.report(),
        "large_abstraction_memory": scale_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS9 induces repeated relational abstractions and explicit argument frames. "
            "It is not unrestricted literary interpretation or complete Japanese "
            "high-school reading comprehension."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and correct == sample_queries
        and scale_report["episodes"] == 100_000
        and max_candidates <= 16
        and max_anchor_reads <= 128
        and max_operations <= 128
        and 2_000 <= scale_report["abstraction_nodes"] <= 2_200
        and len(large_bytes) <= 10_000_000
        and result["peak_process_kib"] <= 1_200_000
        and result["elapsed_seconds"] <= 120.0
    )

    (output_dir / "sparc_hs9_abstraction.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-HS9-compact.model.zlib").write_bytes(compact_bytes)
    (output_dir / "SPARC-HS9-abstraction-large.model.zlib").write_bytes(large_bytes)
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
