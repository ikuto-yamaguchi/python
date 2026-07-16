from minimal_predictive_lm.sparc_abstraction_topic import SPARCHS9Model


def _model() -> SPARCHS9Model:
    model = SPARCHS9Model()
    model.ingest_document(
        "被子植物の分類は種子植物である。"
        "被子植物の胚珠は子房に包まれている。\n\n"
        "裸子植物の分類は種子植物である。"
        "裸子植物の胚珠はむき出しである。",
        source_id="植物資料",
    )
    model.ingest_document(
        "青葉地域の主要産業は稲作である。"
        "青葉地域の気候は夏に高温多湿である。\n\n"
        "青葉地域の水資源は河川灌漑である。",
        source_id="青葉資料",
    )
    model.ingest_document(
        "主張は地域交通への投資が必要である。"
        "理由は高齢者の移動手段が不足しているためである。"
        "根拠は住民調査で通院困難の回答が増加したことである。",
        source_id="交通論説",
    )
    return model


def test_local_comparison_extracts_commonality_and_difference() -> None:
    model = _model()
    reply = model.reply("被子植物と裸子植物を比較してください。")
    assert reply.mechanism == "local-relation-alignment-comparison"
    assert "種子植物" in reply.text
    assert "子房に包まれている" in reply.text
    assert "むき出し" in reply.text
    assert reply.estimated_sparse_operations <= 16


def test_topic_summary_is_source_grounded_and_updates_focus() -> None:
    model = _model()
    reply = model.reply("青葉地域について要約してください。")
    assert reply.mechanism == "topic-centred-sparse-abstraction"
    assert "稲作" in reply.text
    assert "河川灌漑" in reply.text
    assert "青葉資料" in reply.text
    followup = model.reply("それについてもう少し教えてください。")
    assert "青葉地域" in followup.text or "河川灌漑" in followup.text
    assert len(model.base.episodic.workspace) <= model.base.episodic.workspace_size


def test_explicit_argument_frame_and_persistence() -> None:
    model = _model()
    reply = model.reply("交通論説の主張と根拠を説明してください。")
    assert reply.mechanism == "explicit-argument-frame"
    assert "地域交通への投資" in reply.text
    assert "住民調査" in reply.text
    restored = SPARCHS9Model.from_bytes(model.to_bytes())
    comparison = restored.reply("被子植物と裸子植物の違いを比較してください。")
    assert "種子植物" in comparison.text
    assert "むき出し" in comparison.text
