#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import audit_r0_acceptance_bundle as gate


VALID = {"valid": True, "errors": [], "classification": "reproduced"}
INVALID_RAW_LOG = {
    "valid": False,
    "errors": ["run 1: raw-log peak_rss_bytes mismatch"],
    "classification": "initial_reproduction_failure",
}


class AcceptanceRawLogMeasurementBindingTests(unittest.TestCase):
    def _patch_all(self, raw_result: dict):
        patchers = [
            patch.object(gate.evaluation_contract, "validate_dataset", return_value=VALID),
            patch.object(gate.schema_alias, "audit", return_value=VALID),
            patch.object(gate.explicit_holdout_condition, "audit", return_value=VALID),
            patch.object(gate.prediction_eval_split_scope, "audit", return_value=VALID),
            patch.object(gate.prediction_payload, "audit_rows", return_value=VALID),
            patch.object(gate.prediction_metric_coverage, "audit", return_value=VALID),
            patch.object(gate.evaluation_contract, "score", return_value=VALID),
            patch.object(gate.evaluation_contract, "audit_artifacts", return_value=VALID),
            patch.object(gate.artifact_eval_split_scope, "audit", return_value=VALID),
            patch.object(gate.nonzero_measurements, "audit", return_value=VALID),
            patch.object(gate.artifact_path_containment, "audit", return_value=VALID),
            patch.object(gate.raw_log_measurement_binding, "audit", return_value=raw_result),
            patch.object(gate.prediction_cell_binding, "audit", return_value=VALID),
            patch.object(gate.prediction_statistics, "audit", return_value=VALID),
            patch.object(gate.statistics_recomputation, "audit", return_value=VALID),
            patch.object(gate.public_baseline_reproduction, "audit", return_value=VALID),
            patch.object(gate.public_baseline_statistics_binding, "audit", return_value=VALID),
        ]
        return patchers

    def _run(self, raw_result: dict) -> dict:
        patchers = self._patch_all(raw_result)
        for patcher in patchers:
            patcher.start()
        self.addCleanup(lambda: [patcher.stop() for patcher in reversed(patchers)])
        with tempfile.TemporaryDirectory() as tmp:
            return gate.audit_acceptance([], [], {"runs": [{}]}, Path(tmp))

    def test_all_contracts_pass(self):
        result = self._run(VALID)
        self.assertTrue(result["valid"])
        self.assertEqual(result["classification"], "reproduced")
        self.assertIn("raw_log_measurement_binding_contract", result["checks"])
        self.assertTrue(result["raw_logs_must_contain_exactly_one_matching_measurement_record"])

    def test_unbound_raw_log_alone_rejects_bundle(self):
        result = self._run(INVALID_RAW_LOG)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertEqual(result["failed_contracts"], ["raw_log_measurement_binding_contract"])
        self.assertTrue(result["raw_log_measurements_must_equal_manifest_claims"])
        self.assertTrue(result["plain_text_or_unbound_resource_logs_forbidden"])


if __name__ == "__main__":
    unittest.main()
