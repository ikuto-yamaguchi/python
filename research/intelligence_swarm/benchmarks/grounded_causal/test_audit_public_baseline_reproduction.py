#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

import audit_public_baseline_reproduction as target


SHA40 = "1" * 40
SHA64 = "2" * 64


def valid_manifest() -> dict:
    return {
        "statistics_sha256": SHA64,
        "public_baseline": {
            "name": "published-r0-baseline",
            "source_url": "https://example.org/official-baseline",
            "source_commit": SHA40,
            "source_version": "v1.0.0",
            "statistics_sha256": SHA64,
            "expected_values": {
                "action_accuracy": 0.72,
                "prospective_accuracy": 0.61,
            },
            "observed_values": {
                "action_accuracy": 0.719,
                "prospective_accuracy": 0.612,
            },
            "absolute_tolerances": {
                "action_accuracy": 0.005,
                "prospective_accuracy": 0.005,
            },
        },
    }


class PublicBaselineAuditTests(unittest.TestCase):
    def test_complete_reproduction_claim_passes(self) -> None:
        result = target.audit(valid_manifest())
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["classification"], "reproduced")

    def test_missing_baseline_object_fails(self) -> None:
        result = target.audit({"statistics_sha256": SHA64})
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")

    def test_upstream_commit_must_be_full_sha(self) -> None:
        manifest = valid_manifest()
        manifest["public_baseline"]["source_commit"] = "main"
        result = target.audit(manifest)
        self.assertFalse(result["valid"])
        self.assertTrue(any("40-hex" in error for error in result["errors"]))

    def test_statistics_checksum_must_bind_observations(self) -> None:
        manifest = valid_manifest()
        manifest["public_baseline"]["statistics_sha256"] = "3" * 64
        result = target.audit(manifest)
        self.assertFalse(result["valid"])
        self.assertTrue(any("not bound" in error for error in result["errors"]))

    def test_metric_key_sets_must_match(self) -> None:
        manifest = valid_manifest()
        del manifest["public_baseline"]["observed_values"]["action_accuracy"]
        result = target.audit(manifest)
        self.assertFalse(result["valid"])
        self.assertTrue(any("metric keys differ" in error for error in result["errors"]))

    def test_outside_tolerance_fails(self) -> None:
        manifest = valid_manifest()
        manifest["public_baseline"]["observed_values"]["action_accuracy"] = 0.68
        result = target.audit(manifest)
        self.assertFalse(result["valid"])
        self.assertFalse(result["metric_checks"]["action_accuracy"]["within_tolerance"])

    def test_nonfinite_value_fails(self) -> None:
        manifest = copy.deepcopy(valid_manifest())
        manifest["public_baseline"]["observed_values"]["action_accuracy"] = float("nan")
        result = target.audit(manifest)
        self.assertFalse(result["valid"])
        self.assertTrue(any("finite numeric" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
