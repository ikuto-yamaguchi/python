from minimal_predictive_lm.femi import (
    Example,
    factorization_report,
    induce_lookup_rule,
    induce_numeric_rule,
    run_experiment,
)


def test_numeric_addition_induction():
    rule = induce_numeric_rule([
        Example("2と3の和は？", "5です。"),
        Example("8と4の和は？", "12です。"),
    ])
    assert rule is not None
    assert rule.expression.name == "add"
    assert rule.execute("100と23の和は？") == "123です。"


def test_numeric_algebra_induction():
    rule = induce_numeric_rule([
        Example("x+3=8のxは？", "5です。"),
        Example("x+5=12のxは？", "7です。"),
    ])
    assert rule is not None
    assert rule.expression.name == "sub10"
    assert rule.execute("x+17=45のxは？") == "28です。"


def test_lookup_induction():
    rule = induce_lookup_rule([
        Example("日本の首都は？", "東京です。"),
        Example("フランスの首都は？", "パリです。"),
    ])
    assert rule is not None
    assert rule.execute("フランスの首都は？") == "パリです。"


def test_factorized_scaling():
    report = factorization_report([2] * 32)
    assert report.information_lower_bound_bits == 32
    assert report.factorized_state_bits == 32
    assert report.transition_entry_reduction > 1_000_000


def test_frozen_experiment():
    result = run_experiment()
    assert result["passed"] is True
    assert result["evaluation"]["accuracy"] == 1.0
    assert result["neural_network_used"] is False
    assert "not Japanese-high-school-level intelligence" in result["claim_boundary"]
