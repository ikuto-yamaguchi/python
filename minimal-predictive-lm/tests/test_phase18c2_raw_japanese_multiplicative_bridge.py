from minimal_predictive_lm.phase18c2_raw_japanese_multiplicative_bridge import (
    ambiguous_mass_lexicon_rejected,
    evaluate,
    induce,
    negative_controls,
    number_unit_bag_upper_bound,
    run,
    whole_text_memorizer_coverage,
)


def test_lexicon_is_uniquely_induced():
    model, fit = induce()
    assert fit == {"lexical_hypotheses": 16, "survivors": 1, "examples": 18}
    roles = dict(model.cue_roles)
    assert roles["溶液全体"] == "SOLUTION"
    assert roles["液体の量"] == "SOLUTION"
    assert roles["溶けた物質"] == "SOLUTE"
    assert roles["中の成分"] == "SOLUTE"


def test_three_relations_and_all_unknown_positions_are_exact():
    model, _ = induce()
    assert evaluate(model) == (1.0, 1.0, 1.0)


def test_ambiguous_lexicon_and_invalid_inputs_abstain():
    model, _ = induce()
    assert ambiguous_mass_lexicon_rejected()
    assert all(negative_controls(model).values())


def test_surface_and_number_bag_baselines_cannot_solve_suite():
    model, _ = induce()
    assert whole_text_memorizer_coverage() == 0.0
    assert number_unit_bag_upper_bound(model) == 0.5


def test_all_phase18c2_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["free_japanese_parsing"] is False
    assert payload["claim_boundary"]["high_school_intelligence"] is False
