from minimal_predictive_lm.cap_gen_003_opaque_roles import run_experiment


def test_frozen_gate_and_claim_boundary() -> None:
    result = run_experiment()
    assert result["passed"] is True
    assert "prior art" in result["claim_boundary"]
    assert "not raw-byte event discovery" in result["claim_boundary"]
