from minimal_predictive_lm.phase18b5_affine_inequality_reasoning import (
    boundary_free_calibration_is_nonidentifying,
    evaluate,
    heldout,
    induce_model,
    run,
    tampered_interval_is_rejected,
    unknown_relation_abstains,
)


def test_four_relation_words_are_induced_from_24_permutations():
    model, fit = induce_model()
    assert dict(model.relation_map) == {
        "以上": "GE", "以下": "LE", "より大きい": "GT", "より小さい": "LT"
    }
    assert fit["candidates"] == 24
    assert fit["errors"] == 0
    assert fit["second"] > 0


def test_negative_coefficients_open_closed_point_and_empty_intervals():
    model, _ = induce_model()
    accuracy, coverage, verified = evaluate(model)
    assert (accuracy, coverage, verified) == (1.0, 1.0, 1.0)
    intervals = [expected for _, expected in heldout()]
    assert any(i.empty for i in intervals)
    assert any(i.lower == i.upper and not i.empty for i in intervals)
    assert any((i.lower is not None and not i.lower_closed) or (i.upper is not None and not i.upper_closed) for i in intervals)


def test_boundary_free_examples_do_not_identify_strictness():
    assert boundary_free_calibration_is_nonidentifying()


def test_tampered_interval_and_unknown_relation_are_rejected():
    model, _ = induce_model()
    assert tampered_interval_is_rejected(model)
    assert unknown_relation_abstains(model)


def test_all_phase18b5_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["high_school_mathematics"] is False
