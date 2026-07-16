from minimal_predictive_lm.sparc_discourse import SPARCHS9Model, SparseDiscourseGraph


ARTICLE = (
    "学校は探究学習の時間を増やすべきである。"
    "なぜなら、生徒が自分で問いを立てる力を伸ばせるからである。"
    "例えば、地域の水質を調べる活動では理科と社会の知識を結び付けられる。"
    "しかし、基礎知識の授業時間が減るという懸念もある。"
    "したがって、基礎授業を維持しながら探究学習を段階的に増やすことが重要である。"
)


def test_summary_uses_reverse_indexed_supports() -> None:
    model = SPARCHS9Model()
    model.ingest_discourse(ARTICLE, source_id="教育論A", title="探究学習論")
    reply = model.reply("探究学習論の筆者の主張を要約してください。")
    assert reply.mechanism == "sparse-discourse-summary"
    assert "段階的に増やす" in reply.text
    assert "問いを立てる力" in reply.text
    assert "教育論A" in reply.text
    assert model.discourse.last_edge_reads <= 4


def test_evidence_and_counterargument_are_local() -> None:
    graph = SparseDiscourseGraph()
    graph.ingest(ARTICLE, source_id="教育論A", title="探究学習論")
    evidence = graph.answer("探究学習論の結論の根拠は何ですか？")
    assert evidence is not None
    assert evidence.mechanism == "reverse-indexed-evidence"
    assert "問いを立てる力" in evidence.text
    assert graph.last_edge_reads <= 4

    counter = graph.answer("探究学習論にある反対意見を教えてください。")
    assert counter is not None
    assert counter.mechanism == "local-counterargument-retrieval"
    assert "授業時間が減る" in counter.text
    assert graph.last_edge_reads <= 4


def test_two_document_comparison() -> None:
    graph = SparseDiscourseGraph()
    graph.ingest(
        "都市は自動車交通を減らすべきである。なぜなら大気汚染を抑えられるからである。"
        "したがって公共交通を優先することが重要である。",
        source_id="交通A",
        title="公共交通優先論",
    )
    graph.ingest(
        "都市は道路容量を増やすべきである。なぜなら物流の遅延を減らせるからである。"
        "したがって幹線道路の整備が重要である。",
        source_id="交通B",
        title="道路整備論",
    )
    reply = graph.answer("公共交通優先論と道路整備論の違いを比較してください。")
    assert reply is not None
    assert reply.mechanism == "bounded-two-document-comparison"
    assert "交通A" in reply.text and "交通B" in reply.text
    assert reply.active_bits == 2


def test_generic_followup_uses_bounded_document_workspace() -> None:
    graph = SparseDiscourseGraph()
    graph.ingest(ARTICLE, source_id="教育論A", title="探究学習論")
    reply = graph.answer("この文章の要旨は何ですか？")
    assert reply is not None
    assert "段階的に増やす" in reply.text
    assert len(graph.workspace) <= graph.workspace.maxlen


def test_persistence_rebuilds_reverse_indices() -> None:
    model = SPARCHS9Model()
    model.ingest_discourse(ARTICLE, source_id="教育論A", title="探究学習論")
    restored = SPARCHS9Model.from_bytes(model.to_bytes())
    reply = restored.reply("探究学習論の根拠を説明してください。")
    assert "問いを立てる力" in reply.text
    report = restored.discourse.report()
    assert report["global_edge_scan_used"] is False
    assert report["full_history_scan_used"] is False


def test_hs8_capabilities_remain_available() -> None:
    model = SPARCHS9Model()
    model.base.ingest("青葉市の水源は北岳湖である。", source_id="水資源資料")
    reply = model.reply("青葉市の水源はどこですか？")
    assert reply.text.startswith("北岳湖です")
