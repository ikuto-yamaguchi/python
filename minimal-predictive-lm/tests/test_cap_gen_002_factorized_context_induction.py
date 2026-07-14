from minimal_predictive_lm.cap_gen_002_factorized_context_induction import (
    ContextDiscoveryConfig,
    discover_factorized_context_model,
    evaluate_exact_pair_baseline,
    evaluate_factorized_context_model,
    make_combinatorial_context_stream,
    predicted_boundary_scores,
    run_experiment,
    training_boundary_scores,
)
from minimal_predictive_lm.cap_gen_002_loop_microprogram_induction import (
    discover_loop_interchange_model,
)
from minimal_predictive_lm.cap_gen_002_raw_interchange_induction import DiscoveryConfig


def test_training_has_no_repeated_full_context_pair_across_evaluation_split():
    _training, _roles, training_episodes = make_combinatorial_context_stream(
        seed=7,
        split="train",
    )
    _evaluation, _roles2, evaluation_episodes = make_combinatorial_context_stream(
        seed=97,
        split="evaluation",
        evaluation_repeats=2,
    )

    training_source_pairs = {row.source_context_pair for row in training_episodes}
    training_target_pairs = {row.target_context_pair for row in training_episodes}
    evaluation_source_pairs = {row.source_context_pair for row in evaluation_episodes}
    evaluation_target_pairs = {row.target_context_pair for row in evaluation_episodes}

    assert training_source_pairs.isdisjoint(evaluation_source_pairs)
    assert training_target_pairs.isdisjoint(evaluation_target_pairs)
    assert len(training_source_pairs) == 36
    assert len(evaluation_source_pairs) == 12


def test_joint_discovery_learns_three_factorized_roles_and_all_training_boundaries():
    training, hidden_roles, episodes = make_combinatorial_context_stream(
        seed=7,
        split="train",
    )
    model = discover_factorized_context_model(training, ContextDiscoveryConfig())
    boundary = training_boundary_scores(model, episodes)

    assert len(model.roles) == 3
    assert len(model.programs) == 3
    assert boundary["precision"] == 1.0
    assert boundary["recall"] == 1.0
    assert {len(role.source_left_class) for role in model.roles} == {4}
    assert {len(role.source_right_class) for role in model.roles} == {4}
    assert {len(role.target_left_class) for role in model.roles} == {4}
    assert {len(role.target_right_class) for role in model.roles} == {4}
    assert {
        (program.reverse, program.body) for program in model.programs
    } == {
        (role.program.reverse, role.program.body) for role in hidden_roles
    }


def test_frozen_model_transfers_to_unseen_left_right_combinations():
    training, _roles, _episodes = make_combinatorial_context_stream(
        seed=7,
        split="train",
    )
    evaluation_stream, _roles2, evaluation_episodes = make_combinatorial_context_stream(
        seed=97,
        split="evaluation",
        evaluation_repeats=2,
    )
    model = discover_factorized_context_model(training)
    evaluation = evaluate_factorized_context_model(model, evaluation_stream)
    boundary = predicted_boundary_scores(evaluation, evaluation_episodes)

    assert boundary["precision"] == 1.0
    assert boundary["recall"] == 1.0
    assert evaluation.paired == 24
    assert evaluation.exact_accuracy == 1.0
    assert evaluation.context_scan_operations > evaluation.program_operations


def test_exact_pair_and_previous_exact_anchor_baselines_fail_on_unseen_combinations():
    training, _roles, _episodes = make_combinatorial_context_stream(
        seed=7,
        split="train",
    )
    evaluation_stream, _roles2, _evaluation_episodes = make_combinatorial_context_stream(
        seed=97,
        split="evaluation",
        evaluation_repeats=2,
    )
    model = discover_factorized_context_model(training)
    exact_pair = evaluate_exact_pair_baseline(model, evaluation_stream)
    rii_002 = discover_loop_interchange_model(
        training,
        DiscoveryConfig(maximum_gap=12),
    )

    assert exact_pair.paired == 0
    assert rii_002.links == ()


def test_factorized_context_code_is_linear_in_anchor_classes_not_cross_product():
    training, _roles, _episodes = make_combinatorial_context_stream(
        seed=7,
        split="train",
    )
    model = discover_factorized_context_model(training)

    assert model.learned_payload_bits == 1251
    assert model.exact_cross_product_template_bits == 4608
    assert model.learned_payload_bits < model.exact_cross_product_template_bits


def test_independent_targets_do_not_produce_a_context_role():
    control, _roles, _episodes = make_combinatorial_context_stream(
        seed=1701,
        split="train",
        independent_targets=True,
    )
    model = discover_factorized_context_model(control)
    assert model.roles == ()
    assert model.programs == ()


def test_public_discovery_api_contains_no_task_or_boundary_metadata():
    names = set(discover_factorized_context_model.__code__.co_varnames)
    assert "task_id" not in names
    assert "domain" not in names
    assert "event_boundaries" not in names
    assert "aligned_examples" not in names
    assert "hidden_roles" not in names


def test_end_to_end_result_is_bounded_and_passes():
    result = run_experiment()
    assert result["passed"] is True
    assert result["model"]["context_roles"] == 3
    assert result["frozen_unseen_combination_evaluation"]["correct_pairs"] == 24
    assert result["exact_pair_baseline"]["paired_predictions"] == 0
    assert result["rii_002_exact_anchor_baseline"]["surface_links"] == 0
    assert "all individual context variants are seen" in result["claim_boundary"]
