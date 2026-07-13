from fractions import Fraction

from minimal_predictive_lm.phase18c1_multiplicative_relation_core import (
    ambiguous_orientation_rejected,
    constraint_order_invariant,
    evaluate,
    induce,
    multistep_chain,
    negative_controls,
    run,
)


def test_relation_orientation_is_uniquely_induced():
    model, fit = induce()
    assert fit == {"hypotheses": 27, "survivors": 1, "examples": 6}
    assert dict(model.product_slots) == {"速度関係": 0, "濃度関係": 2, "価格関係": 1}


def test_any_one_of_three_quantities_can_be_unknown():
    model, _ = induce()
    assert evaluate(model) == (1.0, 1.0, 1.0)


def test_two_equation_chain_is_exact_and_verified():
    value, steps, verified = multistep_chain()
    assert value == Fraction(720)
    assert steps == 2
    assert verified


def test_order_ambiguity_dimensions_and_zero_division_are_guarded():
    assert constraint_order_invariant()
    assert ambiguous_orientation_rejected()
    assert all(negative_controls().values())


def test_all_phase18c1_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["new_math_family_beyond_linear_constraints"]
    assert payload["claim_boundary"]["general_nonlinear_solver"] is False
    assert payload["claim_boundary"]["high_school_intelligence"] is False
