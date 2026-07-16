from minimal_predictive_lm.sparc_episodic import (
    SPARCHS8Model,
    SparseEpisodicRevisionMemory,
)


def test_long_passage_retrieval_and_source() -> None:
    model = SPARCHS8Model()
    passage = "".join(
        [f"第{index}区画では観測番号{index}を記録した。" for index in range(80)]
    )
    passage += (
        "青葉市の水源は北岳湖である。"
        "北岳湖は冬の降雪を蓄える。"
        "市は夏の渇水に備えて貯水量を管理する。"
    )
    model.ingest(passage, source_id="水資源報告")
    reply = model.reply("青葉市の水源はどこですか？")
    assert reply.text.startswith("北岳湖です")
    assert "水資源報告" in reply.text
    assert reply.candidates_inspected <= 32


def test_bounded_cross_source_causal_chain() -> None:
    model = SPARCHS8Model()
    model.ingest("海面温度の上昇により蒸発量が増える。", source_id="気候A")
    model.ingest("蒸発量が増えるため雲が形成される。", source_id="気候B")
    model.ingest("雲が形成されるため降水が増える。", source_id="気候C")
    reply = model.reply("降水が増えるのはなぜですか？")
    assert reply.mechanism == "bounded-causal-episodic-chain"
    assert "海面温度の上昇" in reply.text
    assert "気候A" in reply.text and "気候B" in reply.text and "気候C" in reply.text
    assert reply.active_bits == 3


def test_revision_supersedes_old_claim() -> None:
    model = SPARCHS8Model()
    model.ingest("青葉市の水源は北岳湖である。", source_id="旧資料")
    model.revise("訂正:青葉市の水源は南川貯水池である。", source_id="訂正文書")
    reply = model.reply("青葉市の水源はどこですか？")
    assert reply.text.startswith("南川貯水池です")
    assert "訂正文書" in reply.text
    assert model.episodic.revision_events == 1
    assert sum(episode.active for episode in model.episodic.episodes) == 1


def test_unresolved_conflict_is_reported() -> None:
    memory = SparseEpisodicRevisionMemory()
    memory.ingest("白峰市の市鳥はツバメである。", source_id="資料A")
    memory.ingest("白峰市の市鳥はカワセミである。", source_id="資料B")
    reply = memory.answer("白峰市の市鳥は何ですか？")
    assert reply is not None
    assert reply.mechanism == "episodic-conflict-detection"
    assert "ツバメ" in reply.text and "カワセミ" in reply.text
    assert memory.conflict_events == 1


def test_bounded_followup_focus() -> None:
    model = SPARCHS8Model()
    model.ingest(
        "青葉市の水源は北岳湖である。北岳湖は冬の降雪を蓄える。",
        source_id="資料A",
    )
    first = model.reply("青葉市の水源はどこですか？")
    assert first.text.startswith("北岳湖です")
    followup = model.reply("それについて教えてください。")
    assert "青葉市" in followup.text or "北岳湖" in followup.text
    assert len(model.episodic.workspace) <= model.episodic.workspace_size


def test_persistence_preserves_revision_state() -> None:
    model = SPARCHS8Model()
    model.ingest("青葉市の水源は北岳湖である。", source_id="旧資料")
    model.revise("最新情報:青葉市の水源は南川貯水池である。", source_id="更新資料")
    restored = SPARCHS8Model.from_bytes(model.to_bytes())
    reply = restored.reply("青葉市の水源はどこですか？")
    assert reply.text.startswith("南川貯水池です")
    assert restored.episodic.revision_events == 1
    report = restored.episodic.report()
    assert report["full_history_scan_used"] is False
    assert report["growing_kv_cache_used"] is False
