from minimal_predictive_lm.cap_gen_002_grounded_actuation_symmetry import (
    GroundingProfile,
    choose_by_grounded_bits,
    complete_graph,
    cycle_graph,
    graph_automorphisms,
    grounding_information_lower_bound,
    is_grounding_base,
    minimum_base_size,
    pareto_frontier,
    pointwise_stabilizer,
    run_experiment,
)


def test_complete_four_has_s4_symmetry_and_needs_three_direct_anchors():
    group = graph_automorphisms(complete_graph(4))
    assert len(group) == 24
    assert minimum_base_size(group, 4) == 3
    assert not is_grounding_base(group, (0, 1))
    assert is_grounding_base(group, (0, 1, 2))


def test_cycle_eight_has_dihedral_symmetry_and_two_points_break_it():
    group = graph_automorphisms(cycle_graph(8))
    assert len(group) == 16
    assert minimum_base_size(group, 8) == 2
    assert len(pointwise_stabilizer(group, (0,))) == 2
    assert len(pointwise_stabilizer(group, (0, 1))) == 1
    assert grounding_information_lower_bound(len(group), 2) == 4


def test_independently_observed_auxiliary_signatures_can_break_symmetry():
    group = graph_automorphisms(cycle_graph(8), tuple(range(8)))
    assert len(group) == 1
    assert minimum_base_size(group, 8) == 0


def test_passive_code_minimum_can_lose_after_grounding_cost_is_charged():
    cycle_group = graph_automorphisms(cycle_graph(8))
    trivial_group = graph_automorphisms(cycle_graph(8), tuple(range(8)))
    transition_only = GroundingProfile(
        "transition-only",
        executable_bits=8,
        automorphisms=cycle_group,
        direct_anchor_bits=7,
        inference_operations=8,
        peak_memory_bits=16,
    )
    auxiliary = GroundingProfile(
        "auxiliary",
        executable_bits=20,
        automorphisms=trivial_group,
        direct_anchor_bits=7,
        inference_operations=10,
        peak_memory_bits=24,
    )

    assert transition_only.executable_bits < auxiliary.executable_bits
    assert transition_only.grounded_total_bits == 22
    assert auxiliary.grounded_total_bits == 20
    assert choose_by_grounded_bits((transition_only, auxiliary)).profile == "auxiliary"
    assert {row.name for row in pareto_frontier((transition_only, auxiliary))} == {
        "transition-only",
        "auxiliary",
    }


def test_interaction_price_changes_the_lifetime_choice():
    group = graph_automorphisms(cycle_graph(8))
    trivial = graph_automorphisms(cycle_graph(8), tuple(range(8)))
    cheap_grounding = GroundingProfile("cheap", 8, group, 3, 8, 16)
    auxiliary = GroundingProfile("auxiliary", 20, trivial, 7, 10, 24)
    assert cheap_grounding.grounded_total_bits == 14
    assert choose_by_grounded_bits((cheap_grounding, auxiliary)).profile == "cheap"


def test_public_api_contains_no_benchmark_or_task_identifier():
    names = set(run_experiment.__code__.co_varnames)
    assert "task_id" not in names
    assert "benchmark" not in names
    assert "domain" not in names
    assert "axis" not in names


def test_end_to_end_theory_gate_passes_with_strict_claim_boundary():
    result = run_experiment()
    assert result["passed"] is True
    assert result["fully_symmetric_four"]["group_size"] == 24
    assert result["fully_symmetric_four"]["minimum_direct_anchors"] == 3
    assert result["cycle_eight"]["group_size"] == 16
    assert result["cycle_eight"]["minimum_direct_anchors"] == 2
    assert result["cycle_eight"]["one_anchor_remaining_alignments"] == 2
    assert result["cycle_eight"]["two_anchor_remaining_alignments"] == 1
    assert result["representation_tradeoff"]["expensive_grounding_choice"] == (
        "observable-auxiliary-cycle"
    )
    assert "prior art" in result["claim_boundary"]
    assert "unverified novelty candidate" in result["claim_boundary"]
