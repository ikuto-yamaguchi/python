from functools import lru_cache

from minimal_predictive_lm.phase18d6_utf8_byte_codec_induction import (
    _bytes_from_hex,
    parse_byte_stream,
)
from minimal_predictive_lm.phase18d7_locally_stationary_viterbi import (
    calibration_grammar,
    enumerate_program_states,
    load_local_stream,
)
from minimal_predictive_lm.phase18d8_online_prequential_filter import (
    _block_end_positions,
    _expand_blocks,
    _prediction_errors,
    _same_signature_switches,
    initial_prior,
    online_filter,
    predict_from_prior,
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
    states, _ = enumerate_program_states(initial_records)
    return payload, initial_records, post_records, states


def test_same_position_prediction_cannot_read_counterfactual_target():
    _, records, _, states = _fixture()
    prior = initial_prior(states)
    prefix = records[0][:-1]
    first = predict_from_prior(prior, prefix, states)
    counterfactual_record = tuple(prefix) + ("a target that never enters prediction",)
    second = predict_from_prior(prior, counterfactual_record[:-1], states)
    assert first.value == second.value
    assert first.best_states == second.best_states


def test_future_suffix_cannot_rewrite_past_online_predictions():
    _, initial_records, post_records, states = _fixture()
    initial = online_filter(initial_records, states)
    extended = online_filter(initial_records + post_records, states)
    assert extended.predictions[: len(initial.predictions)] == initial.predictions
    assert extended.posterior_path[: len(initial.posterior_path)] == initial.posterior_path


def test_online_regret_is_localized_to_unannounced_same_signature_switches():
    payload, records, _, states = _fixture()
    result = online_filter(records, states)
    errors = set(_prediction_errors(result, records))
    switches = set(_same_signature_switches(records, payload["audit_blocks"]))
    assert errors <= {0, *switches}
    assert result.covered_accuracy >= 0.95
    assert result.overall_accuracy >= 0.80


def test_every_initial_block_is_identified_by_its_end_without_support_episode():
    payload, records, _, states = _fixture()
    result = online_filter(records, states)
    ops = result.posterior_ops()
    ends = _block_end_positions(payload["audit_blocks"])
    assert len(records) == len(_expand_blocks(payload["audit_blocks"]))
    assert all(ops[index] == label for index, label in ends)


def test_post_freeze_min_is_discovered_from_stream_update_only():
    payload, initial_records, post_records, states = _fixture()
    result = online_filter(initial_records + post_records, states)
    post_start = len(initial_records)
    min_positions = [
        index
        for index, operation in enumerate(result.posterior_ops()[post_start:], start=post_start)
        if operation == "MIN2"
    ]
    assert min_positions
    assert min_positions[0] - post_start + 1 <= 2
    final_blocks = tuple(payload["audit_blocks"]) + tuple(payload["post_freeze_audit_blocks"])
    assert all(result.posterior_ops()[index] == label for index, label in _block_end_positions(final_blocks))


def test_online_work_is_linear_in_stream_length():
    _, records, _, states = _fixture()
    one = online_filter(records, states)
    two = online_filter(records + records, states)
    ratio = two.stats.total_operations / one.stats.total_operations
    assert 1.95 <= ratio <= 2.05


def test_all_phase18d8_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["resources"]["large_stream_exact_cover_nodes"] == 0
    assert payload["campaign"]["support_episodes_supplied"] is False
    assert payload["claim_boundary"]["zero_error_at_unannounced_same_signature_change_points"] is False
    assert payload["claim_boundary"]["llm_like_general_learning"] is False
