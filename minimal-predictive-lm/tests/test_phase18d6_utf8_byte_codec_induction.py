from minimal_predictive_lm.phase18d6_utf8_byte_codec_induction import (
    NonIdentifiableByteGrammarError,
    _bytes_from_hex,
    _encode_numeric_control,
    _shift_private_use_glyphs,
    evaluate_byte_episodes,
    induce_byte_grammar,
    load_byte_stream,
    run,
)


def test_joint_byte_grammar_and_numeric_codebook_are_identified():
    payload = load_byte_stream()
    grammar = induce_byte_grammar(_bytes_from_hex(payload["byte_stream_hex"]))
    assert (grammar.record_separator, grammar.field_separator) == (ord("|"), ord("~"))
    assert grammar.numeric_zero_codepoint == 0xE300
    assert len(grammar.partition.programs) == 7


def test_byte_only_learning_recovers_all_initial_queries():
    payload = load_byte_stream()
    grammar = induce_byte_grammar(_bytes_from_hex(payload["byte_stream_hex"]))
    assert evaluate_byte_episodes(grammar, payload["episodes"]) == (14, 14, 14)


def test_numeric_glyph_offset_is_semantically_irrelevant():
    payload = load_byte_stream()
    raw = _bytes_from_hex(payload["byte_stream_hex"])
    original = induce_byte_grammar(raw)
    shifted = induce_byte_grammar(_shift_private_use_glyphs(raw, 37))
    assert shifted.numeric_zero_codepoint == original.numeric_zero_codepoint + 37
    assert shifted.partition.fingerprint() == original.partition.fingerprint()


def test_translation_invariant_evidence_cannot_identify_numeric_zero():
    raw = _encode_numeric_control(
        ((-2, 5, 5), (7, 3, 7), (-8, -1, -1), (4, 9, 9), (2, 6, 6))
    )
    try:
        induce_byte_grammar(raw)
    except NonIdentifiableByteGrammarError:
        pass
    else:
        raise AssertionError("max-only evidence must leave many numeric offsets equivalent")


def test_appended_byte_stream_adds_min_without_source_change():
    payload = load_byte_stream()
    initial_raw = _bytes_from_hex(payload["byte_stream_hex"])
    initial = induce_byte_grammar(initial_raw)
    final = induce_byte_grammar(
        initial_raw
        + bytes((initial.record_separator,))
        + _bytes_from_hex(payload["post_freeze_hex"])
    )
    assert len(initial.partition.programs) == 7
    assert len(final.partition.programs) == 8
    assert set(initial.partition.fingerprint()).issubset(set(final.partition.fingerprint()))


def test_all_phase18d6_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["arbitrary_atom_parser"] is False
    assert payload["claim_boundary"]["natural_language_pretraining"] is False
