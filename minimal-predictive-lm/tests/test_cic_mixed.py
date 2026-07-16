from minimal_predictive_lm.cic_artifact import CICArtifact
from minimal_predictive_lm.cic_choice_data import (
    ChoiceExample,
    parse_choice_question,
    stable_choice_split,
)
from minimal_predictive_lm.cic_choice_model import (
    QuantizedChoiceMechanism,
    choice_accuracy,
    train_choice_mechanism,
    train_legacy_choice_mechanism,
)
from minimal_predictive_lm.cic_mixed_artifact import MixedCICArtifact


def test_parse_choice_question() -> None:
    text = "問題：水を出すときに捻るものは？\n(0)蛇口\n(1)ハンドル\n(2)流し\n解答："
    assert parse_choice_question(text) == (
        "水を出すときに捻るものは？",
        ("蛇口", "ハンドル", "流し"),
    )


def test_choice_split_is_deterministic() -> None:
    rows = [
        ChoiceExample(f"問題{i}", f"問題{i}", ("a", "b"), i % 2)
        for i in range(40)
    ]
    first = stable_choice_split(rows)
    second = stable_choice_split(rows)
    assert first == second
    assert len(first[0]) + len(first[1]) == len(rows)


def test_margin_choice_model_survives_quantization() -> None:
    rows = []
    for index in range(12):
        rows.append(
            ChoiceExample(
                f"果物{index}",
                "食べられる果物は？",
                ("りんご", "自動車"),
                0,
            )
        )
        rows.append(
            ChoiceExample(
                f"乗り物{index}",
                "道路を走る乗り物は？",
                ("桃", "自動車"),
                1,
            )
        )
    legacy = train_legacy_choice_mechanism(rows, epochs=4, dimensions=4096)
    raw = train_choice_mechanism(rows, epochs=4, dimensions=4096)
    quantized = QuantizedChoiceMechanism.from_raw(raw, top_weights=1024)
    assert choice_accuracy(legacy, rows)[0] == len(rows)
    assert choice_accuracy(raw, rows)[0] == len(rows)
    assert choice_accuracy(quantized, rows)[0] == len(rows)


def test_mixed_artifact_roundtrip() -> None:
    rows = [
        ChoiceExample("果物は？", "果物は？", ("りんご", "車"), 0),
        ChoiceExample("乗り物は？", "乗り物は？", ("桃", "電車"), 1),
    ] * 4
    raw = train_choice_mechanism(rows, epochs=4, dimensions=1024)
    choice = QuantizedChoiceMechanism.from_raw(raw, top_weights=512)
    arithmetic = CICArtifact(4096, {}, {"variant": "empty-test"})
    artifact = MixedCICArtifact(arithmetic, choice, {"test": True})
    restored = MixedCICArtifact.from_bytes(artifact.to_bytes())
    question = "問題：果物は？\n(0)りんご\n(1)車\n解答："
    assert restored.predict(question).answer == artifact.predict(question).answer
    assert restored.metadata == {"test": True}
