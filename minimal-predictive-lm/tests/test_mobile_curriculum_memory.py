from __future__ import annotations

from minimal_predictive_lm.mobile_curriculum_memory import (
    KnowledgeDocument,
    QuantizedCurriculumMemory,
)


def _documents() -> list[KnowledgeDocument]:
    return [
        KnowledgeDocument(
            "光合成",
            "植物は光合成によって二酸化炭素と水から有機物をつくり、酸素を放出する。",
        ),
        KnowledgeDocument(
            "ニュートンの第二法則",
            "物体に働く合力は質量と加速度の積に等しい。式ではF=maと表す。",
        ),
        KnowledgeDocument(
            "江戸幕府",
            "徳川家康は1603年に征夷大将軍となり、江戸幕府を開いた。",
        ),
    ]


def test_memory_selects_option_supported_by_retrieved_knowledge() -> None:
    memory = QuantizedCurriculumMemory.build(
        _documents(),
        buckets=4096,
        max_features_per_document=256,
        max_postings_per_feature=16,
    )
    prediction = memory.score_options(
        "植物が光合成で放出する気体は何か。",
        ("窒素", "酸素", "二酸化炭素", "水素"),
    )
    assert prediction.index == 1
    assert "光合成" in prediction.retrieved_documents
    assert prediction.active_postings <= memory.max_active_postings * 5


def test_memory_round_trip_preserves_predictions_and_resource_bounds() -> None:
    memory = QuantizedCurriculumMemory.build(
        _documents(),
        buckets=4096,
        max_features_per_document=256,
        max_postings_per_feature=16,
    )
    restored = QuantizedCurriculumMemory.from_bytes(memory.to_bytes())
    prompt = "1603年に江戸幕府を開いた人物は誰か。"
    options = ("徳川家康", "豊臣秀吉", "織田信長", "徳川慶喜")
    before = memory.score_options(prompt, options)
    after = restored.score_options(prompt, options)
    assert after.index == before.index == 0
    assert after.scores == before.scores
    report = restored.resource_report()
    assert report["paged_sparse"] is True
    assert report["estimated_active_bytes"] <= 128 * 1024
    assert report["serialized_bytes"] < 1_000_000


def test_unknown_question_does_not_scan_every_document() -> None:
    documents = [
        KnowledgeDocument(f"資料{index}", f"固有情報{index}についての説明文です。")
        for index in range(500)
    ]
    memory = QuantizedCurriculumMemory.build(
        documents,
        buckets=16384,
        max_features_per_document=64,
        max_postings_per_feature=24,
    )
    prediction = memory.score_options(
        "この資料群にない未知の質問",
        ("甲", "乙", "丙", "丁"),
    )
    assert prediction.active_postings <= memory.max_active_postings * 5
    assert prediction.active_postings < len(documents) * 64
