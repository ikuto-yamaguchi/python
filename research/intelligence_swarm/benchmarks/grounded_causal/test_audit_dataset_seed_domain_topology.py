#!/usr/bin/env python3
from __future__ import annotations

import unittest

from audit_dataset_seed_domain_topology import audit


class Tests(unittest.TestCase):
    def rows(self):
        rows = []
        for seed in (1, 7, 19):
            rows.append({
                "instance_id": f"train-{seed}", "domain": "rtfm_s1",
                "seed": seed, "split": "train", "condition": "in_distribution",
            })
            rows.append({
                "instance_id": f"test-{seed}", "domain": "rtfm_s1",
                "seed": seed, "split": "test", "condition": "dynamics_holdout",
            })
        return rows

    def test_valid_exact_canonical_topology(self):
        result = audit(self.rows())
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["classification"], "qualified")

    def test_rejects_three_noncanonical_seeds(self):
        rows = self.rows()
        for row in rows:
            row["seed"] = {1: 2, 7: 3, 19: 4}[row["seed"]]
        result = audit(rows)
        self.assertFalse(result["valid"])
        self.assertTrue(any("exactly [1, 7, 19]" in error for error in result["errors"]))
        self.assertEqual(result["classification"], "initial_reproduction_failure")

    def test_rejects_seed_missing_from_one_eval_cell(self):
        rows = [row for row in self.rows() if not (
            row["seed"] == 19 and row["split"] == "test"
        )]
        result = audit(rows)
        self.assertFalse(result["valid"])
        self.assertTrue(any("evaluation cell" in error and "missing=[19]" in error for error in result["errors"]))

    def test_rejects_seed_without_train_split(self):
        rows = [row for row in self.rows() if not (
            row["seed"] == 7 and row["split"] == "train"
        )]
        result = audit(rows)
        self.assertFalse(result["valid"])
        self.assertIn("seed 7: train split is missing", result["errors"])

    def test_rejects_empty_domain(self):
        rows = self.rows()
        rows[0]["domain"] = ""
        result = audit(rows)
        self.assertFalse(result["valid"])
        self.assertTrue(any("empty/missing domain" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
