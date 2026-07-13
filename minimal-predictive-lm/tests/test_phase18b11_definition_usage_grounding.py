from minimal_predictive_lm.phase18b11_definition_usage_grounding import (
    contradictory_definitions_are_rejected,
    definitions_alone_are_ambiguous,
    evaluate,
    exact_usage_surface_memorizer_coverage,
    induce,
    negative_definition_is_causally_used,
    no_previous_anchor_overlap,
    run,
    unanchored_alias_cycle_is_rejected,
    unknown_and_ambiguous_tokens_abstain,
)


def test_definitions_deliberately_leave_rate_value_exchangeable():
    assert definitions_alone_are_ambiguous()


def test_usage_examples_resolve_one_model_and_program_pair():
    model, fit = induce()
    assert fit["all_hypotheses"] == 8748
    assert fit["after_definition_constraints"] == 24
    assert fit["zero_error_after_usage"] == 1
    assert dict(model.token_roles) == {
        "ゼルク": "COUNT",
        "ノヴァ": "COUNT",
        "ミルテ": "RATE",
        "ラゴン": "RATE",
        "セフィ": "VALUE",
        "トゥラ": "VALUE",
    }
    assert (model.count_program, model.value_program) == ("SUM", "WEIGHTED_SUM")


def test_definition_aliases_transfer_to_unseen_domains():
    model, _ = induce()
    assert evaluate(model) == (1.0, 1.0, 1.0)


def test_conflict_cycle_unknown_and_ambiguous_cases_abstain():
    model, _ = induce()
    assert unanchored_alias_cycle_is_rejected()
    assert contradictory_definitions_are_rejected()
    assert unknown_and_ambiguous_tokens_abstain(model)


def test_negation_and_non_memorization_gates_are_active():
    assert negative_definition_is_causally_used()
    assert exact_usage_surface_memorizer_coverage() == 0.0
    assert no_previous_anchor_overlap()


def test_all_phase18b11_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["free_japanese_definition_understanding"] is False
    assert payload["claim_boundary"]["high_school_intelligence"] is False
