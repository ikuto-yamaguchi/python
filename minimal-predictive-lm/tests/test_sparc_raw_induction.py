from minimal_predictive_lm.sparc_raw_induction import RawCurriculumModel


def raw_corpus() -> list[str]:
    return [
        "東京は日本の首都です",
        "パリはフランスの首都です",
        "ローマはイタリアの首都です",
        "ベルリンはドイツの首都です",
        "マドリードはスペインの首都です",
        "猫は哺乳類に分類されます",
        "哺乳類は動物に分類されます",
        "猫は動物に分類されます",
        "犬は哺乳類に分類されます",
        "犬は動物に分類されます",
        "動物は生物に分類されます",
        "猫は生物に分類されます",
        "犬は生物に分類されます",
    ]


def test_raw_schema_mining_weak_qa_and_persistence() -> None:
    model = RawCurriculumModel().fit_raw(raw_corpus())
    assert model.miner.report.schemas >= 2
    assert model.align_qa("日本の首都は何ですか？", "東京")
    assert model.align_qa("フランスの首都は何ですか？", "パリ")
    assert model.align_qa("猫は生物に分類されますか？", "はい")
    capital = model.reply("イタリアの首都は何ですか？")
    assert capital.text == "ローマです。"
    taxonomy = model.reply("犬は生物に分類されますか？")
    assert taxonomy.text.startswith("犬は生物の関係")
    unknown = model.reply("未知国の首都は何ですか？")
    assert unknown.mechanism == "calibrated-unknown"
    restored = RawCurriculumModel.from_bytes(model.to_bytes())
    assert restored.reply("イタリアの首都は何ですか？").text == "ローマです。"
