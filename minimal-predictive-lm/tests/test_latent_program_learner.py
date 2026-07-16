from minimal_predictive_lm.latent_program_learner import (
    GroundedLatentProgramLearner,
    GroundedTransition,
    PredictiveStateInducer,
)
from minimal_predictive_lm.sparc_latent_program_gate import (
    _datasets,
    _state_sequence,
    _unlabelled_corpus,
)


def test_state_edits_induce_operation_without_labels() -> None:
    row = GroundedTransition(
        "口座甲 から 口座乙 へ 7 移す",
        {"口座甲": 30, "口座乙": 10},
        {"口座甲": 23, "口座乙": 17},
    )
    plan = GroundedLatentProgramLearner.derive_plan(row)
    assert plan.operation == "transfer"
    assert plan.target == "口座甲"
    assert plan.destination == "口座乙"
    assert plan.value == 7


def test_withheld_expression_transfers_through_unlabelled_context() -> None:
    training, heldout = _datasets()
    model = GroundedLatentProgramLearner()
    assert model.fit(training, unlabelled_sentences=_unlabelled_corpus()) == 4
    for row in heldout[:32]:
        assert model.infer(row.text, row.before).plan == model.derive_plan(row)


def test_serialisation_preserves_latent_programs() -> None:
    training, heldout = _datasets()
    model = GroundedLatentProgramLearner()
    model.fit(training, unlabelled_sentences=_unlabelled_corpus())
    restored = GroundedLatentProgramLearner.from_bytes(model.to_bytes())
    assert (
        restored.infer(heldout[0].text, heldout[0].before).plan
        == model.derive_plan(heldout[0])
    )


def test_predictive_state_is_proposed_without_cue_names() -> None:
    sequence = _state_sequence(
        11,
        "開始甲",
        "開始乙",
        "結果甲",
        "結果乙",
        "質問",
        ("雑音1", "雑音2", "雑音3"),
    )
    result = PredictiveStateInducer(max_candidates=128).fit(
        sequence,
        query_token="質問",
    )
    assert set(result.cue_pair or ()) == {"開始甲", "開始乙"}
    assert result.description_length_gain > 100.0
