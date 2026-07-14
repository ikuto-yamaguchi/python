from minimal_predictive_lm.femi_mgsm import (
    MathRow,
    ProgramSelector,
    character_features,
    extract_numbers,
    parse_expression,
    synthesize_expressions,
)


def test_number_extraction_and_normalization_features():
    assert tuple(map(int, extract_numbers("1,200円の50%"))) == (1200, 50)
    features = character_features("23個から8個減りました")
    assert "COUNT=2" in features


def test_expression_round_trip():
    expression = parse_expression("(- n1 n0)")
    assert expression.key == "(- n1 n0)"
    assert expression.evaluate(extract_numbers("17と45")) == 28


def test_synthesis_finds_multistep_program():
    result = synthesize_expressions(
        "5個の箱に3個ずつあり、さらに2個あります。全部でいくつ？",
        17,
    )
    assert any(
        expression.evaluate(extract_numbers("5 3 2")) == 17
        for expression in result.expressions
    )
    assert result.expansions > 0


def test_selector_generalizes_public_style_templates():
    rows = [
        MathRow("5個の箱に3個ずつあり、さらに2個あります。", 17),
        MathRow("4個の袋に6個ずつあり、さらに1個あります。", 25),
        MathRow("7個の皿に2個ずつあり、さらに5個あります。", 19),
        MathRow("30個から8個使い、その後4個使いました。", 18),
        MathRow("50個から9個使い、その後6個使いました。", 35),
    ]
    model = ProgramSelector.fit(rows)
    prediction, attempts = model.predict("8個の箱に7個ずつあり、さらに3個あります。")
    assert prediction == 59
    assert attempts >= 1
    assert model.serialized_bytes() > 0
