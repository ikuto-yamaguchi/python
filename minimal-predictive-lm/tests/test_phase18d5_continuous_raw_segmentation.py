from minimal_predictive_lm.phase18d5_continuous_raw_segmentation import (
    RawGrammarError,
    evaluate_raw_episodes,
    induce_raw_grammar,
    load_raw_stream,
    parse_raw_stream,
    run,
)


def test_record_and_field_delimiters_are_inferred_from_one_string():
    payload = load_raw_stream()
    assert isinstance(payload["raw_stream"], str)
    grammar = induce_raw_grammar(payload["raw_stream"])
    assert (grammar.record_separator, grammar.field_separator) == (";", ",")
    assert len(grammar.sequences) == 35
    assert len(grammar.partition.programs) == 7


def test_delimiter_symbols_are_not_hardcoded():
    payload = load_raw_stream()
    renamed = payload["raw_stream"].replace(",", "\0").replace(";", "|").replace("\0", "~")
    grammar = induce_raw_grammar(renamed)
    assert (grammar.record_separator, grammar.field_separator) == ("|", "~")
    original = induce_raw_grammar(payload["raw_stream"])
    assert grammar.partition.fingerprint() == original.partition.fingerprint()


def test_raw_support_routes_all_heldout_queries():
    payload = load_raw_stream()
    grammar = induce_raw_grammar(payload["raw_stream"])
    assert evaluate_raw_episodes(grammar, payload["episodes"]) == (14, 14, 14)


def test_appended_raw_text_discovers_one_new_behavior():
    payload = load_raw_stream()
    initial = induce_raw_grammar(payload["raw_stream"])
    combined = payload["raw_stream"] + initial.record_separator + payload["post_freeze_raw"]
    final = induce_raw_grammar(combined)
    assert len(final.partition.programs) == 8
    assert set(initial.partition.fingerprint()).issubset(set(final.partition.fingerprint()))
    episodes = tuple(payload["episodes"]) + tuple(payload["post_freeze_episodes"])
    assert evaluate_raw_episodes(final, episodes) == (16, 16, 16)


def test_invalid_raw_grammar_abstains():
    try:
        induce_raw_grammar("1,2,3,4,5")
    except RawGrammarError:
        pass
    else:
        raise AssertionError("one punctuation kind cannot identify two delimiter roles")


def test_all_phase18d5_theorem_checks_pass():
    result = run()
    assert result["all_theorem_checks_pass"]
    assert all(result["theorem_checks"].values())
    assert result["claim_boundary"]["autonomous_general_tokenization"] is False
    assert result["claim_boundary"]["llm_like_general_learning"] is False
