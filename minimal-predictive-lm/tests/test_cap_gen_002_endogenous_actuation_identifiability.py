from minimal_predictive_lm.cap_gen_002_endogenous_actuation_identifiability import (
    action_quotient_resource_comparison,
    classify_surface_roles,
    group_behavioral_action_surfaces,
    make_identifiable_fixture,
    make_no_policy_shift_fixture,
    passive_actuation_counterexample,
    run_theory_gate,
)


def test_passive_stream_cannot_identify_which_spans_are_actuations():
    controlled, autonomous = passive_actuation_counterexample()

    assert controlled.raw_trace == autonomous.raw_trace
    assert controlled.actuation_positions != autonomous.actuation_positions
    assert controlled.actuation_positions == frozenset({1, 3, 5})
    assert autonomous.actuation_positions == frozenset()


def test_policy_shift_plus_invariant_effect_identifies_action_like_surfaces():
    table = make_identifiable_fixture()
    rows = classify_surface_roles(table)
    roles = {row.surface: row.role for row in rows}

    assert roles == {
        "push-a": "action",
        "push-b": "action",
        "flip-a": "action",
        "flip-b": "action",
        "red": "observation",
        "round": "observation",
    }


def test_surface_spellings_with_the_same_effect_form_one_behavioral_action_class():
    table = make_identifiable_fixture()
    groups = group_behavioral_action_surfaces(table)

    assert groups == (("flip-a", "flip-b"), ("push-a", "push-b"))


def test_without_policy_variation_effectful_surfaces_remain_unidentified():
    table = make_no_policy_shift_fixture()
    roles = {row.surface: row.role for row in classify_surface_roles(table)}

    for surface in ("push-a", "push-b", "flip-a", "flip-b"):
        assert roles[surface] == "abstain"
    assert roles["red"] == "observation"
    assert roles["round"] == "observation"


def test_action_effect_quotient_can_remove_surface_table_blowup():
    comparison = action_quotient_resource_comparison(
        state_count=8,
        surface_count=64,
        action_class_count=4,
        parser_bits=64,
    )

    assert comparison.flat_transition_bits == 1536
    assert comparison.quotient_transition_bits == 96
    assert comparison.surface_to_class_bits == 128
    assert comparison.quotient_total_bits == 288
    assert comparison.compression_ratio > 5.0


def test_no_task_or_benchmark_identifier_enters_theory_api():
    names = set(classify_surface_roles.__code__.co_varnames)
    assert "task_id" not in names
    assert "benchmark" not in names
    assert "axis" not in names
    assert "subject" not in names


def test_end_to_end_theory_gate_is_honestly_bounded_and_passes():
    result = run_theory_gate()

    assert result["passed"] is True
    assert result["passive_non_identifiability"]["observational_views_equal"] is True
    assert result["identifiable_regime_fixture"]["behavioral_action_classes"] == [
        ["flip-a", "flip-b"],
        ["push-a", "push-b"],
    ]
    assert result["resource_comparison"]["compression_ratio"] > 5.0
    assert "known-style constructions" in result["claim_boundary"]
    assert "unverified novelty candidate" in result["claim_boundary"]
