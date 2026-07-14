from minimal_predictive_lm.cap_gen_002_grounded_actuation_symmetry import cycle_graph, graph_automorphisms
from minimal_predictive_lm.cap_gen_002_invariant_auxiliary_symmetry import (
    AuxiliaryChannel,
    deterministic_information_bits,
    evaluate_auxiliary_bundle,
    naive_environmentwise_residual_size,
    prospective_shift_counterexample,
    residual_automorphisms,
    run_experiment,
    single_environment_two_world_counterexample,
)


def _group():
    return graph_automorphisms(cycle_graph(8))


def test_invariant_bundle_breaks_cycle_symmetry():
    group = _group()
    first = AuxiliaryChannel("first", ((1, 0, 0, 0, 0, 0, 0, 0),) * 3, 4, 24, 1, 8)
    second = AuxiliaryChannel("second", ((0, 1, 0, 0, 0, 0, 0, 0),) * 3, 4, 24, 1, 8)
    result = evaluate_auxiliary_bundle(group, (first, second), direct_anchor_bits=7)
    assert len(group) == 16
    assert result.residual_group_size == 1
    assert result.direct_anchor_count == 0
    assert 1.0 < result.deterministic_information_bits < 1.1


def test_environment_dependent_unique_tag_is_not_certified():
    group = _group()
    channel = AuxiliaryChannel(
        "changing-tag",
        (tuple(range(8)), tuple(range(1, 8)) + (0,), tuple(reversed(range(8)))),
        3,
        24,
        1,
        24,
    )
    result = evaluate_auxiliary_bundle(group, (channel,), direct_anchor_bits=7)
    assert deterministic_information_bits(channel.environment_signatures[0]) == 3.0
    assert naive_environmentwise_residual_size(group, channel) == 1
    assert result.certified_channels == ()
    assert result.residual_group_size == 16
    assert result.symmetry_tax_bits == 14


def test_one_stable_marker_leaves_reflection():
    channel = AuxiliaryChannel("one", ((1, 0, 0, 0, 0, 0, 0, 0),) * 2, 4, 16, 1, 8)
    assert len(residual_automorphisms(_group(), (channel,))) == 2


def test_single_environment_has_two_future_worlds():
    result = single_environment_two_world_counterexample()
    assert result["observed_training_signatures_equal"] is True
    assert result["future_predictions_differ"] is True


def test_observed_invariance_needs_prospective_validation():
    result = prospective_shift_counterexample()
    assert result["stable_on_observed_environments"] is True
    assert result["prospective_environment_exposes_shift"] is True


def test_end_to_end_result():
    result = run_experiment()
    assert result["passed"] is True
    assert result["stable_bundle"]["grounded_total_bits"] == 8
    assert result["spurious_unique_tag"]["grounded_total_bits"] == 17
    assert result["no_auxiliary"]["grounded_total_bits"] == 14
    assert "prior art" in result["claim_boundary"]
