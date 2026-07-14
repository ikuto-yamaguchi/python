from minimal_predictive_lm.cap_gen_004_btq_core import infer_repeat_template


def test_repeat_template_generalizes_variable_trace_length() -> None:
    traces = (
        ("TEST_FALSE", "ADVANCE", "TEST_TRUE", "EMIT_REMAINDER"),
        ("TEST_FALSE", "ADVANCE", "TEST_FALSE", "ADVANCE", "TEST_TRUE", "EMIT_REMAINDER"),
    )
    template = infer_repeat_template(traces)
    assert template is not None
    assert template.prefix == ()
    assert template.motif == ("TEST_FALSE", "ADVANCE")
    assert template.suffix == ("TEST_TRUE", "EMIT_REMAINDER")


def test_map_and_reverse_have_different_behavioral_templates() -> None:
    map_template = infer_repeat_template((("READ", "APPLY", "WRITE") * 2, ("READ", "APPLY", "WRITE") * 4))
    reverse_template = infer_repeat_template((("READ_BACK", "WRITE") * 2, ("READ_BACK", "WRITE") * 5))
    assert map_template is not None
    assert reverse_template is not None
    assert map_template.signature != reverse_template.signature
