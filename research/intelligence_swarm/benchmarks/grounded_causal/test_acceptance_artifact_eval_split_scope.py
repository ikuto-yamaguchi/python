#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("r0_acceptance_artifact_split", HERE / "audit_r0_acceptance_bundle.py")
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class ArtifactEvalSplitAcceptanceTests(unittest.TestCase):
    def run_gate(self, artifact_split_valid: bool):
        valid_result = {"valid": True, "errors": []}
        patches = [
            mock.patch.object(AUDIT.evaluation_contract, "validate_dataset", return_value=valid_result),
            mock.patch.object(AUDIT.schema_alias, "audit", return_value=valid_result),
            mock.patch.object(AUDIT.explicit_holdout_condition, "audit", return_value=valid_result),
            mock.patch.object(AUDIT.prediction_eval_split_scope, "audit", return_value=valid_result),
            mock.patch.object(AUDIT.prediction_payload, "audit_rows", return_value=valid_result),
            mock.patch.object(AUDIT.prediction_metric_coverage, "audit", return_value=valid_result),
            mock.patch.object(AUDIT.evaluation_contract, "score", return_value=valid_result),
            mock.patch.object(AUDIT.evaluation_contract, "audit_artifacts", return_value=valid_result),
            mock.patch.object(
                AUDIT.artifact_eval_split_scope,
                "audit",
                return_value={
                    "valid": artifact_split_valid,
                    "errors": [] if artifact_split_valid else ["run 1: artifact run split='train' is not a registered evaluation split"],
                },
            ),
            mock.patch.object(AUDIT.nonzero_measurements, "audit", return_value=valid_result),
            mock.patch.object(AUDIT.artifact_path_containment, "audit", return_value=valid_result),
            mock.patch.object(AUDIT.prediction_cell_binding, "audit", return_value=valid_result),
            mock.patch.object(AUDIT.prediction_statistics, "audit", return_value=valid_result),
            mock.patch.object(AUDIT.statistics_recomputation, "audit", return_value=valid_result),
            mock.patch.object(AUDIT.public_baseline_reproduction, "audit", return_value=valid_result),
            mock.patch.object(AUDIT.public_baseline_statistics_binding, "audit", return_value=valid_result),
        ]
        with ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            return AUDIT.audit_acceptance(
                [{"instance_id": "x"}],
                [{"instance_id": "x"}],
                {"runs": [{"split": "train"}]},
                HERE,
            )

    def test_registered_resource_split_is_required_for_acceptance(self):
        result = self.run_gate(True)
        self.assertTrue(result["valid"], result["errors"])
        self.assertTrue(result["resource_runs_must_use_registered_evaluation_splits"])
        self.assertTrue(result["train_resource_cells_forbidden"])
        self.assertTrue(result["unregistered_resource_cells_forbidden"])

    def test_train_resource_cell_rejects_otherwise_valid_bundle(self):
        result = self.run_gate(False)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertIn("artifact_eval_split_scope_contract", result["failed_contracts"])
        self.assertTrue(result["checks"]["resource_artifact_contract"]["valid"])
        self.assertTrue(result["checks"]["paired_statistics_contract"]["valid"])


if __name__ == "__main__":
    unittest.main()
