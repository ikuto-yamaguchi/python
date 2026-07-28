#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("prediction_payload_audit", HERE / "audit_prediction_payload_leakage.py")
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class PredictionPayloadLeakageTests(unittest.TestCase):
    def data(self):
        rows = []
        for seed in (1, 7, 19):
            rows.append({
                "instance_id": f"train-{seed}",
                "seed": seed,
                "split": "train",
                "valid_action_mask": [1, 1, 0],
            })
            for index in range(2):
                rows.append({
                    "instance_id": f"test-{seed}-{index}",
                    "seed": seed,
                    "split": "test",
                    "valid_action_mask": [1, 1, 0],
                })
        return rows

    def predictions(self, data):
        rows = []
        for gold in data:
            if gold["split"] == "train":
                continue
            for method in sorted(AUDIT.REQUIRED_METHODS):
                rows.append({
                    "instance_id": gold["instance_id"],
                    "method": method,
                    "instance_fingerprint": "a" * 64,
                    "pred_action": 1,
                    "pred_state_after": [0, 1],
                })
        return rows

    def test_clean_payload_passes(self):
        data = self.data()
        result = AUDIT.audit_rows(data, self.predictions(data))
        self.assertTrue(result["valid"], result["errors"])

    def test_gold_state_field_is_rejected(self):
        data = self.data(); predictions = self.predictions(data)
        predictions[0]["gold_state_after"] = [0, 1]
        result = AUDIT.audit_rows(data, predictions)
        self.assertFalse(result["valid"])
        self.assertTrue(any("forbidden gold/outcome fields" in error for error in result["errors"]))

    def test_completed_trajectory_is_rejected(self):
        data = self.data(); predictions = self.predictions(data)
        predictions[0]["completed_trajectory"] = [{"reward": 1}]
        result = AUDIT.audit_rows(data, predictions)
        self.assertFalse(result["valid"])
        self.assertTrue(any("completed_trajectory" in error for error in result["errors"]))

    def test_unregistered_debug_payload_is_rejected(self):
        data = self.data(); predictions = self.predictions(data)
        predictions[0]["debug_hidden_state"] = [1, 2, 3]
        result = AUDIT.audit_rows(data, predictions)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unregistered fields" in error for error in result["errors"]))

    def test_invalid_action_is_rejected(self):
        data = self.data(); predictions = self.predictions(data)
        predictions[0]["pred_action"] = 2
        result = AUDIT.audit_rows(data, predictions)
        self.assertFalse(result["valid"])
        self.assertTrue(any("valid-action schema" in error for error in result["errors"]))

    def test_nonfinite_prediction_is_rejected(self):
        data = self.data(); predictions = self.predictions(data)
        predictions[0]["pred_state_after"] = [float("nan")]
        result = AUDIT.audit_rows(data, predictions)
        self.assertFalse(result["valid"])
        self.assertTrue(any("non-finite" in error for error in result["errors"]))

    def test_missing_method_instance_is_rejected(self):
        data = self.data(); predictions = self.predictions(data)
        predictions = [row for row in predictions if not (
            row["method"] == "outcome_shuffle" and row["instance_id"] == "test-19-1"
        )]
        result = AUDIT.audit_rows(data, predictions)
        self.assertFalse(result["valid"])
        self.assertTrue(any("incomplete prediction coverage" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
