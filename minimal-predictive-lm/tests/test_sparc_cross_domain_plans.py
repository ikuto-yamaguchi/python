from minimal_predictive_lm.sparc_cross_domain_plans import SPARCHS11Model
from minimal_predictive_lm.sparc_role_induction_v3 import SPARCHS10ModelV3


def _add_vehicle(model: SPARCHS11Model, name: str, speed: float, hours: float) -> None:
    model.ingest_fact(
        f"{name}の速度は時速{speed:g}kmである。",
        source_id=f"{name}速度資料",
    )
    model.ingest_fact(
        f"{name}の運転時間は{hours:g}時間である。",
        source_id=f"{name}時間資料",
    )


def _trained_model() -> SPARCHS11Model:
    model = SPARCHS11Model(SPARCHS10ModelV3())
    _add_vehicle(model, "列車A", 60, 2)
    _add_vehicle(model, "列車B", 45, 3)
    _add_vehicle(model, "列車C", 80, 1.5)
    model.teach_plan(
        [
            ("列車Aの移動距離は何kmですか？", "120km"),
            ("列車Bの移動距離は何kmですか？", "135km"),
            ("列車Cの移動距離は何kmですか？", "120km"),
        ]
    )
    return model


def test_cross_document_plan_uses_two_local_facts_and_sources() -> None:
    model = _trained_model()
    _add_vehicle(model, "列車D", 72, 2.5)
    reply = model.reply("列車Dの移動距離は何kmですか？")
    assert reply.mechanism == "learned-cross-domain-plan"
    assert reply.text.startswith("180kmです")
    assert "列車D速度資料" in reply.text
    assert "列車D時間資料" in reply.text
    assert reply.active_bits == 2
    assert model.plans.last_fact_reads == 2
    assert model.plans.report()["plans"] == 1


def test_conflict_refuses_then_revision_reuses_same_plan() -> None:
    model = _trained_model()
    model.ingest_fact("列車Fの速度は時速60kmである。", source_id="旧速度1")
    model.ingest_fact("列車Fの速度は時速70kmである。", source_id="旧速度2")
    model.ingest_fact("列車Fの運転時間は2時間である。", source_id="時間資料")
    conflict = model.reply("列車Fの移動距離は何kmですか？")
    assert conflict.mechanism == "cross-domain-evidence-conflict"
    assert "確定できません" in conflict.text

    model.ingest_fact(
        "最新情報:列車Fの速度は時速80kmである。",
        source_id="訂正速度資料",
        revision=True,
    )
    revised = model.reply("列車Fの移動距離は何kmですか？")
    assert revised.text.startswith("160kmです")
    assert "訂正速度資料" in revised.text
    assert model.plans.report()["plans"] == 1


def test_plan_and_episode_indices_survive_round_trip() -> None:
    model = _trained_model()
    _add_vehicle(model, "列車D", 72, 2.5)
    restored = SPARCHS11Model.from_bytes(model.to_bytes())
    reply = restored.reply("列車Dの移動距離は何kmですか？")
    assert reply.text.startswith("180kmです")
    report = restored.plans.report()
    assert report["plans"] == 1
    assert report["global_subject_scan_used"] is False
    assert report["global_episode_scan_used"] is False
    assert report["global_plan_scan_used"] is False
