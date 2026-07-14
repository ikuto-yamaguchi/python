from __future__ import annotations

import pytest

from minimal_predictive_lm.cap_gen_003_cross_domain_operational_transfer import (
    InteractionDomain,
    cycle_fixture,
)
from minimal_predictive_lm.cap_gen_003_mixed_stream_operational_reuse import (
    certify_mixed_stream,
    control_resource_profile,
    future_looking_boundary_control,
    no_reset_control,
    parse_mixed_stream,
    run_experiment,
    serialize_episode,
    singleton_segmentation_absorption,
)


def _stream() -> tuple[str, ...]:
    alpha, _ = cycle_fixture(
        "ignored",
        ("a0", "a1", "a2", "a3", "a4"),
        0,
    )
    beta, _ = cycle_fixture(
        "ignored",
        ("b0", "b1", "b2", "b3", "b4", "b5", "b6"),
        1,
    )
    gamma, truth = cycle_fixture(
        "ignored",
        ("c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"),
        1,
    )
    truth_map = dict(truth)
    one = InteractionDomain(
        name="not-serialized",
        states=gamma.states,
        passive_edges=gamma.passive_edges,
        active_transitions=((gamma.states[0], truth_map[gamma.states[0]]),),
    )
    return (
        serialize_episode(alpha)
        + serialize_episode(beta)
        + ("FREEZE",)
        + serialize_episode(one)
    )


def test_parser_uses_reset_not_domain_labels() -> None:
    parsed = parse_mixed_stream(_stream())
    certificate = certify_mixed_stream(parsed)
    assert len(parsed.training_episodes) == 2
    assert len(parsed.heldout_episodes) == 1
    assert certificate.domain_label_tokens_used == 0
    assert certificate.parser_name == "causal-reset-event-parser"
    assert all("ignored" not in line for line in _stream())


def test_parser_rejects_missing_freeze() -> None:
    with pytest.raises(ValueError, match="exactly one FREEZE"):
        parse_mixed_stream(("RESET", "EDGE a b"))


def test_singleton_segmentation_is_fake_after_full_accounting() -> None:
    profile = singleton_segmentation_absorption(_stream())
    assert profile.training_accuracy == 1.0
    assert profile.core_only_reduction > 10.0
    assert profile.fully_charged_reduction < 1.0


def test_future_looking_boundary_uses_successor() -> None:
    control = future_looking_boundary_control(
        "STEP same left",
        "STEP same right",
    )
    assert control["causal_prefix_equal"] is True
    assert control["future_boundary_keys_differ"] is True
    assert control["future_successors_used"] == 1
    assert control["certified"] is False


def test_reset_is_required_for_opposite_contexts_with_same_states() -> None:
    states = ("s0", "s1", "s2", "s3", "s4")
    left, _ = cycle_fixture("ignored", states, 0)
    right, _ = cycle_fixture("ignored", states, 1)
    control = no_reset_control(
        serialize_episode(left) + serialize_episode(right)
    )
    assert control["status"] == "contradiction"
    assert control["causal_reset_required"] is True


def test_incomplete_training_support_does_not_certify() -> None:
    alpha, _ = cycle_fixture(
        "ignored",
        ("a0", "a1", "a2", "a3", "a4"),
        0,
    )
    beta, truth = cycle_fixture(
        "ignored",
        ("b0", "b1", "b2", "b3", "b4", "b5"),
        1,
    )
    one = InteractionDomain(
        name="ignored",
        states=beta.states,
        passive_edges=beta.passive_edges,
        active_transitions=(truth[0],),
    )
    heldout, _ = cycle_fixture(
        "ignored",
        ("c0", "c1", "c2", "c3", "c4"),
        0,
        active_sources=(),
    )
    stream = (
        serialize_episode(alpha)
        + serialize_episode(one)
        + ("FREEZE",)
        + serialize_episode(heldout)
    )
    parsed = parse_mixed_stream(stream)
    with pytest.raises(ValueError, match="complete active support"):
        certify_mixed_stream(parsed)


def test_resource_accounting_charges_parser_and_adapters() -> None:
    profile = control_resource_profile((5, 7), 9, 1, 3)
    assert profile.separate_control_entries == 21
    assert profile.shared_control_entries == 5
    assert profile.control_entry_reduction == 4.2
    assert profile.heldout_interaction_savings == 8


def test_frozen_gate() -> None:
    result = run_experiment()
    assert result["passed"] is True
    assert result["stream"]["domain_label_tokens_used"] == 0
    assert result["positive_transfer"]["exact_accuracy"] == 1.0
    assert result["positive_transfer"]["grounded_interactions"] == 1
    assert result["positive_transfer"]["zero_anchor_status"] == "abstain"
    assert result["positive_transfer"]["unsupported_status"] == "unsupported"
    assert result["segmentation_absorption"]["fully_charged_reduction"] < 1.0
    assert result["no_reset_control"]["status"] == "contradiction"
    assert "prior art" in result["claim_boundary"]
