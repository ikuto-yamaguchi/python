from minimal_predictive_lm.cap_gen_002_loop_microprogram_induction import (
    DEFAULT_PROGRAM_LIBRARY,
    LoopProgram,
    discover_loop_interchange_model,
    evaluate_frozen_loop_model,
    make_loop_microprogram_stream,
    run_experiment,
)
from minimal_predictive_lm.cap_gen_002_raw_interchange_induction import (
    DiscoveryConfig,
    boundary_scores,
    discover_interchange_model,
)


def test_loop_programs_compose_primitives_without_semantic_transform_names():
    assert LoopProgram(True, ("EMIT",)).apply(b"abc") == b"cba"
    assert LoopProgram(False, ("INC", "INC", "INC", "EMIT")).apply(b"abc") == b"def"
    assert LoopProgram(False, ("EMIT", "EMIT")).apply(b"abc") == b"aabbcc"
    assert len(DEFAULT_PROGRAM_LIBRARY) == 682


def test_joint_discovery_recovers_six_links_three_shared_programs_and_boundaries():
    training, hidden_relations, episodes = make_loop_microprogram_stream(
        seed=7,
        instances_per_relation=16,
    )
    model = discover_loop_interchange_model(training)
    boundary = boundary_scores(model, episodes)

    assert boundary["precision"] == 1.0
    assert boundary["recall"] == 1.0
    assert len(model.links) == 6
    assert len(model.programs) == 3
    assert {program.signature for program in model.programs} == {
        relation.program.signature for relation in hidden_relations
    }
    assert any(program.body == ("EMIT", "EMIT") for program in model.programs)


def test_frozen_microprogram_model_generalizes_to_unseen_values():
    training, _relations, _episodes = make_loop_microprogram_stream(
        seed=7,
        instances_per_relation=16,
    )
    evaluation_stream, _relations2, _episodes2 = make_loop_microprogram_stream(
        seed=97,
        instances_per_relation=8,
    )
    model = discover_loop_interchange_model(training)
    evaluation = evaluate_frozen_loop_model(model, evaluation_stream)

    assert evaluation.target_spans == 48
    assert evaluation.coverage == 1.0
    assert evaluation.exact_accuracy == 1.0
    assert evaluation.inference_operations == 822


def test_previous_affine_family_misses_length_changing_duplicate_links():
    training, _relations, _episodes = make_loop_microprogram_stream(
        seed=7,
        instances_per_relation=16,
    )
    config = DiscoveryConfig(maximum_gap=12)
    old_model = discover_interchange_model(training, config)
    new_model = discover_loop_interchange_model(training, config)

    assert len(old_model.links) == 4
    assert len(new_model.links) == 6
    assert all(
        len(source_boundary) == 2
        for link in new_model.links
        for source_boundary in link.source_boundaries
    )


def test_independent_target_control_rejects_all_programs():
    stream, _relations, _episodes = make_loop_microprogram_stream(
        seed=1701,
        instances_per_relation=16,
        independent_targets=True,
    )
    model = discover_loop_interchange_model(stream)
    assert model.links == ()
    assert model.programs == ()


def test_no_task_or_domain_identifier_enters_discovery_api():
    names = set(discover_loop_interchange_model.__code__.co_varnames)
    assert "task_id" not in names
    assert "domain" not in names
    assert "event_boundaries" not in names
    assert "aligned_examples" not in names


def test_end_to_end_result_is_bounded_and_passes():
    result = run_experiment()
    assert result["passed"] is True
    assert result["model"]["surface_links"] == 6
    assert result["model"]["shared_programs"] == 3
    assert result["rii_001_affine_baseline"]["surface_links"] == 4
    assert "not a universal" in result["claim_boundary"]
