from minimal_predictive_lm.cap_gen_002_raw_interchange_induction import (
    ByteAffineProgram,
    DiscoveryConfig,
    boundary_scores,
    discover_interchange_model,
    evaluate_frozen_model,
    evaluate_literal_template_baseline,
    make_mixed_raw_stream,
    run_experiment,
)


def test_programs_are_generic_byte_maps_and_reverse_is_compositional():
    assert ByteAffineProgram(False, 1, 3).apply(b"abc") == b"def"
    assert ByteAffineProgram(True, 1, 0).apply(b"abc") == b"cba"


def test_joint_discovery_recovers_boundaries_links_and_shared_operators():
    training, hidden_relations, episodes = make_mixed_raw_stream(
        seed=7,
        instances_per_relation=16,
    )
    model = discover_interchange_model(training, DiscoveryConfig())
    boundary = boundary_scores(model, episodes)

    assert boundary["precision"] == 1.0
    assert boundary["recall"] == 1.0
    assert len(model.links) == 4
    assert len(model.programs) == 2
    assert {program.signature for program in model.programs} == {
        relation.program.signature for relation in hidden_relations
    }
    assert all(link.gain_bits > 0 for link in model.links)


def test_frozen_model_generalizes_to_new_values_without_retraining():
    training, _relations, _episodes = make_mixed_raw_stream(
        seed=7,
        instances_per_relation=16,
    )
    evaluation, _relations2, _episodes2 = make_mixed_raw_stream(
        seed=97,
        instances_per_relation=8,
    )
    model = discover_interchange_model(training)
    result = evaluate_frozen_model(model, evaluation)
    literal = evaluate_literal_template_baseline(training, evaluation, model)

    assert result.coverage == 1.0
    assert result.exact_accuracy == 1.0
    assert result.byte_accuracy == 1.0
    assert literal.exact_accuracy == 0.0
    assert result.inference_operations < result.target_bytes * 2


def test_independent_targets_do_not_create_spurious_operator_links():
    control, _relations, _episodes = make_mixed_raw_stream(
        seed=1701,
        instances_per_relation=16,
        independent_targets=True,
    )
    model = discover_interchange_model(control)
    assert model.links == ()
    assert model.programs == ()


def test_public_api_has_no_task_domain_or_boundary_argument():
    names = set(discover_interchange_model.__code__.co_varnames)
    assert "task_id" not in names
    assert "domain" not in names
    assert "event_boundaries" not in names
    assert "aligned_examples" not in names


def test_end_to_end_experiment_is_honestly_bounded_and_passes():
    result = run_experiment()
    assert result["passed"] is True
    assert "not natural-language" in result["claim_boundary"]
    assert result["model"]["surface_links"] == 4
    assert result["model"]["shared_programs"] == 2
