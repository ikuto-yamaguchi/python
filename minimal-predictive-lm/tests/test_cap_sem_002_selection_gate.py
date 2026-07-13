from minimal_predictive_lm.cap_sem_002_selection_gate import (
    CANONICAL_IMPLEMENTATION,
    experimental_refits_semantic_runtime,
    run_gate,
)


def test_experimental_candidate_refits_semantics_and_is_not_canonical():
    result = run_gate()
    assert experimental_refits_semantic_runtime() is True
    assert result["experimental"]["refits_semantic_runtime"] is True
    assert result["experimental"]["promotion_status"] == "rejected_as_canonical"


def test_frozen_bridge_is_selected_as_cap_sem_002():
    result = run_gate()
    assert result["canonical_implementation"] == CANONICAL_IMPLEMENTATION
    assert result["canonical"]["semantic_runtime_is_frozen"] is True
    assert result["canonical"]["heldout_accuracy"] == 1.0
    assert result["canonical"]["heldout_coverage"] == 1.0


def test_selection_gate_passes_without_overclaiming():
    result = run_gate()
    assert result["passed"] is True
    assert all(result["checks"].values())
    assert result["unrestricted_japanese_understanding"] is False
    assert result["high_school_intelligence"] is False
    assert result["general_llm_parity"] is False
