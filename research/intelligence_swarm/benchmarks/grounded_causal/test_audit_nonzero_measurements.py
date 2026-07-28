#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from audit_nonzero_measurements import FAILURE, audit


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NonzeroMeasurementAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        for name, payload in (("model.bin", b"model"), ("data.jsonl", b"{}\n"), ("run.log", b"ok\n")):
            (self.base / name).write_bytes(payload)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_row(self) -> dict:
        return {
            "model_bytes": (self.base / "model.bin").stat().st_size,
            "peak_rss_bytes": 1024,
            "training_wall_seconds": 0.25,
            "cpu_inference_ms_per_item": 0.01,
            "model_path": "model.bin",
            "model_sha256": digest(self.base / "model.bin"),
            "data_path": "data.jsonl",
            "data_sha256": digest(self.base / "data.jsonl"),
            "raw_log_path": "run.log",
            "raw_log_sha256": digest(self.base / "run.log"),
        }

    def test_measured_nonempty_bundle_passes(self) -> None:
        result = audit({"runs": [self.run_row()]}, self.base)
        self.assertTrue(result["valid"], result)

    def test_zero_model_bytes_fails(self) -> None:
        row = self.run_row(); row["model_bytes"] = 0
        result = audit({"runs": [row]}, self.base)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], FAILURE)

    def test_zero_peak_rss_fails(self) -> None:
        row = self.run_row(); row["peak_rss_bytes"] = 0
        self.assertFalse(audit({"runs": [row]}, self.base)["valid"])

    def test_zero_training_time_fails(self) -> None:
        row = self.run_row(); row["training_wall_seconds"] = 0.0
        self.assertFalse(audit({"runs": [row]}, self.base)["valid"])

    def test_zero_cpu_latency_fails(self) -> None:
        row = self.run_row(); row["cpu_inference_ms_per_item"] = 0.0
        self.assertFalse(audit({"runs": [row]}, self.base)["valid"])

    def test_empty_artifact_fails_even_with_valid_hash(self) -> None:
        empty = self.base / "run.log"; empty.write_bytes(b"")
        row = self.run_row(); row["raw_log_sha256"] = digest(empty)
        result = audit({"runs": [row]}, self.base)
        self.assertFalse(result["valid"])
        self.assertTrue(any("non-empty" in error for error in result["errors"]))

    def test_model_size_mismatch_fails(self) -> None:
        row = self.run_row(); row["model_bytes"] += 1
        self.assertFalse(audit({"runs": [row]}, self.base)["valid"])


if __name__ == "__main__":
    unittest.main()
