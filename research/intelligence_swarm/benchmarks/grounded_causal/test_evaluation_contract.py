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
ec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ec)

METHODS = ["correct", "random", "language_blind", "state_only", "target_label_shuffle", "outcome_shuffle"]


class ContractTests(unittest.TestCase):
    def make_rows(self):
        rows = []
        for seed in (1, 7, 19):
            rows.append({
                "instance_id": f"train-{seed}", "domain": "rtfm_s1", "seed": seed,
                "split": "train", "utterance": f"train text {seed}",
                "state_before": [0, seed], "state_after": [1, seed],
                "action": 1, "reward": 0.0, "done": False,
            })
            for condition in ("entity_holdout", "dynamics_holdout", "language_holdout"):
                rows.append({
                    "instance_id": f"test-{seed}-{condition}",
                    "domain": "rtfm_s1", "seed": seed, "split": "test",
                    "utterance": f"test text {seed} {condition}",
                    "state_before": [0, seed], "state_after": [1, seed],
                    "action": 1, "reward": 1.0, "done": True,
                    "entity_holdout": condition == "entity_holdout",
                    "dynamics_holdout": condition == "dynamics_holdout",
                    "language_holdout": condition == "language_holdout",
                    "entity_signature": f"eval-e-{seed}-{condition}",
                    "dynamics_signature": f"eval-d-{seed}-{condition}",
                })
        return rows

    def make_predictions(self, rows):
        preds = []
        for row in rows:
            if row["split"] == "train":
                continue
            for method in METHODS:
                correct = method == "correct"
                preds.append({
                    "instance_id": row["instance_id"], "method": method,
                    "pred_action": row["action"] if correct else 0,
                    "pred_state_after": row["state_after"] if correct else row["state_before"],
                })
        return preds

    def test_silg_export_schema_adapts_and_scores(self):
        rows = self.make_rows()
        report = ec.validate_dataset(rows)
        self.assertTrue(report["valid"], report)
        scored = ec.score(rows, self.make_predictions(rows))
        self.assertTrue(scored["valid"], scored)
        self.assertEqual(scored["coverage"]["correct"]["coverage"], 1.0)
        self.assertGreaterEqual(
            scored["paired_gaps_vs_correct"]["state_only"]["action"]["mean_gap"], 0.10
        )

    def test_gold_and_completed_trajectory_leakage_rejected(self):
        rows = self.make_rows()
        rows[0]["model_input_fields"] = ["utterance", "state_before", "action"]
        rows[1]["model_input"] = {"history": [], "completed_trajectory": [1, 2]}
        report = ec.validate_dataset(rows)
        self.assertFalse(report["valid"])
        self.assertGreaterEqual(report["leakage_rows"], 2)

    def test_exact_train_test_overlap_rejected(self):
        rows = self.make_rows()
        rows[3]["utterance"] = rows[0]["utterance"]
        report = ec.validate_dataset(rows)
        self.assertFalse(report["valid"])
        self.assertTrue(any("utterance leakage" in e for e in report["errors"]))

    def test_incomplete_prediction_coverage_rejected(self):
        rows = self.make_rows()
        preds = self.make_predictions(rows)
        preds = [p for p in preds if not (
            p["method"] == "state_only" and p["instance_id"].endswith("language_holdout")
        )]
        scored = ec.score(rows, preds)
        self.assertFalse(scored["valid"])
        self.assertLess(scored["coverage"]["state_only"]["coverage"], 1.0)

    def test_artifact_checksum_and_resource_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            raw = base / "run.log"
            model = base / "model.bin"
            data = base / "data.jsonl"
            raw.write_text("ok\n", encoding="utf-8")
            model.write_bytes(b"model")
            data.write_text("{}\n", encoding="utf-8")
            sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            runs = []
            for seed in (1, 7, 19):
                for method in METHODS:
                    runs.append({
                        "method": method, "seed": seed, "domain": "rtfm_s1", "split": "test",
                        "model_bytes": model.stat().st_size, "peak_rss_bytes": 1024,
                        "training_wall_seconds": 1.0, "cpu_inference_ms_per_item": 0.1,
                        "raw_log_path": raw.name, "raw_log_sha256": sha(raw),
                        "model_path": model.name, "model_sha256": sha(model),
                        "data_path": data.name, "data_sha256": sha(data),
                        "code_commit": "deadbeef",
                    })
            report = ec.audit_artifacts({"runs": runs}, base)
            self.assertTrue(report["valid"], report)
            self.assertEqual(report["classification"], "reproduced")


if __name__ == "__main__":
    unittest.main()
