from minimal_predictive_lm.sparc_programs import SPARCHS5Model, SparseProgramBank


def test_program_induction_and_transfer() -> None:
    bank = SparseProgramBank()
    result = bank.teach(
        [
            ("時速60kmで2時間進む距離は何kmですか？", 120),
            ("時速45kmで3時間進む距離は何kmですか？", 135),
            ("時速80kmで1.5時間進む距離は何kmですか？", 120),
        ]
    )
    assert result.program_name in {"mul2", "rate_times_time"}
    answer = bank.solve("時速72kmで2.5時間進む距離は何kmですか？")
    assert answer is not None
    assert answer.text.startswith("180です")
    assert bank.last_candidates <= 2


def test_multiple_curriculum_programs_and_persistence() -> None:
    model = SPARCHS5Model()
    model.teach_math(
        [
            ("800円の商品を25%引きで買うと何円ですか？", 600),
            ("1200円の商品を10%引きで買うと何円ですか？", 1080),
            ("500円の商品を20%引きで買うと何円ですか？", 400),
        ]
    )
    model.teach_math(
        [
            ("70点と80点と90点の平均は何点ですか？", 80),
            ("60点と75点と90点の平均は何点ですか？", 75),
            ("40点と50点と60点の平均は何点ですか？", 50),
        ]
    )
    model.teach_math(
        [
            ("3x+5=20のxは何ですか？", 5),
            ("4x+8=40のxは何ですか？", 8),
            ("5x+10=60のxは何ですか？", 10),
        ]
    )
    assert model.reply("2000円の商品を15%引きで買うと何円ですか？").text.startswith("1700です")
    assert model.reply("55点と70点と85点の平均は何点ですか？").text.startswith("70です")
    assert model.reply("6x+12=54のxは何ですか？").text.startswith("7です")
    restored = SPARCHS5Model.from_bytes(model.to_bytes())
    assert restored.reply("1000円の商品を30%引きで買うと何円ですか？").text.startswith("700です")
