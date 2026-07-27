#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("evaluation_contract", HERE / "evaluation_contract.py")
assert SPEC and SPEC.loader
EC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EC)

METHODS = sorted(EC.REQUIRED_METHODS)
SEEDS = sorted(EC.CANONICAL_SEEDS)
COMMIT = "a" * 40


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_bundle(root: Path) -> dict:
    data = root / "data.jsonl"
    data.write_text('{"instance_id":"x"}\n', encoding="utf-8")
    runs = []
    for seed in SEEDS:
        for method in METHODS:
            stem = f"{method}-{seed}"
            model = root / f"{stem}.bin"
            model.write_bytes((stem + "-model").encode())
            log = root / f"{stem}.json"
            run = {
                "method": method,
                "seed": seed,
                "domain": "rtfm",
                "split": "test",
                "condition": "in_distribution",
                "code_commit": COMMIT,
                "model_bytes": model.stat().st_size,
                "peak_rss_bytes": 1024 + seed,
                "training_wall_seconds": 1.5 + seed,
                "cpu_inference_ms_per_item": 0.5 + seed,
                "model_path": model.name,
                "model_sha256": sha(model),
                "data_path": data.name,
                "data_sha256": sha(data),
                "raw_log_path": log.name,
            }
            record = {"record_type": "r0_measurement", **{k: run[k] for k in (
                "method", "seed", "domain", "split", "condition", "code_commit",
                "model_bytes", "peak_rss_bytes", "training_wall_seconds",
                "cpu_inference_ms_per_item", "model_sha256", "data_sha256",
            )}}
            log.write_text(json.dumps({"events": [record]}, sort_keys=True), encoding="utf-8")
            run["raw_log_sha256"] = sha(log)
            runs.append(run)
    return {"runs": runs}


class CoreRawLogBindingTests(unittest.TestCase):
    def test_valid_bundle_binds_every_run(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = EC.audit_artifacts(build_bundle(root), root)
            self.assertTrue(result["valid"], result["errors"])
            self.assertTrue(result["raw_log_measurement_binding_required"])
            self.assertEqual(len(result["raw_log_measurement_findings"]), len(METHODS) * len(SEEDS))
            self.assertTrue(all(x["matching_measurement_records"] == 1 for x in result["raw_log_measurement_findings"]))

    def test_manifest_measurement_tampering_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = build_bundle(root)
            manifest["runs"][0]["peak_rss_bytes"] += 1
            result = EC.audit_artifacts(manifest, root)
            self.assertFalse(result["valid"])
            self.assertEqual(result["classification"], "initial_reproduction_failure")
            self.assertTrue(any("raw-log peak_rss_bytes mismatch" in e for e in result["errors"]))

    def test_missing_machine_readable_record_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = build_bundle(root)
            run = manifest["runs"][0]
            log = root / run["raw_log_path"]
            log.write_text(json.dumps({"message": "training complete"}), encoding="utf-8")
            run["raw_log_sha256"] = sha(log)
            result = EC.audit_artifacts(manifest, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("expected exactly one raw-log measurement record" in e for e in result["errors"]))

    def test_duplicate_cell_records_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = build_bundle(root)
            run = manifest["runs"][0]
            log = root / run["raw_log_path"]
            payload = json.loads(log.read_text(encoding="utf-8"))
            payload["events"].append(dict(payload["events"][0]))
            log.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
            run["raw_log_sha256"] = sha(log)
            result = EC.audit_artifacts(manifest, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("found 2" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
