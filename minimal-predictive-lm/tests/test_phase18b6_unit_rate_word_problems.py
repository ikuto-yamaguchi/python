from minimal_predictive_lm.phase18b6_unit_rate_word_problems import (
    UnitRateCompiler,
    counterfactual_total_changes_answer,
    equal_rates_abstain,
    evaluate,
    fractional_or_negative_counts_abstain,
    heldout,
    numeric_distractor_abstains,
    run,
    tampered_proof_is_rejected,
    unit_mismatch_abstains,
)


def test_unseen_domains_clause_orders_and_paraphrases_are_exact():
    model = UnitRateCompiler()
    assert len(heldout()) == 12
    assert evaluate(model) == (1.0, 1.0, 1.0)


def test_invalid_count_problems_abstain():
    model = UnitRateCompiler()
    assert equal_rates_abstain(model)
    assert fractional_or_negative_counts_abstain(model)
    assert unit_mismatch_abstains(model)
    assert numeric_distractor_abstains(model)


def test_proof_and_counterfactual_controls():
    model = UnitRateCompiler()
    assert tampered_proof_is_rejected(model)
    assert counterfactual_total_changes_answer(model)


def test_fixed_compiler_cost_is_not_hidden_as_learned_payload():
    model = UnitRateCompiler()
    assert model.payload_bits == 0
    payload = run()
    assert payload["resources"]["source_bytes"] > 0
    assert payload["campaign"]["learned_parser"] is False


def test_all_phase18b6_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["high_school_intelligence"] is False
