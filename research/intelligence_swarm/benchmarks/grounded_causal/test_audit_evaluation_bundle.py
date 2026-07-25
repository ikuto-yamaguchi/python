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
                "instance_id": f"train-{seed}", "domain": "rtfm_s1", "seed": seed,
                "split": "train", "condition": "in_distribution",
                "utterance": [900, seed], "state_before": [0, seed],
                "gold_action": 1, "gold_state_after": [1, seed],
                "entity_signature": f"train-e-{seed}",
                "dynamics_signature": f"train-d-{seed}",
            })
            for item in (0, 1):
                rows.append({
                    "instance_id": f"i-{seed}-{item}", "domain": "rtfm_s1", "seed": seed,
                    "split": "test", "condition": "in_distribution",
                    "utterance": [seed, item], "state_before": [0, seed, item],
                    "gold_action": item, "gold_state_after": [1, seed, item],
                    "entity_signature": f"test-e-{seed}-{item}",
                    "dynamics_signature": f"test-d-{seed}-{item}",
                })
        data = base / "data.jsonl"
        data.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        raw = base / "raw.log"; raw.write_text("raw", encoding="utf-8")
        model = base / "model.pt"; model.write_bytes(b"model")
        runs = []
        for seed in (1, 7, 19):
            eval_rows = [row for row in rows if row["seed"] == seed and row["split"] == "test"]
            donor = {
                eval_rows[0]["instance_id"]: eval_rows[1],
                eval_rows[1]["instance_id"]: eval_rows[0],
            }
            for method in METHODS:
                pred = base / f"pred-{method}-{seed}.jsonl"
                prediction_rows = []
                for gold in eval_rows:
                    row = {
                        "instance_id": gold["instance_id"], "method": method,
                        "instance_fingerprint": contract.instance_fingerprint(gold),
                        "pred_action": gold["gold_action"],
                        "pred_state_after": gold["gold_state_after"],
                    }
                    if method in contract.SHUFFLE_METHODS:
                        source = donor[gold["instance_id"]]
                        row["control_source_instance_id"] = source["instance_id"]
                        row["control_source_fingerprint"] = contract.instance_fingerprint(source)
                    prediction_rows.append(row)
                pred.write_text(
                    "".join(json.dumps(row) + "\n" for row in prediction_rows),
                    encoding="utf-8",
                )
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

    def test_valid_exact_join_runs_complete_contract(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            result = bundle.audit_bundle(self.make_bundle(base), base)
            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(result["prediction_rows_read"], 36)
            self.assertTrue(result["exact_prediction_dataset_join_required"])
            self.assertTrue(result["full_dataset_contract_executed"])
            self.assertTrue(result["semantic_alias_value_leakage_executed"])
            self.assertTrue(result["paired_statistics_executed"])
            self.assertTrue(result["dataset_audit"]["valid"])
            self.assertTrue(result["prediction_statistics"]["valid"])

    def test_semantic_alias_leakage_fails_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); manifest = self.make_bundle(base)
            data = base / manifest["runs"][0]["data_path"]
            rows = [json.loads(line) for line in data.read_text(encoding="utf-8").splitlines()]
            target = next(row for row in rows if row["split"] == "test")
            target["model_input"] = {"future_state": target["gold_state_after"]}
            data.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            for run in manifest["runs"]:
                run["data_sha256"] = sha(data)
            result = bundle.audit_bundle(manifest, base)
            self.assertFalse(result["valid"])
            self.assertTrue(any("semantic_leakage" in error for error in result["errors"]))
            self.assertEqual(result["classification"], "initial_reproduction_failure")

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
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            rows[0]["instance_id"] = "wrong-instance"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
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
