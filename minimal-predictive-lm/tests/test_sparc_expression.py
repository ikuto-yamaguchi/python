from minimal_predictive_lm.sparc_expression import SPARCHS6Model, SparseExpressionBank


def test_synthesizes_program_not_in_named_library() -> None:
    bank = SparseExpressionBank()
    expression = bank.teach(
        [
            ("1箱に8個入りの品を5箱と予備3個用意すると全部で何個ですか？", 43),
            ("1箱に6個入りの品を4箱と予備2個用意すると全部で何個ですか？", 26),
            ("1箱に7個入りの品を3箱と予備5個用意すると全部で何個ですか？", 26),
        ]
    )
    assert expression.cost == 5
    answer = bank.solve(
        "1箱に9個入りの品を6箱と予備4個用意すると全部で何個ですか？"
    )
    assert answer is not None
    assert answer.text.startswith("58です")
    assert "式は" in answer.text


def test_multiple_expression_trees_and_persistence() -> None:
    model = SPARCHS6Model()
    model.teach_expression(
        [
            ("1200円から送料200円を引き4人で分けると1人何円ですか？", 250),
            ("900円から送料100円を引き4人で分けると1人何円ですか？", 200),
            ("1500円から送料300円を引き6人で分けると1人何円ですか？", 200),
        ]
    )
    model.teach_expression(
        [
            ("縦5cm横8cmの長方形の周囲は何cmですか？", 26),
            ("縦4cm横7cmの長方形の周囲は何cmですか？", 22),
            ("縦6cm横9cmの長方形の周囲は何cmですか？", 30),
        ]
    )
    assert model.reply(
        "1800円から送料300円を引き5人で分けると1人何円ですか？"
    ).text.startswith("300です")
    assert model.reply(
        "縦7cm横10cmの長方形の周囲は何cmですか？"
    ).text.startswith("34です")
    restored = SPARCHS6Model.from_bytes(model.to_bytes())
    assert restored.reply(
        "縦8cm横12cmの長方形の周囲は何cmですか？"
    ).text.startswith("40です")
