from minimal_predictive_lm.cap_gen_004_prospective_library import (
    OnlineLibraryLearner,
    contiguous_subprograms,
    duration_shift_control,
    encoded_length,
    isolated_control,
    run_experiment,
    vocabulary_size,
)


def test_encoding_uses_helpers() -> None:
    program = ("a", "b", "c", "d")
    assert encoded_length(program, set()) == 4
    assert encoded_length(program, {("b", "c")}) == 3


def test_candidate_mining_is_domain_agnostic() -> None:
    candidates = contiguous_subprograms(("x", "y", "z"))
    assert ("x", "y") in candidates
    assert ("x", "y", "z") in candidates


def test_prospective_beats_retrospective_and_no_library() -> None:
    result = run_experiment()
    costs = result["costs"]
    assert costs["prospective"] < costs["retrospective"] < costs["none"]
    assert costs["prospective_vs_retrospective_reduction"] > 0.18


def test_policy_transfers_after_two_completed_runs() -> None:
    result = run_experiment()
    assert result["prospective"]["string_probation_task"] == 11
    assert result["retrospective"]["string_admission_task"] == 12
    assert result["prospective"]["grid_probation_task"] == 16
    assert result["retrospective"]["grid_admission_task"] == 17


def test_probation_requires_real_next_task_reuse() -> None:
    result = run_experiment()
    assert result["prospective"]["probation_events"] == 2
    assert result["prospective"]["confirmed_events"] == 2
    assert result["prospective"]["permanent_helpers"] == 4


def test_isolated_tasks_do_not_create_abstractions() -> None:
    programs = isolated_control()
    learner = OnlineLibraryLearner(
        "prospective",
        primitive_vocabulary=vocabulary_size(programs),
    )
    assert learner.run(programs).events == ()


def test_duration_shift_regret_is_bounded_by_probation() -> None:
    programs = duration_shift_control()
    vocabulary = vocabulary_size(programs)
    retrospective = OnlineLibraryLearner(
        "retrospective",
        primitive_vocabulary=vocabulary,
    ).run(programs)
    prospective = OnlineLibraryLearner(
        "prospective",
        primitive_vocabulary=vocabulary,
    ).run(programs)
    assert prospective.total_cost - retrospective.total_cost <= 16
    assert prospective.probation_storage_tokens == 8


def test_learner_does_not_receive_family_labels() -> None:
    result = run_experiment()
    assert result["curriculum"]["family_labels_visible_to_learner"] == 0


def test_full_experiment_passes_with_honest_claim_boundary() -> None:
    result = run_experiment()
    assert result["passed"] is True
    assert "Novelty is not established" in result["claim_boundary"]
    assert "public heterogeneous benchmarks" in result["claim_boundary"]
