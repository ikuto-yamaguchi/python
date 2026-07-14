from __future__ import annotations

import pytest

from minimal_predictive_lm.cap_gen_003_cross_domain_operational_transfer import (
    InteractionDomain,
    cycle_fixture,
    cycle_orders,
    exact_accuracy,
    learn_shared_cycle_operator,
    path_fixture,
    resource_comparison,
    run_experiment,
    separate_table_predictions,
    surface_token_transfer,
    transfer_operator,
)


def fixtures():
    alpha, _ = cycle_fixture("alpha", ("a", "b", "c", "d", "e"), 0)
    beta, _ = cycle_fixture("beta", ("q7", "m2", "z9", "a4", "t1", "k8", "c3"), 1)
    gamma, truth = cycle_fixture(
        "gamma",
        ("north", "violet", "copper", "echo", "jade", "lima", "orbit", "piano", "quartz"),
        1,
    )
    return alpha, beta, gamma, truth


def test_cycle_has_two_orientations() -> None:
    alpha, _, _, _ = fixtures()
    assert len(cycle_orders(alpha)) == 2


def test_one_grounded_edge_transfers_whole_heldout_cycle() -> None:
    alpha, beta, gamma, truth = fixtures()
    certificate = learn_shared_cycle_operator((alpha, beta))
    empty = InteractionDomain(gamma.name, gamma.states, gamma.passive_edges, ())
    unresolved = transfer_operator(certificate, empty)
    assert unresolved.status == "abstain"
    assert unresolved.candidate_count == 2

    truth_map = dict(truth)
    source = gamma.states[0]
    one = InteractionDomain(
        gamma.name,
        gamma.states,
        gamma.passive_edges,
        ((source, truth_map[source]),),
    )
    transferred = transfer_operator(certificate, one)
    assert transferred.status == "transferred"
    assert exact_accuracy(transferred.predictions, truth) == 1.0


def test_surface_reuse_does_not_ground_operation() -> None:
    alpha, _, gamma, truth = fixtures()
    empty = InteractionDomain(gamma.name, gamma.states, gamma.passive_edges, ())
    assert exact_accuracy(surface_token_transfer(alpha, empty), truth) == 0.0


def test_separate_table_covers_only_observed_transition() -> None:
    _, _, gamma, truth = fixtures()
    truth_map = dict(truth)
    source = gamma.states[0]
    one = InteractionDomain(gamma.name, gamma.states, gamma.passive_edges, ((source, truth_map[source]),))
    predictions = separate_table_predictions(one)
    assert len(predictions) == 1
    assert exact_accuracy(predictions, truth) == pytest.approx(1 / 9)


def test_wrong_topology_is_rejected() -> None:
    alpha, beta, _, _ = fixtures()
    certificate = learn_shared_cycle_operator((alpha, beta))
    result = transfer_operator(certificate, path_fixture("path", ("p0", "p1", "p2", "p3", "p4")))
    assert result.status == "unsupported"


def test_incomplete_training_support_is_rejected() -> None:
    alpha, beta, _, _ = fixtures()
    incomplete = InteractionDomain(alpha.name, alpha.states, alpha.passive_edges, alpha.active_transitions[:1])
    with pytest.raises(ValueError, match="complete active support"):
        learn_shared_cycle_operator((incomplete, beta))


def test_resource_separation_and_frozen_gate() -> None:
    alpha, beta, gamma, _ = fixtures()
    resources = resource_comparison((alpha, beta), len(gamma.states), 1)
    assert resources.separate_control_entries == 21
    assert resources.shared_control_entries == 4
    assert resources.control_entry_reduction == pytest.approx(5.25)
    assert resources.heldout_interaction_savings == 8

    result = run_experiment()
    assert result["passed"] is True
    assert result["heldout_domain"]["transferred_exact_accuracy"] == 1.0
    assert result["heldout_domain"]["surface_token_baseline_accuracy"] == 0.0
    assert result["structural_rejection"]["status"] == "unsupported"
    assert "prior art" in result["claim_boundary"]
