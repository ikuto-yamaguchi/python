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

    def patches(
        self,
        *,
        alias_valid=True,
        split_scope_valid=True,
        payload_valid=True,
        metric_coverage_valid=True,
        stats_valid=True,
        recomputation_valid=True,
        measurements_valid=True,
        paths_valid=True,
        cell_binding_valid=True,
    ):
        return (
            mock.patch.object(AUDIT.evaluation_contract, "validate_dataset", return_value={"valid": True, "errors": []}),
            mock.patch.object(AUDIT.schema_alias, "audit", return_value={"valid": alias_valid, "errors": [] if alias_valid else ["goldStateAfter alias leakage"]}),
            mock.patch.object(AUDIT.explicit_holdout_condition, "audit", return_value={"valid": True, "errors": []}),
            mock.patch.object(AUDIT.prediction_eval_split_scope, "audit", return_value={"valid": split_scope_valid, "errors": [] if split_scope_valid else ["unregistered split='debug'"]}),
            mock.patch.object(AUDIT.prediction_payload, "audit_rows", return_value={"valid": payload_valid, "errors": [] if payload_valid else ["gold leakage"]}),
            mock.patch.object(AUDIT.prediction_metric_coverage, "audit", return_value={"valid": metric_coverage_valid, "errors": [] if metric_coverage_valid else ["selective metric omission"]}),
            mock.patch.object(AUDIT.evaluation_contract, "score", return_value={"valid": True, "errors": []}),
            mock.patch.object(AUDIT.evaluation_contract, "audit_artifacts", return_value={"valid": True, "errors": []}),
            mock.patch.object(AUDIT.nonzero_measurements, "audit", return_value={"valid": measurements_valid, "errors": [] if measurements_valid else ["zero placeholder measurement"]}),
            mock.patch.object(AUDIT.artifact_path_containment, "audit", return_value={"valid": paths_valid, "errors": [] if paths_valid else ["artifact path escapes bundle root"]}),
            mock.patch.object(AUDIT.prediction_cell_binding, "audit", return_value={"valid": cell_binding_valid, "errors": [] if cell_binding_valid else ["prediction row cell does not match declared cell"]}),
            mock.patch.object(AUDIT.prediction_statistics, "audit", return_value={"valid": stats_valid, "errors": [] if stats_valid else ["checksum mismatch"]}),
            mock.patch.object(AUDIT.statistics_recomputation, "audit", return_value={"valid": recomputation_valid, "errors": [] if recomputation_valid else ["saved statistics differ from recomputation"]}),
        )

    def run_with(self, **kwargs):
        patches = self.patches(**kwargs)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8], patches[9], patches[10], patches[11], patches[12]:
            return AUDIT.audit_acceptance(self.data, self.predictions, self.manifest, self.base_dir)

    def test_all_contracts_must_pass(self):
        result = self.run_with()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["classification"], "reproduced")
        self.assertEqual(result["failed_contracts"], [])
        self.assertTrue(result["alias_normalized_leakage_audit_required"])
        self.assertTrue(result["registered_split_vocabulary_required"])
        self.assertEqual(result["allowed_train_split"], "train")
        self.assertEqual(result["allowed_evaluation_splits"], ["eval", "test", "valid", "validation"])
        self.assertTrue(result["nonregistered_debug_calibration_posthoc_splits_forbidden"])
        self.assertTrue(result["same_instance_metric_coverage_required"])
        self.assertTrue(result["selective_metric_reporting_forbidden"])
        self.assertTrue(result["optional_gold_metrics_must_be_all_or_none"])
        self.assertTrue(result["all_methods_must_report_each_preregistered_metric"])
        self.assertTrue(result["strictly_positive_measured_resources_required"])
        self.assertTrue(result["nonempty_resource_artifacts_required"])
        self.assertTrue(result["artifact_paths_must_be_bundle_contained"])
        self.assertTrue(result["absolute_parent_escape_and_symlink_paths_forbidden"])
        self.assertTrue(result["prediction_rows_must_match_declared_run_cell"])
        self.assertTrue(result["pooled_or_reused_prediction_artifacts_forbidden"])
        self.assertTrue(result["saved_statistics_must_equal_fresh_recomputation"])
        self.assertTrue(result["statistics_checksum_alone_is_not_acceptance"])

    def test_alias_failure_cannot_be_hidden_by_valid_score(self):
        result = self.run_with(alias_valid=False)
        self.assertFalse(result["valid"])
        self.assertIn("schema_alias_leakage_contract", result["failed_contracts"])
        self.assertTrue(result["checks"]["paired_statistics_contract"]["valid"])

    def test_unregistered_split_cannot_be_hidden_by_valid_score(self):
        result = self.run_with(split_scope_valid=False)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertIn("prediction_eval_split_scope_contract", result["failed_contracts"])
        self.assertTrue(result["checks"]["paired_statistics_contract"]["valid"])

    def test_payload_failure_cannot_be_hidden_by_valid_score(self):
        result = self.run_with(payload_valid=False)
        self.assertFalse(result["valid"])
        self.assertIn("prediction_payload_contract", result["failed_contracts"])

    def test_selective_metric_omission_rejects_otherwise_valid_bundle(self):
        result = self.run_with(metric_coverage_valid=False)
        self.assertFalse(result["valid"])
        self.assertIn("prediction_metric_coverage_contract", result["failed_contracts"])

    def test_zero_placeholder_measurement_rejects_otherwise_valid_bundle(self):
        result = self.run_with(measurements_valid=False)
        self.assertFalse(result["valid"])
        self.assertIn("nonzero_measurement_contract", result["failed_contracts"])

    def test_external_artifact_path_rejects_otherwise_valid_bundle(self):
        result = self.run_with(paths_valid=False)
        self.assertFalse(result["valid"])
        self.assertIn("artifact_path_containment_contract", result["failed_contracts"])

    def test_prediction_cell_mismatch_rejects_otherwise_valid_bundle(self):
        result = self.run_with(cell_binding_valid=False)
        self.assertFalse(result["valid"])
        self.assertIn("prediction_cell_binding_contract", result["failed_contracts"])

    def test_statistics_checksum_failure_rejects_otherwise_valid_bundle(self):
        result = self.run_with(stats_valid=False)
        self.assertFalse(result["valid"])
        self.assertIn("prediction_statistics_evidence_contract", result["failed_contracts"])

    def test_fabricated_checksummed_statistics_reject_otherwise_valid_bundle(self):
        result = self.run_with(recomputation_valid=False)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertIn("statistics_recomputation_binding_contract", result["failed_contracts"])
        self.assertTrue(result["checks"]["prediction_statistics_evidence_contract"]["valid"])
        self.assertTrue(result["checks"]["paired_statistics_contract"]["valid"])

    def test_multiple_failures_are_preserved(self):
        result = self.run_with(alias_valid=False, split_scope_valid=False, payload_valid=False, metric_coverage_valid=False, stats_valid=False, recomputation_valid=False, measurements_valid=False, paths_valid=False, cell_binding_valid=False)
        self.assertEqual(
            result["failed_contracts"],
            [
                "artifact_path_containment_contract",
                "nonzero_measurement_contract",
                "prediction_cell_binding_contract",
                "prediction_eval_split_scope_contract",
                "prediction_metric_coverage_contract",
                "prediction_payload_contract",
                "prediction_statistics_evidence_contract",
                "schema_alias_leakage_contract",
                "statistics_recomputation_binding_contract",
            ],
        )
        self.assertEqual(len(result["errors"]), 9)


if __name__ == "__main__":
    unittest.main()
