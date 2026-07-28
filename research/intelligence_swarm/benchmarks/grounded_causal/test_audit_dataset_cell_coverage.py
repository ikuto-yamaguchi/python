#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("audit_dataset_cell_coverage", HERE / "audit_dataset_cell_coverage.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class DatasetCellCoverageTests(unittest.TestCase):
    def rows(self):
        rows = []
        for seed in (1, 7, 19):
            rows.append({
                "instance_id": f"train-{seed}", "domain": "rtfm_s1", "seed": seed,
                "split": "train", "utterance": [seed], "state_before": [0],
                "state_after": [1], "action": 1,
            })
            for condition in ("in_distribution", "entity_holdout", "dynamics_holdout", "language_holdout"):
                rows.append({
                    "instance_id": f"test-{seed}-{condition}", "domain": "rtfm_s1", "seed": seed,
                    "split": "test", "condition": condition, "utterance": [seed, len(condition)],
                    "state_before": [0], "state_after": [1], "action": 1,
                })
        return rows

    def test_complete_cells_pass(self):
        result = mod.audit(self.rows())
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["evaluation_cell_count"], 4)
        self.assertTrue(all(cell["complete"] for cell in result["evaluation_cells"]))

    def test_one_missing_seed_in_one_condition_fails(self):
        rows = [
            row for row in self.rows()
            if not (row["split"] == "test" and row["condition"] == "dynamics_holdout" and row["seed"] == 19)
        ]
        result = mod.audit(rows)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertTrue(any("dynamics_holdout" in error and "19" in error for error in result["errors"]))

    def test_three_wrong_global_seeds_fail(self):
        rows = self.rows()
        mapping = {1: 2, 7: 3, 19: 5}
        for row in rows:
            row["seed"] = mapping[row["seed"]]
        result = mod.audit(rows)
        self.assertFalse(result["valid"])
        self.assertTrue(any("non-canonical seeds" in error for error in result["errors"]))

    def test_each_domain_must_have_all_seeds(self):
        rows = self.rows()
        rows.extend([
            {
                "instance_id": "other-test-1", "domain": "messenger", "seed": 1,
                "split": "test", "condition": "in_distribution", "utterance": [1],
                "state_before": [0], "state_after": [1], "action": 1,
            },
            {
                "instance_id": "other-test-7", "domain": "messenger", "seed": 7,
                "split": "test", "condition": "in_distribution", "utterance": [7],
                "state_before": [0], "state_after": [1], "action": 1,
            },
        ])
        result = mod.audit(rows)
        self.assertFalse(result["valid"])
        self.assertTrue(any("messenger" in error and "19" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
