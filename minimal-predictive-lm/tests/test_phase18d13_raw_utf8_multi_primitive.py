import pytest

from minimal_predictive_lm.phase18d10_primitive_core import IndexAffinePrimitive
from minimal_predictive_lm.phase18d12_multi_primitive_core import (
    ElementAffinePrimitive,
)
from minimal_predictive_lm.phase18d13_raw_utf8_multi_primitive import (
    NoGrammarError,
    RawLookupPrimitive,
    controls,
    future_hidden_accuracy,
    infer_grammar,
    learn_raw_stream,
    load_dataset,
    run,
)


def test_raw_file_has_only_hex_not_typed_records():
    payload = load_dataset()
    assert set(payload) == {"campaign", "stream_hex", "audit_labels"}
    assert isinstance(payload["stream_hex"], str)
    assert "input" not in payload and "output" not in payload


def test_separator_roles_and_record_count_are_induced():
    payload = load_dataset()
    grammar = infer_grammar(payload["stream_hex"])
    assert grammar.valid_grammars == 1
    assert grammar.record_separator == "|"
    assert grammar.field_separator == "~"
    assert len(grammar.records) == 48


def test_two_heterogeneous_primitives_are_invented_from_raw_stream():
    payload = load_dataset()
    result = learn_raw_stream(payload["stream_hex"])
    assert tuple(p.position for p in result.promotions) == (15, 20)
    assert len(result.library) == 2
    assert isinstance(result.library[0], IndexAffinePrimitive)
    assert (
        result.library[0].multiplier,
        result.library[0].offset,
    ) == (1, 1)
    assert isinstance(result.library[1], ElementAffinePrimitive)
    assert (
        result.library[1].scale,
        result.library[1].offset,
    ) == (1, 1)
    assert not any(isinstance(item, RawLookupPrimitive) for item in result.library)


def test_cross_alphabet_support_and_future_transfer():
    payload = load_dataset()
    result = learn_raw_stream(payload["stream_hex"])
    assert all(
        set(promotion.support_alphabets)
        == {"ascii_letters", "private_use"}
        for promotion in result.promotions
    )
    correct, total = future_hidden_accuracy(
        result,
        payload["audit_labels"],
    )
    assert (correct, total) == (21, 21)


def test_future_suffix_does_not_change_prefix():
    payload = load_dataset()
    full = learn_raw_stream(payload["stream_hex"])
    text = bytes.fromhex(payload["stream_hex"]).decode("utf-8")
    prefix_text = "|".join(text.split("|")[:35])
    prefix = learn_raw_stream(prefix_text.encode("utf-8").hex())
    assert full.predictions[:35] == prefix.predictions
    assert full.observed_operations[:35] == prefix.observed_operations
    assert tuple(
        p.primitive.render() for p in full.promotions
        if p.position < 35
    ) == tuple(p.primitive.render() for p in prefix.promotions)


def test_metagrammar_and_codec_controls():
    payload = load_dataset()
    assert all(controls(payload).values())
    with pytest.raises(NoGrammarError):
        infer_grammar("ff")


def test_all_phase18d13_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["unicode_codepoints_not_raw_bytes_are_atoms"]
    assert payload["claim_boundary"]["candidate_meta_grammar_human_designed"]
    assert not payload["claim_boundary"]["llm_like_general_learning"]
    assert not payload["claim_boundary"]["high_school_intelligence"]
