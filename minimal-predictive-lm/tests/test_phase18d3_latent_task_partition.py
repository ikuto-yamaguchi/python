from minimal_predictive_lm.phase18d3_latent_task_partition import (
    NonIdentifiableRoutingError,
    audit_gold_separation,
    discover_partition,
    evaluate_episodes,
    load_stream,
    route_from_support,
    run,
)


def test_task_count_and_boundaries_are_inferred_without_ids():
    payload = load_stream()
    initial_stream = tuple(payload["stream"])
    partition = discover_partition(initial_stream)
    assert len(partition.programs) == 7
    assert audit_gold_separation(partition, initial_stream)
    assert all("id" not in example for example in initial_stream)


def test_support_examples_route_queries_without_task_names():
    payload = load_stream()
    partition = discover_partition(tuple(payload["stream"]))
    assert evaluate_episodes(partition, payload["episodes"]) == (14, 14, 14)


def test_appended_examples_create_a_new_program_without_source_change():
    payload = load_stream()
    initial = discover_partition(tuple(payload["stream"]))
    final_stream = tuple(payload["stream"]) + tuple(payload["post_freeze_stream"])
    final = discover_partition(final_stream)
    assert len(initial.programs) == 7
    assert len(final.programs) == 8
    assert set(initial.fingerprint()).issubset(set(final.fingerprint()))
    episodes = tuple(payload["episodes"]) + tuple(payload["post_freeze_episodes"])
    assert evaluate_episodes(final, episodes) == (16, 16, 16)


def test_stream_order_and_audit_labels_do_not_change_learning():
    payload = load_stream()
    stream = tuple(payload["stream"])
    original = discover_partition(stream)
    reversed_partition = discover_partition(tuple(reversed(stream)))
    relabeled = tuple({**example, "gold": "unused"} for example in stream)
    relabeled_partition = discover_partition(relabeled)
    assert original.fingerprint() == reversed_partition.fingerprint()
    assert original.fingerprint() == relabeled_partition.fingerprint()


def test_ambiguous_support_abstains():
    payload = load_stream()
    final = discover_partition(
        tuple(payload["stream"]) + tuple(payload["post_freeze_stream"])
    )
    try:
        route_from_support(
            final,
            ({"inputs": {"u": 0, "v": 0}, "output": 0},),
        )
    except NonIdentifiableRoutingError:
        pass
    else:
        raise AssertionError("ambiguous support must abstain")


def test_all_phase18d3_theorem_checks_pass():
    result = run()
    assert result["all_theorem_checks_pass"]
    assert all(result["theorem_checks"].values())
    assert result["claim_boundary"]["raw_unlabeled_pretraining"] is False
    assert result["claim_boundary"]["llm_like_general_learning"] is False
