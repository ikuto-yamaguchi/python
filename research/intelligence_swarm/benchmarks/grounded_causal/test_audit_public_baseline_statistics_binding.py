#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("baseline_binding", HERE / "audit_public_baseline_statistics_binding.py")
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class PublicBaselineStatisticsBindingTests(unittest.TestCase):
    def bundle(self, root: Path, observed: float = 0.75, pointer: str = "/summary/correct/action"):
        stats = {"summary": {"correct": {"action": 0.75}}}
        path = root / "statistics.json"
        path.write_text(json.dumps(stats), encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {
            "statistics_path": "statistics.json",
            "statistics_sha256": digest,
            "public_baseline": {
                "observed_values": {"action": observed},
                "metric_paths": {"action": pointer},
            },
        }

    def test_exact_statistics_field_binding_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = AUDIT.audit(self.bundle(root), root)
            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(result["metric_checks"]["action"]["resolved_statistics_value"], 0.75)

    def test_claimed_value_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = AUDIT.audit(self.bundle(root, observed=0.9), root)
            self.assertFalse(result["valid"])
            self.assertEqual(result["classification"], "initial_reproduction_failure")

    def test_missing_pointer_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = AUDIT.audit(self.bundle(root, pointer="/summary/correct/missing"), root)
            self.assertFalse(result["valid"])

    def test_metric_key_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.bundle(root)
            manifest["public_baseline"]["metric_paths"] = {"prospective": "/summary/correct/prospective"}
            result = AUDIT.audit(manifest, root)
            self.assertFalse(result["valid"])

    def test_checksum_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.bundle(root)
            manifest["statistics_sha256"] = "0" * 64
            result = AUDIT.audit(manifest, root)
            self.assertFalse(result["valid"])

    def test_parent_escape_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root.parent / "outside-statistics.json"
            outside.write_text('{"summary": {}}', encoding="utf-8")
            try:
                manifest = self.bundle(root)
                manifest["statistics_path"] = "../outside-statistics.json"
                result = AUDIT.audit(manifest, root)
                self.assertFalse(result["valid"])
            finally:
                outside.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
