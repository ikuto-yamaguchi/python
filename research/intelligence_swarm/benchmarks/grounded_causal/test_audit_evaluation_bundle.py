#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("audit_evaluation_bundle", HERE / "audit_evaluation_bundle.py")
assert SPEC and SPEC.loader
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)
contract = bundle.contract
METHODS = ["correct", "random", "language_blind", "state_only", "target_label_shuffle", "outcome_shuffle"]
COMMIT = "a" * 40


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BundleAuditTests(unittest.TestCase):
    def make_bundle(self, base: Path) -> dict:
        rows = []
        for seed in (1, 7, 19):
            rows.append({
                "instance_id": f"i-{seed}", "domain": "rtfm_s1", "seed": seed,
                "split": "test", "condition": "in_distribution",
                "utterance": [seed], "state_before": [0, seed],
                "gold_action": 1, "gold_state_after": [1, seed],
            })
        data = base / "data.jsonl"
        data.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        raw = base / "raw.log"; raw.write_text("raw", encoding="utf-8")
        model = base / "model.pt"; model.write_bytes(b"model")
        runs = []
        for seed in (1, 7, 19):
            gold = next(row for row in rows if row["seed"] == seed)
            for method in METHODS:
                pred = base / f"pred-{method}-{seed}.jsonl"
                pred.write_text(json.dumps({
                    "instance_id": gold["instance_id"], "method": method,
                    "instance_fingerprint": contract.instance_fingerprint(gold),
                    "pred_action": 1, "pred_state_after": gold["gold_state_after"],
                }) + "\n", encoding="utf-8")
                runs.append({
                    "method": method, "seed": seed, "domain": "rtfm_s1",
                    "split": "test", "condition": "in_distribution",
                    "model_bytes": model.stat().st_size, "peak_rss_bytes": 100,
                    "training_wall_seconds": 1.0, "cpu_inference_ms_per_item": 0.1,
                    "raw_log_path": raw.name, "raw_log_sha256": sha(raw),
                    "model_path": model.name, "model_sha256": sha(model),
                    "data_path": data.name, "data_sha256": sha(data),
                    "prediction_path": pred.name, "prediction_sha256": sha(pred),
                    "code_commit": COMMIT,
                })
        return {"runs": runs}

    def test_valid_exact_join(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            result = bundle.audit_bundle(self.make_bundle(base), base)
            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(result["prediction_rows_read"], 18)
            self.assertTrue(result["exact_prediction_dataset_join_required"])

    def test_missing_prediction_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); manifest = self.make_bundle(base)
            manifest["runs"][0].pop("prediction_path")
            result = bundle.audit_bundle(manifest, base)
            self.assertFalse(result["valid"])
            self.assertTrue(any("prediction_path is required" in error for error in result["errors"]))
            self.assertEqual(result["classification"], "initial_reproduction_failure")

    def test_prediction_instance_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); manifest = self.make_bundle(base)
            run = manifest["runs"][0]
            path = base / run["prediction_path"]
            row = json.loads(path.read_text(encoding="utf-8"))
            row["instance_id"] = "wrong-instance"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            run["prediction_sha256"] = sha(path)
            result = bundle.audit_bundle(manifest, base)
            self.assertFalse(result["valid"])
            self.assertTrue(any("prediction/data join mismatch" in error for error in result["errors"]))

    def test_model_identity_cannot_change_by_condition(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); manifest = self.make_bundle(base)
            clone = []
            for run in manifest["runs"]:
                copied = dict(run)
                copied["condition"] = "entity_holdout"
                clone.append(copied)
            manifest["runs"].extend(clone)
            other = base / "other.pt"; other.write_bytes(b"other-model")
            target = next(run for run in manifest["runs"] if run["condition"] == "entity_holdout" and run["method"] == "correct")
            target["model_path"] = other.name
            target["model_sha256"] = sha(other)
            target["model_bytes"] = other.stat().st_size
            result = bundle.audit_bundle(manifest, base)
            self.assertFalse(result["valid"])
            self.assertTrue(any("model or code identity changed" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
