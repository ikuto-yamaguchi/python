from minimal_predictive_lm.sparc_counterexamples import SPARCHS14Model
from minimal_predictive_lm.sparc_cross_domain_plans_v2 import SPARCHS11ModelV2
from minimal_predictive_lm.sparc_goal_rules import SPARCHS13Model
from minimal_predictive_lm.sparc_relational_plans import SPARCHS12Model


def _base_rule_model() -> SPARCHS14Model:
    model = SPARCHS14Model(
        SPARCHS13Model(SPARCHS12Model(SPARCHS11ModelV2()))
    )
    model.ingest_fact("哺乳類の標準活動は活動である。", source_id="哺乳類活動資料")
    for animal in ("クマA", "クマB", "クマC"):
        model.ingest_fact(
            f"{animal}の分類は哺乳類である。", source_id=f"{animal}分類資料"
        )
        model.ingest_fact(
            f"{animal}の活動状態は活動である。", source_id=f"{animal}直接観測"
        )
    model.base.teach_rule(
        [
            ("クマAの活動状態は何ですか？", "活動です"),
            ("クマBの活動状態は何ですか？", "活動です"),
            ("クマCの活動状態は何ですか？", "活動です"),
        ]
    )
    return model


def _add_validation_subject(
    model: SPARCHS14Model,
    subject: str,
    season: str,
    observed: str,
) -> None:
    model.ingest_fact(
        f"{subject}の分類は哺乳類である。", source_id=f"{subject}分類資料"
    )
    model.ingest_fact(
        f"{subject}の季節状態は{season}である。", source_id=f"{subject}季節資料"
    )
    model.ingest_fact(
        f"{subject}の活動状態は{observed}である。", source_id=f"{subject}観測資料"
    )


def _validated_model() -> SPARCHS14Model:
    model = _base_rule_model()
    for subject in ("支持A", "支持B", "支持C"):
        _add_validation_subject(model, subject, "通常", "活動")
    for subject in ("反例A", "反例B", "反例C"):
        _add_validation_subject(model, subject, "冬眠中", "休止")
    model.validate_rules(
        [
            *((f"{subject}の活動状態は何ですか？", "活動です") for subject in ("支持A", "支持B", "支持C")),
            *((f"{subject}の活動状態は何ですか？", "休止です") for subject in ("反例A", "反例B", "反例C")),
        ]
    )
    return model


def test_counterexamples_induce_local_exclusion_guard() -> None:
    model = _validated_model()
    report = model.validator.report()
    assert report["supports"] == 3
    assert report["refutations"] == 3
    assert report["exclusion_guards"] == 1
    state = next(iter(model.validator.states.values()))
    assert len(state.exclusion_guards) == 1
    guard = state.exclusion_guards[0]
    assert guard.relation == "季節状態"
    assert guard.value == "冬眠中"


def test_guard_blocks_unseen_exception_but_allows_normal_case() -> None:
    model = _validated_model()
    model.ingest_fact("未知通常の分類は哺乳類である。", source_id="通常分類資料")
    model.ingest_fact("未知通常の季節状態は通常である。", source_id="通常季節資料")
    model.ingest_fact("未知冬眠の分類は哺乳類である。", source_id="冬眠分類資料")
    model.ingest_fact("未知冬眠の季節状態は冬眠中である。", source_id="冬眠季節資料")

    normal = model.reply("未知通常の活動状態は何ですか？")
    blocked = model.reply("未知冬眠の活動状態は何ですか？")
    assert normal.text.startswith("活動です")
    assert normal.mechanism == "goal-directed-learned-rule"
    assert blocked.mechanism == "counterexample-guarded-rule"
    assert "季節状態=冬眠中" in blocked.text
    assert "確定できません" in blocked.text
    assert model.validator.last_guard_reads == 1


def test_direct_observation_overrides_guard_and_persists() -> None:
    model = _validated_model()
    model.ingest_fact("観測個体の分類は哺乳類である。", source_id="観測分類")
    model.ingest_fact("観測個体の季節状態は冬眠中である。", source_id="観測季節")
    model.ingest_fact("観測個体の活動状態は休止である。", source_id="直接観測")
    reply = model.reply("観測個体の活動状態は何ですか？")
    assert reply.text.startswith("休止です")
    assert reply.mechanism != "counterexample-guarded-rule"

    restored = SPARCHS14Model.from_bytes(model.to_bytes())
    restored.ingest_fact("復元冬眠の分類は哺乳類である。", source_id="復元分類")
    restored.ingest_fact("復元冬眠の季節状態は冬眠中である。", source_id="復元季節")
    blocked = restored.reply("復元冬眠の活動状態は何ですか？")
    assert blocked.mechanism == "counterexample-guarded-rule"
    assert restored.validator.report()["exclusion_guards"] == 1
    assert restored.validator.report()["global_exception_scan_used"] is False
