import pytest

from minimal_predictive_lm.sparc_units import (
    LENGTH,
    TIME,
    SPARCHS7Model,
    SparseTypedPlanBank,
    synthesize_typed_expression,
)


def test_unit_conversion_and_surface_transfer() -> None:
    bank = SparseTypedPlanBank()
    expression = bank.teach(
        [
            ("時速60kmで2時間進む距離は何kmですか？", "120km"),
            ("時速45kmで3時間進む距離は何kmですか？", "135km"),
            ("時速80kmで1.5時間進む距離は何kmですか？", "120km"),
        ]
    )
    assert expression.semantic_states <= 32
    assert bank.solve(
        "時速90kmで40分進む距離は何kmですか？"
    ).text.startswith("60kmです")

    bank.link_surface(
        "秒速1mで2秒進む距離は何mですか？", expression, support=3
    )
    assert bank.solve(
        "秒速12mで25秒進む距離は何mですか？"
    ).text.startswith("300mです")


def test_mixed_area_invalid_dimension_and_persistence() -> None:
    model = SPARCHS7Model()
    model.teach_units(
        [
            ("底辺100cm、高さ2mの長方形の面積は何m²ですか？", "2m²"),
            ("底辺50cm、高さ4mの長方形の面積は何m²ですか？", "2m²"),
            ("底辺250cm、高さ3mの長方形の面積は何m²ですか？", "7.5m²"),
        ]
    )
    assert model.reply(
        "底辺120cm、高さ2.5mの長方形の面積は何m²ですか？"
    ).text.startswith("3m²です")

    with pytest.raises(ValueError):
        synthesize_typed_expression(
            [
                ((1.0, 2.0), (LENGTH, TIME), 3.0, LENGTH),
                ((2.0, 5.0), (LENGTH, TIME), 7.0, LENGTH),
                ((4.0, 1.0), (LENGTH, TIME), 5.0, LENGTH),
            ],
            max_cost=7,
        )

    restored = SPARCHS7Model.from_bytes(model.to_bytes())
    assert restored.reply(
        "底辺200cm、高さ1.5mの長方形の面積は何m²ですか？"
    ).text.startswith("3m²です")
