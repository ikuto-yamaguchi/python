from minimal_predictive_lm.sparc_hs4_experiment import configured_model


def test_weak_qa_unknown_and_cross_domain_reasoning() -> None:
    model = configured_model()
    assert model.reply("イタリアの首都は何ですか？").text == "ローマです。"
    assert model.reply("犬は生物に分類されますか？").text.startswith("犬は生物の関係")
    assert model.reply("落雷は装置停止につながりますか？").text.startswith("落雷は装置停止の関係")
    unknown = model.reply("未知国の首都は何ですか？")
    assert unknown.mechanism == "calibrated-unknown"
    assert "教えて" in unknown.text
