from minimal_predictive_lm.sparc_discourse_compact import (
    CompactSparseDiscourseGraph,
    SPARCHS9CompactModel,
)


ARTICLE = (
    "学校は探究学習の時間を増やすべきである。"
    "なぜなら、生徒が自分で問いを立てる力を伸ばせるからである。"
    "例えば、地域の水質を調べる活動では理科と社会の知識を結び付けられる。"
    "しかし、基礎知識の授業時間が減るという懸念もある。"
    "したがって、基礎授業を維持しながら探究学習を段階的に増やすことが重要である。"
)


def test_exact_title_prefers_longest_over_prefix() -> None:
    graph = CompactSparseDiscourseGraph()
    graph.ingest(ARTICLE, source_id="資料A", title="循環論A")
    graph.ingest(
        ARTICLE.replace("探究学習", "地域学習"),
        source_id="資料AA",
        title="循環論AA",
    )
    reply = graph.answer("循環論AAの筆者の主張を要約してください。")
    assert reply is not None
    assert "資料AA" in reply.text
    assert "地域学習" in reply.text
    assert graph.last_candidates == 1
    assert graph.last_anchor_reads == 0


def test_selective_index_and_reverse_edges() -> None:
    graph = CompactSparseDiscourseGraph(anchors_per_document=64)
    graph.ingest(ARTICLE, source_id="教育論A", title="探究学習論")
    reply = graph.answer("探究学習論の根拠を説明してください。")
    assert reply is not None
    assert "問いを立てる力" in reply.text
    report = graph.report()
    assert report["selective_anchor_index"] is True
    assert report["posting_edges"] <= 64
    assert graph.last_edge_reads <= 4


def test_compact_persistence_rebuilds_title_and_sparse_index() -> None:
    model = SPARCHS9CompactModel()
    model.ingest_discourse(ARTICLE, source_id="教育論A", title="探究学習論")
    restored = SPARCHS9CompactModel.from_bytes(model.to_bytes())
    reply = restored.reply("探究学習論の筆者の主張は何ですか？")
    assert "段階的に増やす" in reply.text
    assert restored.discourse.last_anchor_reads == 0
    assert restored.discourse.report()["global_edge_scan_used"] is False


def test_base_hs8_fallback_is_retained() -> None:
    model = SPARCHS9CompactModel()
    model.base.ingest("青葉市の水源は北岳湖である。", source_id="水資料")
    reply = model.reply("青葉市の水源はどこですか？")
    assert reply.text.startswith("北岳湖です")
