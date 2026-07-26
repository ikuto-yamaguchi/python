#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from qualify_r01_source_policy import (
    EXPECTED_METHODS,
    EXPECTED_RTFM,
    EXPECTED_SEEDS,
    EXPECTED_SILG,
    classify_failures,
)

SHA = "a" * 64


def valid_training() -> dict:
    runs = []
    for seed in EXPECTED_SEEDS:
        runs.append(
            {
                "seed": seed,
                "completed": True,
                "wall_seconds": 100.0,
                "log_sha256": SHA,
                "resource": {"peak_rss_kib": 500000, "exit_status": 0},
                "checkpoint": {
                    "frames_in_checkpoint": 131072,
                    "official_checkpoint_bytes": 1000,
                    "official_checkpoint_sha256": SHA,
                    "model_state_bytes": 900,
                    "model_state_sha256": SHA,
                },
            }
        )
    return {
        "status": "success",
        "source_pins": {"silg": EXPECTED_SILG, "rtfm": EXPECTED_RTFM},
        "seeds": list(EXPECTED_SEEDS),
        "frames_per_seed": 131072,
        "model_audit": {
            "completed": True,
            "parameters": 4916915,
            "trainable_parameters": 4916915,
            "state_dict_bytes": 20000000,
            "state_dict_sha256": SHA,
            "cpu_forward_latency_ms_per_step": 7.0,
        },
        "runs": runs,
    }


def valid_matched() -> dict:
    aggregate = {
        method: {"win_rate": 0.0, "return_mean": 0.0}
        for method in EXPECTED_METHODS
    }
    aggregate["correct"] = {"win_rate": 0.2, "return_mean": 0.5}
    aggregate["random"] = {"win_rate": 0.05, "return_mean": 0.1}
    return {
        "status": "success",
        "seeds": list(EXPECTED_SEEDS),
        "methods": sorted(EXPECTED_METHODS),
        "all_initial_streams_match": True,
        "answer_leakage": False,
        "aggregate": aggregate,
    }


class QualificationResourceAuditTests(unittest.TestCase):
    def test_complete_bundle_qualifies(self) -> None:
        failures, classification, _ = classify_failures(valid_training(), valid_matched())
        self.assertEqual([], failures)
        self.assertEqual("qualified", classification)

    def test_checkpoint_frame_count_must_equal_requested_budget(self) -> None:
        training = valid_training()
        training["runs"][0]["checkpoint"]["frames_in_checkpoint"] = 131073
        failures, classification, _ = classify_failures(training, valid_matched())
        self.assertIn("checkpoint_frame_budget_mismatch_seed_1", failures)
        self.assertEqual("implementation_or_artifact_failure", classification)

    def test_missing_peak_rss_is_rejected(self) -> None:
        training = valid_training()
        del training["runs"][1]["resource"]["peak_rss_kib"]
        failures, classification, _ = classify_failures(training, valid_matched())
        self.assertIn("missing_peak_rss_seed_7", failures)
        self.assertEqual("implementation_or_artifact_failure", classification)

    def test_missing_cpu_latency_is_rejected(self) -> None:
        training = valid_training()
        del training["model_audit"]["cpu_forward_latency_ms_per_step"]
        failures, _, _ = classify_failures(training, valid_matched())
        self.assertIn("invalid_model_audit_cpu_forward_latency_ms_per_step", failures)

    def test_invalid_checkpoint_checksum_is_rejected(self) -> None:
        training = valid_training()
        training["runs"][2]["checkpoint"]["model_state_sha256"] = "not-a-sha"
        failures, _, _ = classify_failures(training, valid_matched())
        self.assertIn("invalid_checkpoint_model_state_sha256_seed_19", failures)

    def test_extra_or_reordered_run_seed_topology_is_rejected(self) -> None:
        training = valid_training()
        training["runs"] = [training["runs"][1], training["runs"][0], training["runs"][2]]
        failures, _, _ = classify_failures(training, valid_matched())
        self.assertIn("training_run_seed_topology_mismatch", failures)

    def test_policy_failure_remains_distinct_from_artifact_failure(self) -> None:
        matched = copy.deepcopy(valid_matched())
        matched["aggregate"]["correct"] = {"win_rate": 0.0, "return_mean": 0.0}
        failures, classification, _ = classify_failures(valid_training(), matched)
        self.assertIn("zero_source_policy_success", failures)
        self.assertEqual("optimization_or_policy_competence_failure", classification)


if __name__ == "__main__":
    unittest.main()
