#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "audit_prediction_method_topology", HERE / "audit_prediction_method_topology.py"
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
ec = mod.ec
METHODS = sorted(mod.EXPECTED_METHODS)


class Tests(unittest.TestCase):
    def rows(self):
        rows = []
        for seed in (1, 7, 19):
            rows.append({
                "instance_id": f"train-{seed}",
                "domain": "rtfm_s1",
                "seed": seed,
                "split": "train",
                "condition": "in_distribution",
                "utterance": f"train {seed}",
                "state_before": [0, seed],
                "gold_action": 1,
                "gold_state_after": [1, seed],
            })
            for condition in ("entity_holdout", "dynamics_holdout", "language_holdout"):
                for replica in (0, 1):
                    rows.append({
                        "instance_id": f"test-{seed}-{condition}-{replica}",
                        "domain": "rtfm_s1",
                        "seed": seed,
                        "split": "test",
                        "condition": condition,
                        "utterance": f"test {seed} {condition} {replica}",
                        "state_before": [0, seed, condition, replica],
                        "gold_action": 1,
                        "gold_state_after": [1, seed, condition, replica],
                        condition: True,
                        "entity_signature": f"e-{seed}-{condition}-{replica}",
                        "dynamics_signature": f"d-{seed}-{condition}-{replica}",
                    })
        return rows

    def predictions(self, rows):
        eval_rows = [row for row in rows if row["split"] != "train"]
        by_cell = defaultdict(list)
        for row in eval_rows:
            adapted = ec.adapt_row(row)
            by_cell[ec._cell_key(adapted)].append(row)
        donors = {}
        for values in by_cell.values():
            self.assertGreaterEqual(len(values), 2)
            for i, row in enumerate(values):
                donors[row["instance_id"]] = values[(i + 1) % len(values)]
        result = []
        for row in eval_rows:
            fingerprint = ec.instance_fingerprint(ec.adapt_row(row))
            for method in METHODS:
                pred = {
                    "instance_id": row["instance_id"],
                    "method": method,
                    "instance_fingerprint": fingerprint,
                    "pred_action": row["gold_action"] if method == "correct" else 0,
                    "pred_state_after": row["gold_state_after"] if method == "correct" else row["state_before"],
                }
                if method in ec.SHUFFLE_METHODS:
                    donor = donors[row["instance_id"]]
                    pred["control_source_instance_id"] = donor["instance_id"]
                    pred["control_source_fingerprint"] = ec.instance_fingerprint(ec.adapt_row(donor))
                result.append(pred)
        return result

    def test_accepts_exact_topology(self):
        rows = self.rows()
        result = mod.audit(rows, self.predictions(rows))
        self.assertTrue(result["valid"], result["errors"])
        self.assertTrue(result["exact_method_set_per_instance_required"])
        self.assertTrue(result["exact_method_set_per_cell_required"])

    def test_rejects_unregistered_extra_method(self):
        rows = self.rows()
        predictions = self.predictions(rows)
        extra = dict(predictions[0])
        extra["method"] = "representation_probe"
        predictions.append(extra)
        result = mod.audit(rows, predictions)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertTrue(any("unregistered prediction methods" in error for error in result["errors"]))

    def test_rejects_method_missing_on_one_instance(self):
        rows = self.rows()
        missing_id = "test-19-language_holdout-1"
        predictions = [
            pred for pred in self.predictions(rows)
            if not (pred["method"] == "state_only" and pred["instance_id"] == missing_id)
        ]
        result = mod.audit(rows, predictions)
        self.assertFalse(result["valid"])
        self.assertTrue(any(f"instance {missing_id}" in error for error in result["errors"]))

    def test_rejects_method_missing_from_one_cell(self):
        rows = self.rows()
        predictions = [
            pred for pred in self.predictions(rows)
            if not (
                pred["method"] == "outcome_shuffle"
                and pred["instance_id"].startswith("test-7-dynamics_holdout-")
            )
        ]
        result = mod.audit(rows, predictions)
        self.assertFalse(result["valid"])
        self.assertTrue(any("outcome_shuffle" in error and "prediction identity mismatch" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
