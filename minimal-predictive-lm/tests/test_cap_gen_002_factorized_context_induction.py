import pytest

from minimal_predictive_lm.cap_gen_002_factorized_context_induction import (
    ContextDiscoveryConfig,
    discover_factorized_context_model,
    evaluate_exact_pair_baseline,
    evaluate_factorized_context_model,
    make_combinatorial_context_stream,
    predicted_boundary_scores,
    training_boundary_scores,
)
from minimal_predictive_lm.cap_gen_002_loop_microprogram_induction import (
    discover_loop_interchange_model,
)
from minimal_predictive_lm.cap_gen_002_raw_interchange_induction import DiscoveryConfig


@pytest.fixture(scope="module")
def training_bundle():
    return make_combinatorial_context_stream(seed=7, split="train")


@pytest.fixture(scope="module")
def evaluation_bundle():
    return make_combinatorial_context_stream(
        seed=97,
        split="evaluation",
        evaluation_repeats=2,
    )


@pytest.fixture(scope="module")
def trained_model(training_bundle):
    training, _hidden_roles, _episodes = training_bundle
    return discover_factorized_context_model(training, ContextDiscoveryConfig())


@pytest.fixture(scope="module")
def frozen_evaluation(trained_model, evaluation_bundle):
    evaluation_stream, _roles, _episodes = evaluation_bundle
    return evaluate_factorized_context_model(trained_model, evaluation_stream)


@pytest.fixture(scope="module")
def control_model():
    control, _roles, _episodes = make_combinatorial_context_stream(
        seed=1701,
        split="train",
        independent_targets=True,
    )
    return discover_factorized_context_model(control)


def test_training_has_no_repeated_full_context_pair_across_evaluation_split(
    training_bundle,
    evaluation_bundle,
):
    _training, _roles, training_episodes = training_bundle
    _evaluation, _roles2, evaluation_episodes = evaluation_bundle

    training_source_pairs = {row.source_context_pair for row in training_episodes}
    training_target_pairs = {row.target_context_pair for row in training_episodes}
    evaluation_source_pairs = {row.source_context_pair for row in evaluation_episodes}
    evaluation_target_pairs = {row.target_context_pair for row in evaluation_episodes}

    assert training_source_pairs.isdisjoint(evaluation_source_pairs)
    assert training_target_pairs.isdisjoint(evaluation_target_pairs)
    assert len(training_source_pairs) == 36
    assert len(evaluation_source_pairs) == 12


def test_joint_discovery_learns_three_factorized_roles_and_all_training_boundaries(
    training_bundle,
    trained_model,
):
    _training, hidden_roles, episodes = training_bundle
    boundary = training_boundary_scores(trained_model, episodes)

    assert len(trained_model.roles) == 3
    assert len(trained_model.programs) == 3
    assert boundary["precision"] == 1.0
    assert boundary["recall"] == 1.0
    assert {len(role.source_left_class) for role in trained_model.roles} == {4}
    assert {len(role.source_right_class) for role in trained_model.roles} == {4}
    assert {len(role.target_left_class) for role in trained_model.roles} == {4}
    assert {len(role.target_right_class) for role in trained_model.roles} == {4}
    assert {
        (program.reverse, program.body) for program in trained_model.programs
    } == {
        (role.program.reverse, role.program.body) for role in hidden_roles
    }


def test_frozen_model_transfers_to_unseen_left_right_combinations(
    evaluation_bundle,
    frozen_evaluation,
):
    _evaluation_stream, _roles, evaluation_episodes = evaluation_bundle
    boundary = predicted_boundary_scores(frozen_evaluation, evaluation_episodes)

    assert boundary["precision"] == 1.0
    assert boundary["recall"] == 1.0
    assert frozen_evaluation.paired == 24
    assert frozen_evaluation.exact_accuracy == 1.0
    assert frozen_evaluation.context_scan_operations > frozen_evaluation.program_operations


def test_exact_pair_and_previous_exact_anchor_baselines_fail_on_unseen_combinations(
    training_bundle,
    evaluation_bundle,
    trained_model,
):
    training, _roles, _episodes = training_bundle
    evaluation_stream, _roles2, _evaluation_episodes = evaluation_bundle
    exact_pair = evaluate_exact_pair_baseline(trained_model, evaluation_stream)
    rii_002 = discover_loop_interchange_model(
        training,
        DiscoveryConfig(maximum_gap=12),
    )

    assert exact_pair.paired == 0
    assert rii_002.links == ()


def test_factorized_context_code_is_linear_in_anchor_classes_not_cross_product(
    trained_model,
):
    assert trained_model.learned_payload_bits == 1251
    assert trained_model.exact_cross_product_template_bits == 4608
    assert trained_model.learned_payload_bits < trained_model.exact_cross_product_template_bits


def test_independent_targets_do_not_produce_a_context_role(control_model):
    assert control_model.roles == ()
    assert control_model.programs == ()


def test_public_discovery_api_contains_no_task_or_boundary_metadata():
    names = set(discover_factorized_context_model.__code__.co_varnames)
    assert "task_id" not in names
    assert "domain" not in names
    assert "event_boundaries" not in names
    assert "aligned_examples" not in names
    assert "hidden_roles" not in names
