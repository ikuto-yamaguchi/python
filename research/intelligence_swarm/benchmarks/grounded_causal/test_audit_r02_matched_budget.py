#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit_r02_matched_budget import audit


def base_payload() -> dict:
    evaluations = []
    for method in ("environment_first", "end_to_end", "state_only"):
        evaluations.append(
            {
                "method": method,
                "conditions": {
                    "all": {
                        "n": 6,
                        "action_accuracy": 0.5,
                        "typed_next_state_loss": 1.0,
                        "task_success": None,
                        "task_success_status": "not_available_offline",
                    }
                },
                "cpu_inference_ms_per_instance_mean": 0.2,
            }
        )
    return {
        "seed": 1,
        "config": {"env_epochs": 8, "lang_epochs": 8},
        "dataset": {
            "sha256": "a" * 64,
            "n_train": 40,
            "n_test": 6,
            "splits": ["train", "test"],
        },
        "parameter_budget": {
            "environment_first_inference_bytes": 1000,
            "end_to_end_inference_bytes": 1000,
            "environment_pretraining_only_bytes": 500,
            "state_only_inference_bytes": 800,
            "equal": True,
        },
        "training": {
            "environment_pretraining_seconds": 1.0,
            "environment_first_language_seconds": 1.0,
            "end_to_end_seconds": 2.0,
            "state_only_seconds": 2.0,
            "peak_rss_kib": 100000,
        },
        "evaluations": evaluations,
        "checkpoints": {
            method: {"bytes": 100, "sha256": str(index) * 64, "path": f"{method}.pt"}
            for index, method in enumerate(("environment_first", "end_to_end", "state_only"), 1)
        },
    }


class MatchedBudgetAuditTest(unittest.TestCase):
    def write_payload(self, payload: dict) -> Path:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(payload, tmp)
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink, missing_ok=True)
        return Path(tmp.name)

    def test_matched_offline_bundle_passes_and_records_equal_exposure(self) -> None:
        report = audit(self.write_payload(base_payload()))
        self.assertTrue(report["passed"])
        self.assertEqual(
            report["classification"],
            "matched_offline_budget_audit_passed_online_task_success_pending",
        )
        self.assertEqual(set(report["training_row_exposures"].values()), {640})

    def test_parameter_mismatch_fails(self) -> None:
        payload = base_payload()
        payload["parameter_budget"]["end_to_end_inference_bytes"] = 999
        report = audit(self.write_payload(payload))
        self.assertFalse(report["passed"])
        self.assertIn("inference parameter bytes mismatch", report["failures"])

    def test_prediction_coverage_mismatch_fails(self) -> None:
        payload = base_payload()
        payload["evaluations"][0]["conditions"]["all"]["n"] = 5
        report = audit(self.write_payload(payload))
        self.assertFalse(report["passed"])
        self.assertTrue(any("prediction coverage" in item for item in report["failures"]))

    def test_noncanonical_seed_fails(self) -> None:
        payload = base_payload()
        payload["seed"] = 2
        report = audit(self.write_payload(payload))
        self.assertFalse(report["passed"])
        self.assertIn("non-canonical seed: 2", report["failures"])


if __name__ == "__main__":
    unittest.main()
