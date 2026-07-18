from minimal_predictive_lm.synthetic_causal_curriculum import build_synthetic_causal_curriculum


def test_procedural_causal_worlds_have_separate_surfaces() -> None:
    curriculum = build_synthetic_causal_curriculum()
    assert len(curriculum.train) >= 80
    assert len(curriculum.holdout) >= 30
    train_text = " ".join(row.raw_question for row in curriculum.train)
    holdout_text = " ".join(row.raw_question for row in curriculum.holdout)
    for name in ("Ivo", "Juna", "Kian", "Lumi"):
        assert name not in train_text
        assert name in holdout_text
    assert {row.answer_index for row in curriculum.train} == {0, 1}
    assert {row.answer_index for row in curriculum.holdout} == {0, 1}
