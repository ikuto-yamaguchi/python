from __future__ import annotations

import pytest

from minimal_predictive_lm import cap_gen_003_reset_free_boundary_operational_reuse as r


def test_frozen_gate_passes() -> None:
    result = r.run_experiment()
    assert result["passed"] is True
    assert result["stream"]["reset_tokens_used"] == 0
    assert result["stream"]["domain_label_tokens_used"] == 0
    assert result["stream"]["detected_boundary_count"] == 3
    assert result["stream"]["all_boundaries_causal"] is True


def test_heldout_transfer_is_one_shot_and_exact() -> None:
    result = r.run_experiment()["positive_transfer"]
    assert result["status"] == "transferred"
    assert result["exact_accuracy"] == 1.0
    assert result["predictions"] == 9
    assert result["grounded_interactions"] == 1
    assert result["future_successors_used"] == 0


def test_zero_anchor_abstains_and_path_is_rejected() -> None:
    result = r.run_experiment()["positive_transfer"]
    assert result["zero_anchor_status"] == "abstain"
    assert result["zero_anchor_candidates"] == 2
    assert result["unsupported_status"] == "unsupported"


def test_segmentation_absorption_fails_complete_accounting() -> None:
    profile = r.segmentation_absorption_profile(13)
    assert profile.core_only_reduction == 13.0
    assert profile.fully_charged_entries == 15
    assert profile.fully_charged_reduction < 1.0


def test_future_looking_boundary_is_rejected() -> None:
    control = r.causal_boundary_control()
    assert control["future_successors_used"] == 1
    assert control["certified"] is False


def test_operationally_identical_hidden_boundary_is_merged() -> None:
    control = r.nonidentifiable_boundary_control()
    assert control["hidden_episode_count"] == 2
    assert control["detected_boundary_count"] == 0
    assert control["detected_segment_count"] == 1
    assert control["correct_action"] == "merge"


def test_surprise_proposal_requires_delayed_reuse_certification() -> None:
    control = r.delayed_boundary_certification_control()
    assert control["proposal_allowed"] is True
    assert control["new_context_certified"] is False
    assert control["accepted_boundary"] is False


def test_reset_token_is_forbidden() -> None:
    with pytest.raises(ValueError, match="RESET tokens are forbidden"):
        r.parse_reset_free_stream(("RESET", "EDGE a b"))


def test_resource_result_is_not_overclaimed() -> None:
    resources = r.run_experiment()["resources"]
    assert resources["heldout_incremental_surplus"] == 6
    assert resources["unit_weight_global_surplus"] == -1.0
    assert resources["passive_cost_break_even_with_unit_other_costs"] == pytest.approx(20 / 21)
