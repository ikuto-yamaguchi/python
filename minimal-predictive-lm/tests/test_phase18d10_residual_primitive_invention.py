from functools import lru_cache

from minimal_predictive_lm.phase18d10_residual_primitive_invention import (
    IndexAffinePrimitive,
    _base_residual_coverage,
    _coverage,
    _metamorphic_parameter_recovery,
    load_dataset,
    negative_controls,
    run,
    select_reusable_primitive,
)


@lru_cache(maxsize=1)
def _fixture():
    dataset = load_dataset()
    episodes = tuple(dataset["residual_episodes"])
    post_freeze = tuple(dataset["post_freeze_tasks"])
    selection = select_reusable_primitive(episodes)
    return dataset, episodes, post_freeze, selection


def test_frozen_dsl_cannot_explain_direct_residual_episodes():
    _, episodes, _, _ = _fixture()
    assert _base_residual_coverage(episodes) == (0, len(episodes))


def test_generic_meta_grammar_selects_one_cross_type_primitive():
    _, _, _, selection = _fixture()
    assert selection.candidates_evaluated == 170
    assert selection.exact_candidates == 1
    assert selection.probe_behavior_classes == 1
    assert selection.training_accuracy == 1.0
    assert selection.validation_accuracy == 1.0
    assert selection.validation_types == 2
    assert selection.validation_episodes == 4
    assert isinstance(selection.primitive, IndexAffinePrimitive)
    assert (selection.primitive.multiplier, selection.primitive.offset) == (1, 1)


def test_invented_primitive_expands_post_freeze_capability():
    _, _, tasks, selection = _fixture()
    total = sum(len(task["test"]) for task in tasks)
    baseline_correct, baseline_covered, _ = _coverage(tasks, ())
    final_correct, final_covered, _ = _coverage(
        tasks,
        (selection.primitive,),
    )
    assert (baseline_correct, baseline_covered) == (0, 0)
    assert (final_correct, final_covered) == (total, total)


def test_primitive_has_positive_mdl_gain():
    _, _, _, selection = _fixture()
    assert selection.compression_gain_bits > 0
    assert selection.model_bits < selection.literal_bits


def test_target_parameter_is_not_hardcoded_by_the_candidate_search():
    assert _metamorphic_parameter_recovery()


def test_ambiguity_memorization_and_conflict_controls():
    _, episodes, _, _ = _fixture()
    assert all(negative_controls(episodes).values())


def test_all_phase18d10_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["primitive_target_prelisted"] is False
    assert payload["claim_boundary"]["primitive_meta_grammar_human_designed"] is True
    assert payload["claim_boundary"]["llm_like_general_learning"] is False
    assert payload["claim_boundary"]["high_school_intelligence"] is False
