from minimal_predictive_lm.sparc_episodic_focus import SPARCHS8Model


def test_focus_survives_crowded_workspace_and_distractors() -> None:
    model = SPARCHS8Model()
    distractors = "".join(
        f"観測区画{index}の担当者は記録員{index}である。" for index in range(120)
    )
    model.ingest(
        distractors
        + "青葉市の水源は北岳湖である。"
        + "北岳湖は冬の降雪を蓄える。"
        + "青葉市は夏の渇水に備えて貯水量を管理する。",
        source_id="水資源報告",
    )
    model.ingest("白峰市の市鳥はツバメである。", source_id="資料A")
    model.ingest("白峰市の市鳥はカワセミである。", source_id="資料B")

    # Pollute the bounded workspace with other successful answers first.
    assert "矛盾" in model.reply("白峰市の市鳥は何ですか？").text
    first = model.reply("青葉市の水源はどこですか？")
    assert first.text.startswith("北岳湖です")

    followup = model.reply("それについてもう少し教えてください。")
    assert followup.mechanism == "bounded-discourse-focus"
    assert "青葉市" in followup.text or "北岳湖" in followup.text
    assert "水資源報告" in followup.text
    assert followup.candidates_inspected <= 32
    assert len(model.episodic.workspace) <= model.episodic.workspace_size


def test_focus_model_round_trip_keeps_revision_memory() -> None:
    model = SPARCHS8Model()
    model.ingest("青葉市の人口は十二万人である。", source_id="旧統計")
    model.revise("最新情報:青葉市の人口は十三万人である。", source_id="新統計")
    restored = SPARCHS8Model.from_bytes(model.to_bytes())
    reply = restored.reply("青葉市の人口は何人ですか？")
    assert reply.text.startswith("十三万人です")
    assert restored.episodic.revision_events == 1
