from minimal_predictive_lm.cap_sem_003_open_relation_grounding import (
    NOVEL_QUERY_GROUPS,
    NOVEL_STATEMENT_GROUPS,
    run_gate,
)


def test_all_opaque_relation_expressions_are_grounded():
    result = run_gate()
    assert result["learned_statement_markers"] == sum(
        len(group) for group in NOVEL_STATEMENT_GROUPS
    )
    assert result["learned_query_markers"] == sum(
        len(group) for group in NOVEL_QUERY_GROUPS
    )
    assert result["checks"]["learner_has_no_novel_gold_group_reference"]


def test_grounded_relations_transfer_to_unseen_multihop_documents():
    result = run_gate()
    assert result["heldout_accuracy"] == 1.0
    assert result["heldout_coverage"] == 1.0
    assert result["exact_raw_memorizer_accuracy"] == 0.5
    assert all(value == 1.0 for value in result["variant_accuracies"].values())
    assert result["alternate_punctuation_accuracy"] == 1.0


def test_semantic_runtime_and_surface_bridge_remain_frozen():
    result = run_gate()
    assert result["checks"]["semantic_runtime_is_frozen"]
    assert result["checks"]["surface_bridge_is_frozen"]
    assert result["passed"] is True
    assert all(result["checks"].values())
    assert result["natural_language_definition_understanding"] is False
    assert result["unrestricted_relation_learning"] is False
    assert result["high_school_intelligence"] is False
    assert result["general_llm_parity"] is False
