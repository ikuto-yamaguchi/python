from minimal_predictive_lm.sparc_hs2 import SPARCHS2Model


def test_combined_chat_learning_reasoning_and_fallback() -> None:
    model = SPARCHS2Model().fit_dialogues([("こんにちは", "こんにちは。")])
    assert model.reply("こんにちは").text == "こんにちは。"

    assert "覚えました" in model.reply("アキラは高校生です").text
    model.reply("高校生は学生です")
    model.reply("学生は人です")
    result = model.reply("アキラは人ですか？")
    assert result.text.startswith("はい")
    assert len(result.path) == 3

    restored = SPARCHS2Model.from_bytes(model.to_bytes())
    assert restored.reply("アキラは人ですか？").text.startswith("はい")
