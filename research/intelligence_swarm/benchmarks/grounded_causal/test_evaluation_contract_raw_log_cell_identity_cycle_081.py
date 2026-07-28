#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import evaluation_contract as ec


def measurement(domain: str, condition: str) -> dict:
    return {
        "record_type": "r0_measurement",
        "method": "correct",
        "seed": 1,
        "domain": domain,
        "split": "TEST",
        "condition": condition,
        "code_commit": "a" * 40,
        "model_bytes": 10,
        "peak_rss_bytes": 20,
        "training_wall_seconds": 1.5,
        "cpu_inference_ms_per_item": 0.25,
        "model_sha256": "b" * 64,
        "data_sha256": "c" * 64,
    }


def test_raw_log_cell_uses_canonical_domain_and_condition() -> None:
    left = measurement("RTFM", "entity_holdout+dynamics_holdout")
    right = measurement("ＲＴＦＭ", "DYNAMICS_HOLDOUT | ENTITY_HOLDOUT")
    assert ec._raw_log_cell(left) == ec._raw_log_cell(right)


def test_raw_log_binding_compares_canonical_cell_labels() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        log = root / "run.json"
        log.write_text(json.dumps(measurement("ＲＴＦＭ", "DYNAMICS_HOLDOUT | ENTITY_HOLDOUT")), encoding="utf-8")
        run = measurement("rtfm", "entity_holdout+dynamics_holdout")
        run["raw_log_path"] = log.name
        errors, finding = ec._audit_run_raw_log_binding(run, 1, root, {})
        assert errors == []
        assert finding["matching_measurement_records"] == 1
        assert finding["cell"][2] == "rtfm"
        assert finding["cell"][4] == "dynamics_holdout+entity_holdout"


def test_patch_contract_is_present() -> None:
    source = Path(ec.__file__).read_text(encoding="utf-8")
    assert "normalized_resource_cell_identity_required" in source
    assert "artifact domain labels collide after canonicalization" in source
    assert "artifact condition labels collide after canonicalization" in source


if __name__ == "__main__":
    test_raw_log_cell_uses_canonical_domain_and_condition()
    test_raw_log_binding_compares_canonical_cell_labels()
    test_patch_contract_is_present()
    print("cycle 081 raw-log cell identity regression: ok")
