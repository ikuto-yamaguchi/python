from minimal_predictive_lm.sparc_hs3_experiment import configured_model
from minimal_predictive_lm.sparc_schema import SPARCHS3Model


def test_learned_schema_multihop_and_composition() -> None:
    model = configured_model()
    for sentence in [
        "アキラは高校生に分類されます",
        "高校生は学生に分類されます",
        "学生は人に分類されます",
        "人は生物に分類されます",
    ]:
        reply = model.reply(sentence)
        assert reply.mechanism == "learned-surface-schema"
    result = model.reply("アキラは生物に分類されますか")
    assert result.mechanism == "learned-schema-compositional-reasoning"
    assert result.text.startswith("アキラは生物に分類できます")
    assert len(result.path) == 4
    assert "根拠は" in result.text


def test_learned_cause_comparison_and_persistence() -> None:
    model = configured_model()
    for sentence in [
        "落雷によって停電が起きました",
        "停電によって冷却停止が起きました",
        "冷却停止によって装置停止が起きました",
    ]:
        model.reply(sentence)
    cause = model.reply("落雷は装置停止につながりますか")
    assert cause.text.startswith("落雷は装置停止につながる原因")

    for sentence in [
        "Aの方がBより高いです",
        "Bの方がCより高いです",
        "Cの方がDより高いです",
    ]:
        model.reply(sentence)
    comparison = model.reply("AはDより高いですか")
    assert comparison.text.startswith("AはDより高い")

    restored = SPARCHS3Model.from_bytes(model.to_bytes())
    assert restored.reply("落雷は装置停止につながりますか").text.startswith("落雷は装置停止")
