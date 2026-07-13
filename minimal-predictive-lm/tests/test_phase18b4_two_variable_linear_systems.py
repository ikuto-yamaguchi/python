from phase18b4_two_variable_linear_systems import (
    ambiguous_calibration_is_rejected,
    evaluate,
    heldout,
    induce_relation_model,
    inconsistent_systems_abstain,
    one_equation_abstains,
    run,
    singular_systems_abstain,
    tampered_proof_is_rejected,
)


def test_relation_semantics_are_induced_uniquely():
    model, fit = induce_relation_model()
    assert dict(model.relation_map) == {"合わせる": "ADD", "引く": "SUB"}
    assert fit == {"candidates": 2, "errors": 0, "second": 3}


def test_heldout_negative_fractional_systems_are_exact():
    model, _ = induce_relation_model()
    accuracy, coverage, verified = evaluate(model)
    assert (accuracy, coverage, verified) == (1.0, 1.0, 1.0)
    assert len(heldout()) == 12
    assert any(x < 0 or y < 0 or x.denominator != 1 or y.denominator != 1 for _, (x, y) in heldout())


def test_singular_inconsistent_and_incomplete_systems_abstain():
    model, _ = induce_relation_model()
    assert singular_systems_abstain(model)
    assert inconsistent_systems_abstain(model)
    assert one_equation_abstains(model)


def test_tampered_proof_is_rejected():
    model, _ = induce_relation_model()
    assert tampered_proof_is_rejected(model)


def test_ambiguous_calibration_is_detected():
    assert ambiguous_calibration_is_rejected()


def test_all_phase18b4_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["high_school_mathematics"] is False
