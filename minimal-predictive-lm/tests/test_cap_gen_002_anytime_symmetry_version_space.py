from minimal_predictive_lm.cap_gen_002_anytime_symmetry_version_space import (
    BernoulliCount,
    allocated_error_budget,
    build_version_certificate,
    generated_subgroup,
    identity_permutation,
    inverse,
    marker_counts,
    retained_symmetries,
    run_experiment,
    time_uniform_hoeffding_interval,
)
from minimal_predictive_lm.cap_gen_002_grounded_actuation_symmetry import (
    cycle_graph,
    graph_automorphisms,
)


def test_time_uniform_budget_and_intervals_are_conservative():
    assert allocated_error_budget(
        delta=0.05,
        stream_count=16,
        maximum_trials=100_000,
    ) < 0.05
    low = time_uniform_hoeffding_interval(
        BernoulliCount(0, 16),
        delta=0.05,
        stream_count=16,
    )
    high = time_uniform_hoeffding_interval(
        BernoulliCount(16, 16),
        delta=0.05,
        stream_count=16,
    )
    assert low[1] >= high[0]


def test_more_evidence_shrinks_the_safe_version_space_without_early_grounding():
    group = graph_automorphisms(cycle_graph(8))
    early = retained_symmetries(
        group,
        marker_counts(action_count=8, marked_actions=(0, 1), trials=16),
        delta=0.05,
    )
    late = retained_symmetries(
        group,
        marker_counts(action_count=8, marked_actions=(0, 1), trials=32),
        delta=0.05,
    )
    early_certificate = build_version_certificate(group, early)
    late_certificate = build_version_certificate(group, late)

    assert len(early) == 16
    assert early_certificate.robust_base_size == 2
    assert len(late) == 1
    assert late_certificate.robust_base_size == 0


def test_group_logic_prunes_an_element_whose_required_power_was_rejected():
    group = graph_automorphisms(cycle_graph(4))
    identity = identity_permutation(4)
    rotation = tuple((index + 1) % 4 for index in range(4))
    certificate = build_version_certificate(group, (identity, rotation))

    assert len(certificate.retained_elements) == 2
    assert certificate.logically_supported_elements == frozenset({identity})
    assert len(certificate.plausible_subgroups) == 1


def test_subgroup_version_space_is_sharper_than_generated_envelope():
    group = graph_automorphisms(cycle_graph(4))
    rotation = tuple((index + 1) % 4 for index in range(4))
    reflection = tuple((-index) % 4 for index in range(4))
    rotations = generated_subgroup((rotation,), 4)
    certificate = build_version_certificate(group, (*rotations, reflection))

    assert len(certificate.plausible_subgroups) == 4
    assert certificate.robust_base_size == 1
    assert len(certificate.generated_envelope) == 8
    assert certificate.envelope_base_size == 2


def test_rejected_element_count_can_choose_the_worse_experiment():
    result = run_experiment()["active_choice_counterexample"]
    count_choice = result["element_count_choice"]
    version_choice = result["version_space_choice"]

    assert count_choice["rejected_elements"] == 6
    assert count_choice["robust_base_size"] == 1
    assert version_choice["rejected_elements"] == 5
    assert version_choice["robust_base_size"] == 0


def test_permutation_inverse_and_generated_subgroup_contract():
    rotation = tuple((index + 1) % 4 for index in range(4))
    subgroup = generated_subgroup((rotation,), 4)
    assert len(subgroup) == 4
    assert inverse(rotation) in subgroup


def test_end_to_end_theory_gate_passes_with_honest_claim_boundary():
    result = run_experiment()
    assert result["passed"] is True
    assert result["finite_sample_progression"]["trials_16"]["robust_base_size"] == 2
    assert result["finite_sample_progression"]["trials_32"]["robust_base_size"] == 0
    assert result["logical_pruning"]["raw_retained_elements"] == 2
    assert result["logical_pruning"]["logically_supported_elements"] == 1
    assert "prior art" in result["claim_boundary"]
    assert "unverified novelty candidate" in result["claim_boundary"]
