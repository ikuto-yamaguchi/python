from minimal_predictive_lm.sparc_cross_domain_plans_v2 import SPARCHS11ModelV2
from minimal_predictive_lm.sparc_goal_rules import SPARCHS13Model
from minimal_predictive_lm.sparc_relational_plans import SPARCHS12Model


def _trained_model() -> SPARCHS13Model:
    model = SPARCHS13Model(SPARCHS12Model(SPARCHS11ModelV2()))
    for animal in ("ツバメ", "ハト", "カラス"):
        model.ingest_fact(
            f"{animal}の分類は鳥類である。", source_id=f"{animal}分類資料"
        )
        model.ingest_fact(
            f"{animal}の体温特性は一定である。",
            source_id=f"{animal}直接結論",
        )
        model.ingest_fact(
            f"{animal}の生理区分は恒温型である。",
            source_id=f"{animal}生理結論",
        )
    model.ingest_fact("鳥類の体温は一定である。", source_id="鳥類生理資料")
    model.ingest_fact("一定の代謝分類は恒温型である。", source_id="代謝分類資料")
    model.teach_rule(
        [
            ("ツバメの体温特性は何ですか？", "一定です"),
            ("ハトの体温特性は何ですか？", "一定です"),
            ("カラスの体温特性は何ですか？", "一定です"),
        ]
    )
    model.teach_rule(
        [
            ("ツバメの生理区分は何ですか？", "恒温型です"),
            ("ハトの生理区分は何ですか？", "恒温型です"),
            ("カラスの生理区分は何ですか？", "恒温型です"),
        ]
    )
    return model


def test_goal_rule_derives_missing_head_fact() -> None:
    model = _trained_model()
    model.ingest_fact("ハヤブサの分類は鳥類である。", source_id="ハヤブサ分類資料")
    reply = model.reply("ハヤブサの体温特性は何ですか？")
    assert reply.mechanism == "goal-directed-learned-rule"
    assert reply.text.startswith("一定です")
    assert "体温特性(x,z) <- 分類 -> 体温" in reply.text
    assert "ハヤブサ分類資料" in reply.text
    assert "鳥類生理資料" in reply.text


def test_goal_rule_recursively_invokes_another_rule() -> None:
    model = _trained_model()
    model.ingest_fact("ハヤブサの分類は鳥類である。", source_id="ハヤブサ分類資料")
    reply = model.reply("ハヤブサの生理区分は何ですか？")
    assert reply.text.startswith("恒温型です")
    assert "生理区分(x,z) <- 体温特性 -> 代謝分類" in reply.text
    assert "体温特性(x,z) <- 分類 -> 体温" in reply.text
    assert "代謝分類資料" in reply.text
    assert model.goal_rules.last_rule_reads == 2


def test_goal_rule_conflict_and_round_trip() -> None:
    model = _trained_model()
    model.ingest_fact("未知生物の分類は鳥類である。", source_id="分類資料1")
    model.ingest_fact("未知生物の分類は爬虫類である。", source_id="分類資料2")
    model.ingest_fact("爬虫類の体温は変温である。", source_id="爬虫類生理資料")
    conflict = model.reply("未知生物の体温特性は何ですか？")
    assert conflict.mechanism == "goal-rule-evidence-conflict"

    model.ingest_fact(
        "最新情報:未知生物の分類は鳥類である。",
        source_id="訂正分類資料",
        revision=True,
    )
    restored = SPARCHS13Model.from_bytes(model.to_bytes())
    revised = restored.reply("未知生物の生理区分は何ですか？")
    assert revised.text.startswith("恒温型です")
    report = restored.goal_rules.report()
    assert report["rules"] == 2
    assert report["forward_materialisation_used"] is False
    assert report["global_entity_scan_used"] is False
    assert report["global_edge_scan_used"] is False
    assert report["global_rule_scan_used"] is False
