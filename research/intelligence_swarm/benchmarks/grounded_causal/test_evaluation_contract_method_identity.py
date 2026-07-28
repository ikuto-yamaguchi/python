#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("evaluation_contract", HERE / "evaluation_contract.py")
assert SPEC and SPEC.loader
EC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EC)
METHODS = sorted(EC.REQUIRED_METHODS)
COMMIT = "a" * 40


class MethodAndIdentityTests(unittest.TestCase):
    def rows(self):
        rows = []
        for seed in sorted(EC.CANONICAL_SEEDS):
            rows.append({"instance_id": f"train-{seed}", "domain": "rtfm_s1", "seed": seed, "split": "train", "condition": "in_distribution", "utterance": f"train {seed}", "state_before": [0, seed], "gold_action": 1, "gold_state_after": [1, seed]})
            for index in range(2):
                rows.append({"instance_id": f"test-{seed}-{index}", "domain": "rtfm_s1", "seed": seed, "split": "test", "condition": "dynamics_holdout", "utterance": f"test {seed} {index}", "state_before": [0, seed, index], "gold_action": 1, "gold_state_after": [1, seed, index]})
        return rows

    def predictions(self, rows):
        eval_rows = [row for row in rows if row["split"] != "train"]
        by_seed = {seed: [row for row in eval_rows if row["seed"] == seed] for seed in EC.CANONICAL_SEEDS}
        predictions = []
        for row in eval_rows:
            donor = by_seed[row["seed"]][1 - int(row["instance_id"].rsplit("-", 1)[1])]
            fingerprint = EC.instance_fingerprint(EC.adapt_row(row))
            for method in METHODS:
                pred = {"instance_id": row["instance_id"], "method": method, "instance_fingerprint": fingerprint, "pred_action": 1 if method == "correct" else 0, "pred_state_after": row["gold_state_after"] if method == "correct" else row["state_before"]}
                if method in EC.SHUFFLE_METHODS:
                    pred["control_source_instance_id"] = donor["instance_id"]
                    pred["control_source_fingerprint"] = EC.instance_fingerprint(EC.adapt_row(donor))
                predictions.append(pred)
        return predictions

    def manifest(self, base):
        raw = base / "raw.log"; raw.write_text("raw", encoding="utf-8")
        model = base / "model.pt"; model.write_bytes(b"model")
        data = base / "data.jsonl"; data.write_text("data", encoding="utf-8")
        sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        runs = []
        for seed in sorted(EC.CANONICAL_SEEDS):
            for method in METHODS:
                runs.append({"method": method, "seed": seed, "domain": "rtfm_s1", "split": "test", "condition": "dynamics_holdout", "model_bytes": model.stat().st_size, "peak_rss_bytes": 100, "training_wall_seconds": 1.0, "cpu_inference_ms_per_item": 0.1, "raw_log_path": raw.name, "raw_log_sha256": sha(raw), "model_path": model.name, "model_sha256": sha(model), "data_path": data.name, "data_sha256": sha(data), "code_commit": COMMIT})
        return {"runs": runs}

    def test_score_rejects_unregistered_method(self):
        rows = self.rows(); predictions = self.predictions(rows)
        extra = dict(predictions[0]); extra["method"] = "representation_probe"; predictions.append(extra)
        result = EC.score(rows, predictions)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unexpected prediction methods" in error for error in result["errors"]))

    def test_artifacts_reject_unregistered_method(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); manifest = self.manifest(base)
            extra = dict(manifest["runs"][0]); extra["method"] = "representation_probe"; manifest["runs"].append(extra)
            result = EC.audit_artifacts(manifest, base)
            self.assertFalse(result["valid"])
            self.assertTrue(any("unexpected methods" in error for error in result["errors"]))

    def test_artifacts_reject_mixed_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); manifest = self.manifest(base); manifest["runs"][0]["code_commit"] = "b" * 40
            result = EC.audit_artifacts(manifest, base)
            self.assertFalse(result["valid"])
            self.assertTrue(any("exactly one code_commit" in error for error in result["errors"]))

    def test_artifacts_reject_dataset_identity_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); manifest = self.manifest(base)
            other = base / "other.jsonl"; other.write_text("other", encoding="utf-8")
            manifest["runs"][0]["data_path"] = other.name
            manifest["runs"][0]["data_sha256"] = hashlib.sha256(other.read_bytes()).hexdigest()
            result = EC.audit_artifacts(manifest, base)
            self.assertFalse(result["valid"])
            self.assertTrue(any("share one data_path/data_sha256" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
