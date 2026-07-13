from functools import lru_cache
import random

from minimal_predictive_lm.phase18d6_utf8_byte_codec_induction import (
    _bytes_from_hex,
    parse_byte_stream,
)
from minimal_predictive_lm.phase18d7_locally_stationary_viterbi import (
    _expand_blocks,
    audit_path,
    calibration_grammar,
    enumerate_program_states,
    evaluate_context_episodes,
    infer_locally_stationary_path,
    load_local_stream,
    run,
)


@lru_cache(maxsize=1)
def _fixture():
    payload = load_local_stream()
    grammar = calibration_grammar()
    initial_records = parse_byte_stream(
        _bytes_from_hex(payload["ordered_stream_hex"]),
        grammar.record_separator,
        grammar.field_separator,
        grammar.numeric_zero_codepoint,
    )
    post_records = parse_byte_stream(
        _bytes_from_hex(payload["post_freeze_hex"]),
        grammar.record_separator,
        grammar.field_separator,
        grammar.numeric_zero_codepoint,
    )
    states, evaluated = enumerate_program_states(initial_records)
    return payload, grammar, initial_records, post_records, states, evaluated


def _initial_labels(payload, records):
    return _expand_blocks(
        payload["audit_blocks"],
        target_length=len(records),
    )


def test_generic_candidate_state_library_has_expected_behavior_classes():
    _, _, _, _, states, evaluated = _fixture()
    assert len(states) == 130
    assert evaluated > len(states)


def test_viterbi_recovers_every_locally_stationary_record():
    payload, _, records, _, states, _ = _fixture()
    result = infer_locally_stationary_path(records, states)
    labels = _initial_labels(payload, records)
    assert audit_path(result, labels) == (len(records), len(records))
    assert len(records) == 253
    assert len(result.used_states()) == 7


def test_local_persistence_is_causal_not_decorative():
    payload, _, records, _, states, _ = _fixture()
    labels = _initial_labels(payload, records)
    no_prior = infer_locally_stationary_path(records, states, switch_penalty=0)
    no_prior_correct, total = audit_path(no_prior, labels)
    assert no_prior_correct < total

    permutation = list(range(len(records)))
    random.Random(20260713).shuffle(permutation)
    shuffled_records = tuple(records[index] for index in permutation)
    shuffled_labels = tuple(labels[index] for index in permutation)
    shuffled = infer_locally_stationary_path(shuffled_records, states)
    shuffled_correct, shuffled_total = audit_path(shuffled, shuffled_labels)
    assert shuffled_correct < shuffled_total


def test_context_routing_and_post_freeze_behavior_are_data_only():
    payload, grammar, records, post_records, states, _ = _fixture()
    initial = infer_locally_stationary_path(records, states)
    assert evaluate_context_episodes(
        grammar, initial.used_states(), payload["episodes"]
    ) == (14, 14, 14)

    final = infer_locally_stationary_path(records + post_records, states)
    episodes = tuple(payload["episodes"]) + tuple(payload["post_freeze_episodes"])
    assert len(final.used_states()) == 8
    assert evaluate_context_episodes(
        grammar, final.used_states(), episodes
    ) == (16, 16, 16)
    assert set(initial.fingerprint()).issubset(set(final.fingerprint()))


def test_viterbi_work_scales_linearly_with_record_count():
    _, _, records, _, states, _ = _fixture()
    one = infer_locally_stationary_path(records, states)
    two = infer_locally_stationary_path(records + records, states)
    ratio = two.stats.total_operations / one.stats.total_operations
    assert 1.95 <= ratio <= 2.05


def test_all_phase18d7_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["resources"]["large_stream_exact_cover_nodes"] == 0
    assert payload["claim_boundary"]["arbitrarily_interleaved_task_discovery"] is False
    assert payload["claim_boundary"]["llm_like_general_learning"] is False
