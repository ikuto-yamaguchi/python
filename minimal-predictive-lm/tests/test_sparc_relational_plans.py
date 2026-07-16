from minimal_predictive_lm.sparc_cross_domain_plans_v2 import SPARCHS11ModelV2
from minimal_predictive_lm.sparc_relational_plans import SPARCHS12Model


def _taxonomy_model() -> SPARCHS12Model:
    model = SPARCHS12Model(SPARCHS11ModelV2())
    for animal in ("ツバメ", "ハト", "カラス"):
        model.ingest_fact(
            f"{animal}の分類は鳥類である。", source_id=f"{animal}分類資料"
        )
    model.ingest_fact("鳥類の体温は一定である。", source_id="鳥類生理資料")
    model.teach_relational_plan(
        [
            ("ツバメの体温特性は何ですか？", "一定です"),
            ("ハトの体温特性は何ですか？", "一定です"),
            ("カラスの体温特性は何ですか？", "一定です"),
        ]
    )
    return model


def test_learned_relation_sequence_transfers_to_unseen_subject() -> None:
    model = _taxonomy_model()
    model.ingest_fact("ハヤブサの分類は鳥類である。", source_id="ハヤブサ分類資料")
    reply = model.reply("ハヤブサの体温特性は何ですか？")
    assert reply.mechanism == "learned-relational-path-plan"
    assert reply.text.startswith("一定です")
    assert "分類 → 体温" in reply.text
    assert "ハヤブサ分類資料" in reply.text
    assert "鳥類生理資料" in reply.text
    assert model.relational_plans.last_edge_reads == 2


def test_relation_conflict_refuses_then_revision_reuses_plan() -> None:
    model = _taxonomy_model()
    model.ingest_fact("未知生物の分類は鳥類である。", source_id="分類資料1")
    model.ingest_fact("未知生物の分類は爬虫類である。", source_id="分類資料2")
    model.ingest_fact("爬虫類の体温は外気で変化する。", source_id="爬虫類生理資料")
    conflict = model.reply("未知生物の体温特性は何ですか？")
    assert conflict.mechanism == "relational-plan-evidence-conflict"
    assert "確定できません" in conflict.text

    model.ingest_fact(
        "最新情報:未知生物の分類は鳥類である。",
        source_id="訂正分類資料",
        revision=True,
    )
    revised = model.reply("未知生物の体温特性は何ですか？")
    assert revised.text.startswith("一定です")
    assert "訂正分類資料" in revised.text or "分類資料1" in revised.text


def test_relational_plan_survives_round_trip() -> None:
    model = _taxonomy_model()
    model.ingest_fact("ハヤブサの分類は鳥類である。", source_id="ハヤブサ分類資料")
    restored = SPARCHS12Model.from_bytes(model.to_bytes())
    reply = restored.reply("ハヤブサの体温特性は何ですか？")
    assert reply.text.startswith("一定です")
    report = restored.relational_plans.report()
    assert report["plans"] == 1
    assert report["global_node_scan_used"] is False
    assert report["global_episode_scan_used"] is False
    assert report["global_relation_scan_used"] is False
    assert report["global_plan_scan_used"] is False
