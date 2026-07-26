#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("cell_binding", HERE / "audit_prediction_cell_binding.py")
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)

METHODS = [
    "correct",
    "random",
    "language_blind",
    "state_only",
    "target_label_shuffle",
    "outcome_shuffle",
]
SEEDS = [1, 7, 19]


class PredictionCellBindingTests(unittest.TestCase):
    def make_bundle(self, root: Path):
        runs = []
        for method in METHODS:
            for seed in SEEDS:
                rel = f"predictions/{method}-{seed}.jsonl"
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                row = {
                    "instance_id": f"{method}-{seed}-x",
                    "method": method,
                    "seed": seed,
                    "domain": "rtfm",
                    "split": "test",
                    "condition": "dynamics_holdout",
                }
                path.write_text(json.dumps(row) + "\n", encoding="utf-8")
                runs.append({
                    "method": method,
                    "seed": seed,
                    "domain": "rtfm",
                    "split": "test",
                    "condition": "dynamics_holdout",
                    "predictions_path": rel,
                })
        return {"runs": runs}

    def test_exact_cell_bound_artifacts_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = AUDIT.audit(self.make_bundle(root), root)
            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(result["declared_cells"], 18)
            self.assertEqual(result["prediction_artifacts"], 18)

    def test_row_with_wrong_seed_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.make_bundle(root)
            run = manifest["runs"][0]
            path = root / run["predictions_path"]
            row = json.loads(path.read_text(encoding="utf-8"))
            row["seed"] = 7
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            result = AUDIT.audit(manifest, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("does not match declared cell" in error for error in result["errors"]))

    def test_pooled_rows_from_multiple_cells_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.make_bundle(root)
            run = manifest["runs"][0]
            path = root / run["predictions_path"]
            first = json.loads(path.read_text(encoding="utf-8"))
            second = dict(first)
            second["seed"] = 7
            path.write_text(json.dumps(first) + "\n" + json.dumps(second) + "\n", encoding="utf-8")
            result = AUDIT.audit(manifest, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("exactly declared cell" in error for error in result["errors"]))

    def test_same_artifact_reused_for_two_declared_cells_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.make_bundle(root)
            manifest["runs"][1]["predictions_path"] = manifest["runs"][0]["predictions_path"]
            result = AUDIT.audit(manifest, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("reused across multiple declared cells" in error for error in result["errors"]))

    def test_missing_row_cell_field_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.make_bundle(root)
            run = manifest["runs"][0]
            path = root / run["predictions_path"]
            row = json.loads(path.read_text(encoding="utf-8"))
            del row["condition"]
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            result = AUDIT.audit(manifest, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("missing cell fields" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
