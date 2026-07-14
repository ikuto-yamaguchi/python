from __future__ import annotations

from fractions import Fraction

from minimal_predictive_lm.meci_core import OperationalQuotient, QuotientByteModel, huffman_code


def test_operational_quotient_is_coarsest_exact_partition() -> None:
    histories = ("h0", "h1", "h2", "h3")
    queries = ("next", "act")
    answers = {
        ("h0", "next"): "a", ("h0", "act"): "left",
        ("h1", "next"): "a", ("h1", "act"): "left",
        ("h2", "next"): "b", ("h2", "act"): "left",
        ("h3", "next"): "b", ("h3", "act"): "right",
    }
    quotient = OperationalQuotient.build(histories, queries, answers)
    assert quotient.state_count == 3
    assert quotient.state_of["h0"] == quotient.state_of["h1"]
    assert quotient.state_of["h2"] != quotient.state_of["h3"]
    assert quotient.worst_case_memory_lower_bound_bits == 2
    assert quotient.canonical_state_bits == 2


def test_huffman_expected_update_is_within_one_bit_of_entropy() -> None:
    code = huffman_code({"stay": 0.75, "jump": 0.125, "reset": 0.125})
    assert code.expected_decisions >= code.entropy_lower_bound
    assert code.expected_decisions < code.entropy_lower_bound + 1.0


def test_byte_model_merges_empirically_equivalent_contexts() -> None:
    model = QuotientByteModel(max_order=3).fit(b"abababab\n")
    assert model.state_count <= model.context_count
    assert model.distribution(b"xxa") == {ord("b"): Fraction(1, 1)}
    assert model.predict(b"xxa") == ord("b")


def test_byte_model_generates_learned_continuation() -> None:
    model = QuotientByteModel(max_order=8).fit(b"<U>hi\n<A>hello\n<U>hi\n<A>hello\n")
    result = model.generate(b"<U>hi\n<A>", max_new_bytes=6, stop=b"\n")
    assert result == b"hello\n"


def test_report_exposes_memory_metric() -> None:
    model = QuotientByteModel(max_order=4).fit(b"abcabcabc")
    report = model.report()
    assert report["predictive_states_after_quotient"] <= report["contexts_before_quotient"]
    assert report["working_state_lower_bound_bits"] >= 0
