from minimal_predictive_lm.phase18b9_raw_japanese_span_schema import (
    NonIdentifiableRawSchemaError,
    ambiguous_calibration_is_rejected,
    evaluate,
    induce,
    parse,
    run,
    schema_intervention_changes_prediction,
    tampered_solution_is_rejected,
    unknown_extra_and_unit_mismatch_abstain,
    unsupported_question_abstains,
)


def test_raw_relation_spans_and_equations_are_uniquely_induced():
    model, fit = induce()
    assert fit == {"candidates": 217800, "errors": 0, "second": 3}
    assert (model.count_program, model.value_program) == ("SUM", "WEIGHTED_SUM")
    assert set(dict(model.cue_roles).values()) == {"COUNT", "RATE", "VALUE"}


def test_unseen_domains_orders_and_entity_directions_are_exact():
    model, _ = induce()
    assert evaluate(model) == (1.0, 1.0, 1.0)


def test_parser_has_no_explicit_target_clue_or_question_prefix():
    model, _ = induce()
    sample = (
        "背景説明だけが先にある。子供券一つ分の値は500円である。"
        "大人券と子供券は全部で17枚ある。売上の合計は11300円だった。"
        "大人券の単価は900円だ。大人券と子供券はそれぞれ何枚か。"
    )
    parsed = parse(sample)
    assert parsed.entities == ("大人券", "子供券")
    assert len(parsed.facts) == 4
    assert model.answer_parsed(parsed) is not None


def test_ambiguous_schema_is_rejected():
    assert ambiguous_calibration_is_rejected()
    try:
        induce(())
    except (NonIdentifiableRawSchemaError, ValueError):
        pass


def test_unknown_extra_unit_and_question_fail_safely():
    model, _ = induce()
    assert unknown_extra_and_unit_mismatch_abstain(model)
    assert unsupported_question_abstains(model)


def test_internal_schema_and_proof_are_causally_checked():
    model, _ = induce()
    assert schema_intervention_changes_prediction(model)
    assert tampered_solution_is_rejected(model)


def test_all_phase18b9_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["free_japanese_parsing"] is False
    assert payload["claim_boundary"]["unseen_paraphrase_understanding"] is False
    assert payload["claim_boundary"]["high_school_intelligence"] is False
