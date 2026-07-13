from minimal_predictive_lm.phase18b10_mdl_paraphrase_anchors import (
    anchor_ablation_reduces_coverage,
    conflict_unknown_and_arity_controls,
    evaluate,
    exact_span_baseline_coverage,
    induce,
    run,
    tampered_solution_is_rejected,
    unseen_synonym_without_anchor_abstains,
)


def test_extension_roles_and_unique_mdl_anchor_cover_are_induced():
    model, fit, _ = induce()
    assert fit["extension_spans"] == 9
    assert fit["role_trials"] == 27
    assert fit["anchor_candidates"] == 11
    assert fit["anchor_subsets"] == 2048
    assert fit["selected_anchors"] == 9
    assert set(model.anchors) == {
        ("全部", "COUNT"), ("合わせると", "COUNT"), ("総数", "COUNT"),
        ("単価", "RATE"), ("一つ分", "RATE"), ("ごと", "RATE"),
        ("売上", "VALUE"), ("全体量", "VALUE"), ("合計", "VALUE"),
    }


def test_unseen_complete_spans_recombine_learned_anchors():
    model, _, _ = induce()
    assert evaluate(model) == (1.0, 1.0, 1.0)
    assert exact_span_baseline_coverage() == 0.0


def test_anchor_conflict_absence_and_wrong_arity_abstain():
    model, _, _ = induce()
    assert all(conflict_unknown_and_arity_controls(model).values())
    assert unseen_synonym_without_anchor_abstains(model)


def test_every_selected_anchor_is_needed_by_frozen_heldout():
    model, _, _ = induce()
    assert anchor_ablation_reduces_coverage(model)


def test_proof_tampering_is_rejected():
    model, _, _ = induce()
    assert tampered_solution_is_rejected(model)


def test_all_phase18b10_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["semantic_synonym_understanding"] is False
    assert payload["claim_boundary"]["free_japanese"] is False
    assert payload["claim_boundary"]["high_school_intelligence"] is False
