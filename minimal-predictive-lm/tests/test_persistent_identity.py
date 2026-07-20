import json
import random

from minimal_predictive_lm.persistent_identity import (
    PredictiveIdentityVersionSpace,
    make_case,
    run_experiment,
)


def test_informative_identity_is_unique():
    previous, current, truth = make_case(random.Random(1), 4, True, False)
    hypotheses, _, _ = PredictiveIdentityVersionSpace().infer(previous, current)
    assert hypotheses == [truth]


def test_symmetric_identity_remains_ambiguous():
    previous, current, _ = make_case(random.Random(1), 4, False, False)
    hypotheses, _, _ = PredictiveIdentityVersionSpace().infer(previous, current)
    assert len(hypotheses) > 1


def test_integrated_claim_stays_false(tmp_path):
    report = run_experiment(tmp_path / "report.json")
    assert report["summary"]["candidate_supported"] is False
    assert report["summary"]["highschool_level_passed"] is False
    assert report["summary"]["integrated_gate_mean"] == 0.0
    saved = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert saved["summary"]["native_japanese_communication_passed"] is False
