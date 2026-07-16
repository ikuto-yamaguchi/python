from minimal_predictive_lm.sparc_reasoning import SparseRelationalCortex


def test_multihop_negative_and_property() -> None:
    model = SparseRelationalCortex("ci")
    for text in ["アキラは高校生です", "高校生は学生です", "学生は人です", "人は生物です"]:
        assert model.learn_text(text)
    result = model.answer("アキラは生物ですか？")
    assert result is not None
    assert result.text.startswith("はい")
    assert len(result.path) == 4
    assert result.nodes_activated <= 8

    model.learn_text("ペンギンは哺乳類ではありません")
    negative = model.answer("ペンギンは哺乳類ですか？")
    assert negative is not None
    assert negative.text.startswith("いいえ")

    model.learn_text("富士山の高さは3776メートルです")
    prop = model.answer("富士山の高さは何ですか？")
    assert prop is not None
    assert "3776メートル" in prop.text


def test_cause_comparison_persistence_and_bounds() -> None:
    model = SparseRelationalCortex("ci")
    for text in ["落雷が原因で停電です", "停電が原因で冷却停止です", "冷却停止が原因で装置停止です"]:
        assert model.learn_text(text)
    cause = model.answer("落雷は装置停止の原因ですか？")
    assert cause is not None
    assert cause.text.startswith("はい")
    assert len(cause.path) == 3

    for text in ["AはBより高いです", "BはCより高いです", "CはDより高いです"]:
        assert model.learn_text(text)
    comparison = model.answer("AとDではどちらが高いですか？")
    assert comparison is not None
    assert comparison.text.startswith("Aの方")

    for index in range(50):
        model.learn_text(f"概念{index}は概念{index + 1}です")
    bounded = model.answer("概念0は概念8ですか？")
    assert bounded is not None
    assert bounded.nodes_activated <= model.profile.max_activations
    assert bounded.edges_inspected <= model.profile.max_edges_per_query
    assert model.answer("概念0は概念20ですか？") is None

    restored = SparseRelationalCortex.from_bytes(model.to_bytes())
    again = restored.answer("落雷は装置停止の原因ですか？")
    assert again is not None
    assert again.text.startswith("はい")
