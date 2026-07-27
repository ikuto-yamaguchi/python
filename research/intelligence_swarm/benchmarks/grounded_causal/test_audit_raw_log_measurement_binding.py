#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit_raw_log_measurement_binding.py")
SPEC = importlib.util.spec_from_file_location("audit_raw_log_measurement_binding", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class RawLogMeasurementBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run = {
            "method": "correct",
            "seed": 1,
            "domain": "rtfm",
            "split": "test",
            "condition": "in_distribution",
            "code_commit": "a" * 40,
            "model_bytes": 123,
            "peak_rss_bytes": 456,
            "training_wall_seconds": 7.5,
            "cpu_inference_ms_per_item": 1.25,
            "model_sha256": "b" * 64,
            "data_sha256": "c" * 64,
            "raw_log_path": "run.jsonl",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def write_records(self, records):
        (self.root / "run.jsonl").write_text(
            "\n".join(json.dumps(row) for row in records) + "\n",
            encoding="utf-8",
        )

    def record(self, **updates):
        row = {"record_type": "r0_measurement", **self.run}
        row.pop("raw_log_path")
        row.update(updates)
        return row

    def audit(self, run=None):
        return MODULE.audit({"runs": [run or dict(self.run)]}, self.root)

    def test_exact_machine_readable_record_passes(self):
        self.write_records([{"event": "stdout", "message": "training"}, self.record()])
        result = self.audit()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["findings"][0]["matching_measurement_records"], 1)

    def test_metric_mismatch_fails(self):
        self.write_records([self.record(peak_rss_bytes=999)])
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("peak_rss_bytes mismatch" in error for error in result["errors"]))
        self.assertEqual(result["classification"], "initial_reproduction_failure")

    def test_missing_measurement_record_fails(self):
        self.write_records([{"event": "stdout", "message": "no measurement"}])
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("found 0" in error for error in result["errors"]))

    def test_duplicate_measurement_records_fail(self):
        self.write_records([self.record(), self.record()])
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("found 2" in error for error in result["errors"]))

    def test_wrong_cell_record_fails(self):
        self.write_records([self.record(seed=7)])
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("found 0" in error for error in result["errors"]))

    def test_json_document_with_nested_events_is_supported(self):
        (self.root / "run.jsonl").write_text(
            json.dumps({"events": [{"event": "stdout"}, self.record()]}),
            encoding="utf-8",
        )
        result = self.audit()
        self.assertTrue(result["valid"], result["errors"])

    def test_plain_text_log_fails_closed(self):
        (self.root / "run.jsonl").write_text("training complete\n", encoding="utf-8")
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("raw log must be JSON" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
