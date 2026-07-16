from __future__ import annotations

import json
import resource
import time
from pathlib import Path

from .sparc_episodic import SPARCHS8Model, SparseEpisodicRevisionMemory
from .sparc_hs7_experiment import configured_model as configured_hs7


def configured_model() -> SPARCHS8Model:
    model = SPARCHS8Model(configured_hs7())
    distractors = "".join(
        f"観測区画{index}では記録番号{index}を保存した。" for index in range(120)
    )
    model.ingest(
        distractors
        + "青葉市の水源は北岳湖である。"
        + "北岳湖は冬の降雪を蓄える。"
        + "市は夏の渇水に備えて貯水量を管理する。",
        source_id="水資源報告",
    )
    model.ingest("海面温度の上昇により蒸発量が増える。", source_id="気候A")
    model.ingest("蒸発量が増えるため雲が形成される。", source_id="気候B")
    model.ingest("雲が形成されるため降水が増える。", source_id="気候C")
    model.ingest("青葉市の人口は十二万人である。", source_id="旧統計")
    model.revise("最新情報:青葉市の人口は十三万人である。", source_id="新統計")
    model.ingest("白峰市の市鳥はツバメである。", source_id="白峰資料A")
    model.ingest("白峰市の市鳥はカワセミである。", source_id="白峰資料B")
    return model


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = configured_model()

    answers = {
        "conversation": model.reply("こんにちは"),
        "social": model.reply("イタリアの首都は何ですか？"),
        "units": model.reply("時速90kmで40分進む距離は何kmですか？"),
        "long_fact": model.reply("青葉市の水源はどこですか？"),
        "causal": model.reply("降水が増えるのはなぜですか？"),
        "revision": model.reply("青葉市の人口は何人ですか？"),
        "conflict": model.reply("白峰市の市鳥は何ですか？"),
    }

    followup_first = model.reply("青葉市の水源はどこですか？")
    followup = model.reply("それについて教えてください。")

    sustained_correct = 0
    for index in range(30):
        model.ingest(
            f"対話項目{index}の合言葉は符号{index}である。",
            source_id=f"対話資料{index}",
        )
        answer = model.reply(f"対話項目{index}の合言葉は何ですか？")
        if answer.text.startswith(f"符号{index}です"):
            sustained_correct += 1

    compact_bytes = model.to_bytes()
    restored = SPARCHS8Model.from_bytes(compact_bytes)
    persistence = restored.reply("青葉市の人口は何人ですか？")

    active_old_population = [
        episode
        for episode in model.episodic.episodes
        if episode.claim_key == "青葉市␟人口" and episode.active
    ]
    checks = {
        "conversation_retained": answers["conversation"].text.startswith("こんにちは"),
        "social_retained": answers["social"].text == "ローマです。",
        "unit_planning_retained": answers["units"].text.startswith("60kmです"),
        "long_passage_fact": answers["long_fact"].text.startswith("北岳湖です"),
        "source_grounding": "水資源報告" in answers["long_fact"].text,
        "multi_source_causal_chain": (
            answers["causal"].mechanism == "bounded-causal-episodic-chain"
            and all(source in answers["causal"].text for source in ("気候A", "気候B", "気候C"))
        ),
        "revision_applied": answers["revision"].text.startswith("十三万人です"),
        "old_claim_suppressed": (
            len(active_old_population) == 1
            and active_old_population[0].claim_value == "十三万人"
        ),
        "unresolved_conflict_reported": (
            answers["conflict"].mechanism == "episodic-conflict-detection"
            and "ツバメ" in answers["conflict"].text
            and "カワセミ" in answers["conflict"].text
        ),
        "bounded_followup_focus": (
            followup_first.text.startswith("北岳湖です")
            and ("青葉市" in followup.text or "北岳湖" in followup.text)
            and len(model.episodic.workspace) <= model.episodic.workspace_size
        ),
        "thirty_turn_persistence": sustained_correct == 30,
        "save_load_revision": persistence.text.startswith("十三万人です"),
    }

    scale_start = time.perf_counter()
    memory = SparseEpisodicRevisionMemory(
        max_episodes=120_000,
        max_candidates=32,
        read_budget=192,
    )
    episode_count = 100_000
    for index in range(episode_count):
        memory.ingest(
            f"地域{index}の主要産業は産業{index % 2003}である。",
            source_id=f"大規模資料{index}",
        )

    sample_queries = 512
    correct = 0
    max_candidates = 0
    max_anchor_reads = 0
    max_operations = 0
    for sample in range(sample_queries):
        index = (sample * 7919) % episode_count
        answer = memory.answer(f"地域{index}の主要産業は何ですか？")
        if answer is not None and answer.text.startswith(f"産業{index % 2003}です"):
            correct += 1
        max_candidates = max(max_candidates, memory.last_candidates)
        max_anchor_reads = max(max_anchor_reads, memory.last_anchor_reads)
        max_operations = max(max_operations, memory.last_estimated_operations)

    large_bytes = memory.to_bytes()
    scale_report = {
        "episodes": len(memory.episodes),
        "posting_edges": sum(len(items) for items in memory.postings.values()),
        "claim_keys": len(memory.claims),
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

    result: dict[str, object] = {
        "capability_id": "SPARC-HS8-EPISODIC-REVISION",
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
        "compact_model": {
            "serialized_bytes": len(compact_bytes),
            "episodic": model.episodic.report(),
            "workspace_entries": len(model.episodic.workspace),
        },
        "large_episodic_memory": scale_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS8 adds sparse long-passage episodic retrieval, source grounding, "
            "bounded causal chaining, conflict detection and explicit revision. "
            "It is not unrestricted reading comprehension or Japanese high-school-level AGI."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and correct == sample_queries
        and max_candidates <= 32
        and max_anchor_reads <= 192
        and max_operations <= 512
        and len(large_bytes) <= 5_000_000
        and result["peak_process_kib"] <= 1_000_000
        and result["elapsed_seconds"] <= 120.0
    )

    (output_dir / "sparc_hs8_episodic.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "SPARC-HS8-compact.model.zlib").write_bytes(compact_bytes)
    (output_dir / "SPARC-HS8-episodic-large.model.zlib").write_bytes(large_bytes)
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
