import inspect

import pytest

from minimal_predictive_lm.phase18d14_byte_codec_core import (
    NoJointModelError,
    PrefixedPairCodec,
    TaggedByteCodec,
    encode_records,
    joint_infer,
    primitive_signature,
    shift_private_use,
)
from minimal_predictive_lm.phase18d14_joint_byte_codec import (
    load_dataset,
    negative_controls,
    run,
)


def test_joint_codec_and_two_primitives_are_unique():
    result = joint_infer(load_dataset()["stream_hex"])
    assert result.grammar_candidates == 2
    assert result.eligible_candidates == 1
    assert result.positive_candidates == 1
    assert result.selected.grammar.codec.kind == "tagged_mixed_width"
    assert len(result.selected.grammar.records) == 48
    assert primitive_signature(result) == (
        ("index", 1, 1),
        ("element", 1, 1),
    )


def test_utf8_is_not_a_hidden_fixed_decoder():
    raw = bytes.fromhex(load_dataset()["stream_hex"])
    with pytest.raises(UnicodeDecodeError):
        raw.decode("utf-8")


def test_promotions_are_cross_alphabet_and_leave_only_noise():
    result = joint_infer(load_dataset()["stream_hex"])
    promotions = result.selected.promotions
    assert tuple(row.position for row in promotions) == (15, 20)
    assert all(
        set(row.support_alphabets)
        == {"ascii_letters", "private_use"}
        for row in promotions
    )
    assert [row.position for row in result.selected.unresolved] == [5, 19, 47]


def test_marker_separator_and_payload_shift_are_not_hardcoded():
    original = joint_infer(load_dataset()["stream_hex"])
    records = shift_private_use(original.selected.grammar.records, 17)
    transformed = encode_records(
        records,
        TaggedByteCodec(0xF6),
        0xF4,
        0xF5,
    )
    recovered = joint_infer(transformed)
    assert recovered.selected.grammar.record_separator == 0xF4
    assert recovered.selected.grammar.field_separator == 0xF5
    assert recovered.selected.grammar.codec.render() == {
        "kind": "tagged_mixed_width",
        "marker": 0xF6,
    }
    assert primitive_signature(recovered) == primitive_signature(original)


def test_distinct_fixed_width_codec_family_is_recovered():
    original = joint_infer(load_dataset()["stream_hex"])
    transformed = encode_records(
        original.selected.grammar.records,
        PrefixedPairCodec(0xF6, 0xF7),
        0xF4,
        0xF5,
    )
    recovered = joint_infer(transformed)
    assert recovered.selected.grammar.codec.render() == {
        "kind": "prefixed_fixed_width_2",
        "raw_prefix": 0xF6,
        "tagged_prefix": 0xF7,
    }
    assert primitive_signature(recovered) == primitive_signature(original)


def test_ambiguous_or_malformed_streams_abstain():
    assert all(negative_controls().values())
    with pytest.raises(NoJointModelError):
        joint_infer("00")


def test_no_audit_labels_enter_the_learner_api():
    assert "audit_labels" not in inspect.signature(joint_infer).parameters
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["llm_like_general_learning"] is False
    assert payload["claim_boundary"]["high_school_intelligence"] is False
