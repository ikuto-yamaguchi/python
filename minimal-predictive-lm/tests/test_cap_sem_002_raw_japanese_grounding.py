from minimal_predictive_lm.cap_sem_002_raw_japanese_grounding import run_gate


def test_surface_parser_is_learned_with_only_global_role_ambiguity():
    result = run_gate()
    assert result["parser_calibration_accuracy"] == 1.0
    assert result["equivalent_best_models"] == 2
    assert result["candidate_ngrams"] <= 24
    assert result["candidate_pairs"] <= 16


def test_raw_text_transfers_to_unseen_multihop_documents():
    result = run_gate()
    assert result["heldout_accuracy"] == 1.0
    assert result["heldout_coverage"] == 1.0
    assert result["raw_memorization_accuracy"] == 0.5
    assert all(
        accuracy == 1.0
        for accuracy in result["variant_accuracies"].values()
    )
    assert all(
        coverage == 1.0
        for coverage in result["variant_coverages"].values()
    )


def test_capability_gate_passes_under_resource_and_claim_bounds():
    result = run_gate()
    assert result["passed"]
    assert all(result["checks"].values())
    assert result["controlled_raw_japanese_grounding"] is True
    assert result["unrestricted_japanese_understanding"] is False
    assert result["high_school_intelligence"] is False
    assert result["general_llm_parity"] is False
