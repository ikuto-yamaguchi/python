from minimal_predictive_lm.sparc_hs16_public_gate import (
    _load_baseline,
    _runtime_fingerprint,
)


def test_hs16_runtime_fingerprint_is_stable_and_baseline_is_frozen():
    assert _runtime_fingerprint() == _runtime_fingerprint()
    baseline = _load_baseline()
    assert baseline["capability_id"] == "CAP-GEN-001"
    assert baseline["suite"]["examples"] == 600
    assert baseline["suite"]["axes"] == 15
    assert baseline["score"]["correct"] == 398
    assert baseline["axis_scores"]["belief_propagation"]["correct"] == 0
    assert baseline["axis_scores"]["formal_validity"]["correct"] == 0
