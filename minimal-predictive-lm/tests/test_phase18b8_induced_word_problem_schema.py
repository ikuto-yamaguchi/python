from minimal_predictive_lm.phase18b8_induced_word_problem_schema import (
    COUNT_CUES,
    RATE_CUES,
    VALUE_CUES,
    ambiguous_calibration_is_rejected,
    evaluate,
    induce,
    run,
    schema_intervention_changes_prediction,
    unit_mismatch_abstains,
    unknown_and_extra_cues_abstain,
)


def test_schema_is_uniquely_induced_from_demonstrations():
    model, fit = induce()
    assert fit["errors"] == 0
    assert fit["second"] > 0
    assert dict(model.global_roles) == {**{x: "COUNT" for x in COUNT_CUES}, **{x: "VALUE" for x in VALUE_CUES}}
    assert all(dict(model.rate_active)[x] for x in RATE_CUES)
    assert (model.count_program, model.value_program) == ("SUM", "WEIGHTED_SUM")


def test_unseen_domains_and_combinations_are_exact():
    model, _ = induce()
    assert evaluate(model) == (1.0, 1.0, 1.0)


def test_ambiguous_calibration_is_rejected():
    assert ambiguous_calibration_is_rejected()


def test_unknown_extra_and_unit_mismatch_abstain():
    model, _ = induce()
    assert unknown_and_extra_cues_abstain(model)
    assert unit_mismatch_abstains(model)


def test_schema_role_is_causally_used():
    model, _ = induce()
    assert schema_intervention_changes_prediction(model)


def test_all_phase18b8_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["free_japanese_word_problems"] is False
    assert payload["claim_boundary"]["high_school_intelligence"] is False
