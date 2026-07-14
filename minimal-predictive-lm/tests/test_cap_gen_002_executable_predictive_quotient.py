from minimal_predictive_lm.cap_gen_002_executable_predictive_quotient import (
    Probe,
    ResourceCandidate,
    ResourceVector,
    behavioral_partition,
    build_theory_fixture,
    canonical_decision,
    exact_minimum_probe_selection,
    greedy_probe_selection,
    make_unseen_surface_counterexample,
    observational_program_quotient,
    pareto_frontier,
    partition_is_exact,
    quotient_machine,
    run_theory_gate,
)


def _probe_fixture():
    classes = ("r0", "r1", "r2", "r3")
    probes = (
        Probe("high-bit", 1, 1, 1),
        Probe("low-bit", 1, 1, 1),
        Probe("parity", 3, 1, 1),
    )
    responses = {
        ("r0", "high-bit"): "0",
        ("r1", "high-bit"): "0",
        ("r2", "high-bit"): "1",
        ("r3", "high-bit"): "1",
        ("r0", "low-bit"): "0",
        ("r1", "low-bit"): "1",
        ("r2", "low-bit"): "0",
        ("r3", "low-bit"): "1",
        ("r0", "parity"): "0",
        ("r1", "parity"): "1",
        ("r2", "parity"): "1",
        ("r3", "parity"): "0",
    }
    return classes, probes, responses


def test_partition_refinement_uses_deeper_successors_not_only_immediate_output():
    table = build_theory_fixture()
    partition = behavioral_partition(table)

    assert partition == (("a0", "a1"), ("b",), ("sink0",), ("sink1",))
    assert quotient_machine(table).minimum_fixed_state_bits == 2


def test_exact_predictor_cannot_merge_distinguishable_histories():
    table = build_theory_fixture()
    valid = (("a0", "a1"), ("b",), ("sink0",), ("sink1",))
    invalid = (("a0", "a1", "b"), ("sink0",), ("sink1",))

    assert partition_is_exact(table, valid)
    assert not partition_is_exact(table, invalid)


def test_unseen_surface_has_two_observationally_identical_training_worlds():
    worlds = make_unseen_surface_counterexample()

    assert worlds.training_views_equal()
    assert worlds.unseen_views_differ()
    # Any deterministic learner receives the same training view in both worlds, so its
    # single unseen assignment must be wrong in at least one of them.
    hypothetical_assignment = "0"
    world_a_role = worlds.world_a_responses[(worlds.unseen_history, "probe-a")]
    world_b_role = worlds.world_b_responses[(worlds.unseen_history, "probe-a")]
    assert hypothetical_assignment in {world_a_role, world_b_role}
    assert world_a_role != world_b_role


def test_exact_and_greedy_probe_selection_separate_all_pairs():
    classes, probes, responses = _probe_fixture()
    exact = exact_minimum_probe_selection(classes, probes, responses)
    greedy = greedy_probe_selection(classes, probes, responses)

    assert exact.complete
    assert exact.probes == ("high-bit", "low-bit")
    assert exact.total_cost == 2
    assert greedy.complete
    assert greedy.total_cost == 2


def test_nonseparating_probe_family_reports_incomplete():
    classes, probes, responses = _probe_fixture()
    exact = exact_minimum_probe_selection(classes, probes[:1], responses)
    greedy = greedy_probe_selection(classes, probes[:1], responses)

    assert not exact.complete
    assert exact.probes == ()
    assert not greedy.complete
    assert greedy.probes == ("high-bit",)


def test_pareto_frontier_keeps_bits_compute_tradeoff_and_removes_dominated_model():
    candidates = (
        ResourceCandidate("short-recompute", ResourceVector(10, 80, 100, 4, 8)),
        ResourceCandidate("large-lookup", ResourceVector(100, 120, 1, 80, 8)),
        ResourceCandidate("dominated", ResourceVector(120, 150, 120, 100, 10)),
    )
    frontier = pareto_frontier(candidates)

    assert tuple(candidate.identifier for candidate in frontier) == (
        "large-lookup",
        "short-recompute",
    )


def test_canonicalization_abstains_on_zero_resource_gap():
    candidates = (
        ResourceCandidate("left", ResourceVector(10, 10, 10, 10, 10)),
        ResourceCandidate("right", ResourceVector(10, 10, 10, 10, 10)),
    )
    decision = canonical_decision(
        candidates,
        ResourceVector(1, 1, 1, 1, 1),
    )

    assert decision.abstained
    assert decision.selected is None
    assert decision.gap == 0


def test_declared_weight_policy_can_select_with_a_strict_gap():
    candidates = (
        ResourceCandidate("short-recompute", ResourceVector(10, 80, 100, 4, 8)),
        ResourceCandidate("large-lookup", ResourceVector(100, 120, 1, 80, 8)),
    )
    decision = canonical_decision(
        candidates,
        ResourceVector(10, 1, 1, 1, 1),
    )

    assert not decision.abstained
    assert decision.selected == "short-recompute"
    assert decision.gap is not None and decision.gap > 0


def test_observational_program_quotient_is_only_a_known_search_optimization():
    quotient = observational_program_quotient(
        {
            "inc-dec": ("a", "b"),
            "identity": ("a", "b"),
            "reverse": ("z", "y"),
        },
        {
            "inc-dec": ResourceVector(20, 0, 4, 1, 2),
            "identity": ResourceVector(8, 0, 2, 1, 2),
            "reverse": ResourceVector(9, 0, 3, 1, 2),
        },
    )

    assert quotient == (
        ("identity", ("identity", "inc-dec")),
        ("reverse", ("reverse",)),
    )


def test_public_theory_api_contains_no_benchmark_or_subject_identifier():
    names = set(quotient_machine.__code__.co_varnames)
    assert "task_id" not in names
    assert "benchmark" not in names
    assert "subject" not in names
    assert "axis" not in names


def test_end_to_end_theory_gate_is_honestly_bounded_and_passes():
    result = run_theory_gate()

    assert result["passed"] is True
    assert result["quotient"]["state_count"] == 4
    assert result["probe_selection"]["exact_cost"] == 2
    assert result["canonical_tie"]["abstained"] is True
    assert result["unseen_surface_counterexample"]["training_views_equal"] is True
    assert "known-style constructions" in result["claim_boundary"]
    assert "unverified novelty candidate" in result["claim_boundary"]
