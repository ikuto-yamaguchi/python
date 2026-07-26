#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("r0_acceptance", HERE / "audit_r0_acceptance_bundle.py")
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class R0AcceptanceBundleTests(unittest.TestCase):
    def setUp(self):
        self.data = [{"instance_id": "x"}]
        self.predictions = [{"instance_id": "x"}]
        self.manifest = {"runs": [{}]}
        self.base_dir = HERE

    def patches(self, *, alias_valid=True, payload_valid=True, stats_valid=True, measurements_valid=True):
        return (
            mock.patch.object(AUDIT.evaluation_contract, "validate_dataset", return_value={"valid": True, "errors": []}),
            mock.patch.object(
                AUDIT.schema_alias,
                "audit",
                return_value={"valid": alias_valid, "errors": [] if alias_valid else ["goldStateAfter alias leakage"]},
            ),
            mock.patch.object(AUDIT.prediction_payload, "audit_rows", return_value={"valid": payload_valid, "errors": [] if payload_valid else ["gold leakage"]}),
            mock.patch.object(AUDIT.evaluation_contract, "score", return_value={"valid": True, "errors": []}),
            mock.patch.object(AUDIT.evaluation_contract, "audit_artifacts", return_value={"valid": True, "errors": []}),
            mock.patch.object(
                AUDIT.nonzero_measurements,
                "audit",
                return_value={"valid": measurements_valid, "errors": [] if measurements_valid else ["zero placeholder measurement"]},
            ),
            mock.patch.object(AUDIT.prediction_statistics, "audit", return_value={"valid": stats_valid, "errors": [] if stats_valid else ["checksum mismatch"]}),
        )

    def run_with(self, *, alias_valid=True, payload_valid=True, stats_valid=True, measurements_valid=True):
        patches = self.patches(
            alias_valid=alias_valid,
            payload_valid=payload_valid,
            stats_valid=stats_valid,
            measurements_valid=measurements_valid,
        )
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
            return AUDIT.audit_acceptance(self.data, self.predictions, self.manifest, self.base_dir)

    def test_all_contracts_must_pass(self):
        result = self.run_with()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["classification"], "reproduced")
        self.assertEqual(result["failed_contracts"], [])
        self.assertTrue(result["alias_normalized_leakage_audit_required"])
        self.assertTrue(result["strictly_positive_measured_resources_required"])
        self.assertTrue(result["nonempty_resource_artifacts_required"])

    def test_alias_failure_cannot_be_hidden_by_valid_score(self):
        result = self.run_with(alias_valid=False)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertIn("schema_alias_leakage_contract", result["failed_contracts"])
        self.assertTrue(result["checks"]["paired_statistics_contract"]["valid"])

    def test_payload_failure_cannot_be_hidden_by_valid_score(self):
        result = self.run_with(payload_valid=False)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertIn("prediction_payload_contract", result["failed_contracts"])
        self.assertTrue(result["checks"]["paired_statistics_contract"]["valid"])

    def test_zero_placeholder_measurement_rejects_otherwise_valid_bundle(self):
        result = self.run_with(measurements_valid=False)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertIn("nonzero_measurement_contract", result["failed_contracts"])
        self.assertTrue(result["checks"]["resource_artifact_contract"]["valid"])

    def test_statistics_checksum_failure_rejects_otherwise_valid_bundle(self):
        result = self.run_with(stats_valid=False)
        self.assertFalse(result["valid"])
        self.assertIn("prediction_statistics_evidence_contract", result["failed_contracts"])

    def test_multiple_failures_are_preserved(self):
        result = self.run_with(alias_valid=False, payload_valid=False, stats_valid=False, measurements_valid=False)
        self.assertEqual(
            result["failed_contracts"],
            [
                "nonzero_measurement_contract",
                "prediction_payload_contract",
                "prediction_statistics_evidence_contract",
                "schema_alias_leakage_contract",
            ],
        )
        self.assertEqual(len(result["errors"]), 4)


if __name__ == "__main__":
    unittest.main()
