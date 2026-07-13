from minimal_predictive_lm.cap_sem_001_relational_meaning import (
    QUERY_GROUPS,
    STATEMENT_GROUPS,
    build_heldout_records,
    build_training_records,
    evaluate,
    learn_meaning,
    metamorphic_records,
    run_gate,
)


def test_synonyms_share_latent_codes_and_inverse_pairs():
    model = learn_meaning(build_training_records())
    for statement_group, query_group in zip(
        STATEMENT_GROUPS, QUERY_GROUPS
    ):
        codes = {
            model.marker_codes[marker]
            for marker in statement_group + query_group
        }
        assert len(codes) == 1
    codes = [model.marker_codes[group[0]] for group in STATEMENT_GROUPS]
    assert model.inverse_codes[codes[0]] == codes[1]
    assert model.inverse_codes[codes[2]] == codes[3]


def test_heldout_composition_and_metamorphic_invariance():
    model = learn_meaning(build_training_records())
    heldout = build_heldout_records()
    original = evaluate(model, heldout)
    assert original.accuracy == 1.0
    for rows in metamorphic_records(heldout).values():
        variant = evaluate(model, rows)
        assert variant.accuracy == 1.0
        assert variant.predictions == original.predictions


def test_capability_gate_passes_with_hard_resource_budgets():
    result = run_gate()
    assert result["passed"]
    assert all(result["checks"].values())
    assert result["raw_japanese_understanding"] is False
    assert result["general_llm_parity"] is False
