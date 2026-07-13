from minimal_predictive_lm.phase18d4_self_supervised_sequence_learning import (
    InvalidSequenceError,
    audit_sequence_clusters,
    evaluate_masked_queries,
    learn_from_sequences,
    load_sequences,
    run,
    sequence_to_example,
)


def test_training_records_are_sequences_not_supervised_io_records():
    payload = load_sequences()
    assert all(isinstance(row, list) for row in payload["sequences"])
    assert all(len(row) >= 2 for row in payload["sequences"])
    assert all(not isinstance(row, dict) for row in payload["sequences"])


def test_next_value_objective_recovers_latent_behaviors():
    payload = load_sequences()
    partition = learn_from_sequences(payload["sequences"])
    assert len(partition.programs) == 7
    assert audit_sequence_clusters(partition, payload["audit_clusters"])
    assert evaluate_masked_queries(partition, payload["episodes"]) == (14, 14, 14)


def test_appended_sequences_add_behavior_without_code_change():
    payload = load_sequences()
    initial = learn_from_sequences(payload["sequences"])
    final_sequences = tuple(payload["sequences"]) + tuple(payload["post_freeze_sequences"])
    final = learn_from_sequences(final_sequences)
    assert len(final.programs) == 8
    assert set(initial.fingerprint()).issubset(set(final.fingerprint()))
    episodes = tuple(payload["episodes"]) + tuple(payload["post_freeze_episodes"])
    assert evaluate_masked_queries(final, episodes) == (16, 16, 16)


def test_sequence_requires_prefix_and_next_value():
    for row in ((), (1,)):
        try:
            sequence_to_example(row)
        except InvalidSequenceError:
            pass
        else:
            raise AssertionError("short sequence must fail")


def test_all_phase18d4_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["raw_token_language_modeling"] is False
    assert payload["claim_boundary"]["llm_like_general_learning"] is False
