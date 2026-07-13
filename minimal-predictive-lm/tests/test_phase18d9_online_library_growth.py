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
from minimal_predictive_lm.phase18d8_online_prequential_audit import effective_blocks
from minimal_predictive_lm.phase18d8_online_prequential_filter import (
    _block_end_positions,
    _same_signature_switches,
)
from minimal_predictive_lm.phase18d9_online_library_audit import run
from minimal_predictive_lm.phase18d9_online_library_growth import (
    _growth_prediction_errors,
    grow_program_library,
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


def test_active_library_is_acquired_from_stream_not_preloaded():
    payload, records, _, states = _fixture()
    result = grow_program_library(records, states)
    blocks = effective_blocks(payload["audit_blocks"], len(records))
    expected = {str(row["label"]) for row in blocks}
    assert set(result.acquired_ops()) == expected
    assert len(result.acquired_order) == 7
    assert result.acquisition_positions[0] > 0


def test_every_block_finishes_with_the_acquired_program_active():
    payload, records, _, states = _fixture()
    blocks = effective_blocks(payload["audit_blocks"], len(records))
    result = grow_program_library(records, states)
    ops = result.active_ops()
    assert all(ops[index] == label for index, label in _block_end_positions(blocks))


def test_post_freeze_stream_adds_min_without_source_change():
    _, records, post_records, states = _fixture()
    initial = grow_program_library(records, states)
    final = grow_program_library(records + post_records, states)
    assert set(final.acquired_ops()) - set(initial.acquired_ops()) == {"MIN2"}
    assert len(final.acquired_order) == len(initial.acquired_order) + 1
    assert final.predictions[: len(initial.predictions)] == initial.predictions
    assert final.active_path[: len(initial.active_path)] == initial.active_path


def test_prediction_errors_are_only_unannounced_same_signature_switch_regret():
    payload, records, _, states = _fixture()
    blocks = effective_blocks(payload["audit_blocks"], len(records))
    result = grow_program_library(records, states)
    errors = set(_growth_prediction_errors(result, records))
    switches = set(_same_signature_switches(records, blocks))
    assert errors <= {0, *switches}
    assert result.covered_accuracy >= 0.95
    assert result.coverage >= 0.45


def test_online_library_growth_work_is_near_linear():
    _, records, _, states = _fixture()
    one = grow_program_library(records, states)
    two = grow_program_library(records + records, states)
    ratio = two.stats.total_operations / one.stats.total_operations
    assert 1.8 <= ratio <= 2.2


def test_all_phase18d9_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["campaign"]["active_programs_at_start"] == 0
    assert payload["acquisition"]["initial_program_count"] == 7
    assert payload["acquisition"]["final_program_count"] == 8
    assert payload["resources"]["large_stream_exact_cover_nodes"] == 0
    assert payload["claim_boundary"]["primitive_search_space_learned"] is False
    assert payload["claim_boundary"]["llm_like_general_learning"] is False
