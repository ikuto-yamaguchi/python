#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "audit_holdout_condition_integrity", HERE / "audit_holdout_condition_integrity.py"
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class HoldoutConditionIntegrityTests(unittest.TestCase):
    def rows(self):
        rows = []
        for seed in (1, 7, 19):
            rows.append({
                "instance_id": f"train-{seed}",
                "domain": "rtfm_s1",
                "seed": seed,
                "split": "train",
                "condition": "in_distribution",
                "entity_signature": f"train-entity-{seed}",
                "dynamics_signature": f"train-dynamics-{seed}",
            })
            rows.append({
                "instance_id": f"id-{seed}",
                "domain": "rtfm_s1",
                "seed": seed,
                "split": "test",
                "condition": "in_distribution",
                "entity_signature": f"train-entity-{seed}",
                "dynamics_signature": f"train-dynamics-{seed}",
            })
            rows.append({
                "instance_id": f"entity-{seed}",
                "domain": "rtfm_s1",
                "seed": seed,
                "split": "test",
                "condition": "entity_holdout",
                "entity_holdout": True,
                "entity_signature": f"held-entity-{seed}",
                "dynamics_signature": f"train-dynamics-{seed}",
            })
            rows.append({
                "instance_id": f"dynamics-{seed}",
                "domain": "rtfm_s1",
                "seed": seed,
                "split": "test",
                "condition": "dynamics_holdout",
                "dynamics_holdout": True,
                "entity_signature": f"train-entity-{seed}",
                "dynamics_signature": f"held-dynamics-{seed}",
            })
        return rows

    def test_mixed_in_distribution_overlap_is_allowed(self):
        result = mod.audit(self.rows())
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["cell_count"], 2)
        self.assertTrue(result["in_distribution_overlap_is_not_misclassified"])

    def test_entity_holdout_overlap_fails(self):
        rows = self.rows()
        row = next(item for item in rows if item["instance_id"] == "entity-1")
        row["entity_signature"] = "train-entity-1"
        result = mod.audit(rows)
        self.assertFalse(result["valid"])
        self.assertTrue(any("entity holdout violation" in error for error in result["errors"]))
        self.assertEqual(result["classification"], "initial_reproduction_failure")

    def test_missing_holdout_signature_fails(self):
        rows = self.rows()
        row = next(item for item in rows if item["instance_id"] == "dynamics-7")
        row.pop("dynamics_signature")
        result = mod.audit(rows)
        self.assertFalse(result["valid"])
        self.assertTrue(any("rows without dynamics signature" in error for error in result["errors"]))

    def test_missing_seed_in_one_condition_fails(self):
        rows = [item for item in self.rows() if item["instance_id"] != "entity-19"]
        result = mod.audit(rows)
        self.assertFalse(result["valid"])
        self.assertTrue(any("missing=[19]" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
