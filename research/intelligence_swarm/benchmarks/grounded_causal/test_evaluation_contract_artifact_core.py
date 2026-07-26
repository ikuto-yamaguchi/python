#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("evaluation_contract.py")
SPEC = importlib.util.spec_from_file_location("evaluation_contract", MODULE_PATH)
assert SPEC and SPEC.loader
EC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EC)

METHODS = {
    "correct",
    "random",
    "language_blind",
    "state_only",
    "target_label_shuffle",
    "outcome_shuffle",
}
SEEDS = {1, 7, 19}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EvaluationContractArtifactCoreTest(unittest.TestCase):
    def make_bundle(self, root: Path) -> dict:
        model = root / "model.bin"
        data = root / "data.jsonl"
        log = root / "train.log"
        model.write_bytes(b"model-bytes")
        data.write_text('{"row":1}\n', encoding="utf-8")
        log.write_text("completed\n", encoding="utf-8")
        runs = []
        for method in sorted(METHODS):
            for seed in sorted(SEEDS):
                runs.append(
                    {
                        "method": method,
                        "seed": seed,
                        "domain": "rtfm",
                        "split": "test",
                        "condition": "in_distribution",
                        "model_bytes": model.stat().st_size,
                        "peak_rss_bytes": 1024,
                        "training_wall_seconds": 1.25,
                        "cpu_inference_ms_per_item": 0.5,
                        "raw_log_path": log.name,
                        "raw_log_sha256": sha256(log),
                        "model_path": model.name,
                        "model_sha256": sha256(model),
                        "data_path": data.name,
                        "data_sha256": sha256(data),
                        "code_commit": "a" * 40,
                    }
                )
        return {"runs": runs}

    def test_valid_self_contained_positive_bundle_passes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = EC.audit_artifacts(self.make_bundle(root), root)
            self.assertTrue(result["valid"], result["errors"])
            self.assertTrue(result["positive_resource_measurements_required"])
            self.assertTrue(result["artifact_path_containment_required"])
            self.assertTrue(result["nonempty_artifacts_required"])

    def test_zero_measurement_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self.make_bundle(root)
            manifest["runs"][0]["peak_rss_bytes"] = 0
            result = EC.audit_artifacts(manifest, root)
            self.assertFalse(result["valid"])
            self.assertEqual(result["classification"], "initial_reproduction_failure")
            self.assertTrue(any("peak_rss_bytes must be a finite positive number" in e for e in result["errors"]))

    def test_absolute_artifact_path_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self.make_bundle(root)
            manifest["runs"][0]["raw_log_path"] = str(root / "train.log")
            result = EC.audit_artifacts(manifest, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("non-empty relative path" in e for e in result["errors"]))

    def test_parent_traversal_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
            root = Path(td)
            external = Path(outside) / "outside.log"
            external.write_text("external\n", encoding="utf-8")
            manifest = self.make_bundle(root)
            manifest["runs"][0]["raw_log_path"] = "../outside.log"
            manifest["runs"][0]["raw_log_sha256"] = sha256(external)
            result = EC.audit_artifacts(manifest, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("parent traversal" in e for e in result["errors"]))

    def test_empty_artifact_fails_even_with_correct_hash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self.make_bundle(root)
            empty = root / "empty.log"
            empty.write_bytes(b"")
            manifest["runs"][0]["raw_log_path"] = empty.name
            manifest["runs"][0]["raw_log_sha256"] = sha256(empty)
            result = EC.audit_artifacts(manifest, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("artifact must be non-empty" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
