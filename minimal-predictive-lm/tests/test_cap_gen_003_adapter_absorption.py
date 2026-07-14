from __future__ import annotations

from minimal_predictive_lm.cap_gen_003_adapter_absorption import (
    absorb_arbitrary_domains,
    arbitrary_domain,
    common_guaranteed_transitions,
    cycle_reuse_profile,
    fully_absorbed_adapter,
    partial_lookup_adapter,
    reuse_profile_from_lookup,
    run_experiment,
)


def test_unrestricted_adapters_absorb_arbitrary_transition_tables() -> None:
    domains = (
        arbitrary_domain("a", "a", (1, 0, 3, 2)),
        arbitrary_domain("b", "b", (2, 3, 1, 0)),
    )
    result = absorb_arbitrary_domains(domains)
    assert result.exact_training_accuracy == 1.0
    assert result.shared_core_entries == 1
    assert result.adapter_entries == 8
    assert result.core_only_reduction == 8.0
    assert result.fully_charged_reduction == 8 / 9


def test_one_grounded_lookup_cannot_predict_arbitrary_unseen_successors() -> None:
    heldout = arbitrary_domain("heldout", "h", (1, 0, 3, 2, 5, 4, 7, 6))
    adapter = partial_lookup_adapter(heldout, (heldout.states[0],))
    profile = reuse_profile_from_lookup("partial", heldout, adapter)
    assert profile.heldout_exact_accuracy == 1 / 8
    assert profile.heldout_interaction_savings == 7
    assert not profile.certified_operational_reuse


def test_future_leakage_is_rejected_even_with_perfect_accuracy() -> None:
    heldout = arbitrary_domain("heldout", "h", (1, 0, 3, 2, 5, 4, 7, 6))
    adapter = partial_lookup_adapter(
        heldout,
        (heldout.states[0],),
        leak_future=True,
    )
    profile = reuse_profile_from_lookup("leaked", heldout, adapter)
    assert profile.heldout_exact_accuracy == 1.0
    assert profile.future_active_successors_used == 7
    assert not profile.certified_operational_reuse


def test_full_lookup_has_no_operational_reuse_surplus() -> None:
    heldout = arbitrary_domain("heldout", "h", (1, 0, 3, 2, 5, 4, 7, 6))
    profile = reuse_profile_from_lookup(
        "full",
        heldout,
        fully_absorbed_adapter(heldout),
    )
    assert profile.heldout_exact_accuracy == 1.0
    assert profile.heldout_storage_savings == 0
    assert profile.heldout_interaction_savings == 0
    assert not profile.certified_operational_reuse


def test_same_one_anchor_evidence_does_not_identify_arbitrary_future() -> None:
    world_a = arbitrary_domain("a", "w", (1, 0, 3, 2, 5, 4, 7, 6))
    world_b = arbitrary_domain("b", "w", (1, 2, 0, 3, 4, 5, 6, 7))
    common = common_guaranteed_transitions((world_a, world_b))
    assert common == (world_a.transitions[0],)
    assert len(common) / len(world_a.states) == 1 / 8


def test_previous_cross_domain_operator_passes_anti_absorption_gate() -> None:
    profile = cycle_reuse_profile()
    assert profile.heldout_exact_accuracy == 1.0
    assert profile.future_active_successors_used == 0
    assert profile.heldout_storage_savings == 8
    assert profile.heldout_interaction_savings == 8
    assert profile.certified_operational_reuse


def test_frozen_gate_and_claim_boundary() -> None:
    result = run_experiment()
    assert result["passed"] is True
    assert result["adapter_absorption"]["core_only_reduction"] == 18.0
    assert result["adapter_absorption"]["fully_charged_reduction"] < 1.0
    assert result["heldout_lookup_controls"]["future_leaking"]["certified"] is False
    assert result["heldout_lookup_controls"]["fully_grounded"]["certified"] is False
    assert result["indistinguishable_worlds"]["common_transition_count"] == 1
    assert result["positive_control"]["certified"] is True
    assert "prior art" in result["claim_boundary"]
    assert "not raw-stream learning" in result["claim_boundary"]
