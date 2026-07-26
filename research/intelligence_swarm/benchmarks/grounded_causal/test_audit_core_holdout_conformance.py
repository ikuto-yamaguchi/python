#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

import audit_core_holdout_conformance


SEEDS = (1, 7, 19)


def row(seed: int, split: str, condition: str, suffix: str, entity: str, dynamics: str):
    return {
        "instance_id": f"{seed}-{split}-{condition}-{suffix}",
        "domain": "rtfm",
        "seed": seed,
        "split": split,
        "condition": condition,
        "utterance": f"instruction {seed} {split} {condition} {suffix}",
        "state_before": {"x": suffix},
        "gold_action": 0,
        "gold_state_after": {"x": suffix, "done": True},
        "entity_id": entity,
        "dynamics_id": dynamics,
    }


def clean_bundle():
    rows = []
    for seed in SEEDS:
        rows.append(row(seed, "train", "in_distribution", "train", f"train-e-{seed}", f"train-d-{seed}"))
        rows.append(row(seed, "test", "entity_holdout", "entity", f"held-e-{seed}", f"train-d-{seed}"))
        rows.append(row(seed, "test", "dynamics_holdout", "dynamics", f"train-e-{seed}", f"held-d-{seed}"))
        rows.append(row(seed, "test", "language_holdout", "language", f"train-e-{seed}", f"train-d-{seed}"))
    return rows


class CoreHoldoutConformanceTests(unittest.TestCase):
    def test_clean_bundle_agrees(self):
        result = audit_core_holdout_conformance.audit(clean_bundle())
        self.assertTrue(result["valid"], result)
        self.assertTrue(result["core_explicit_holdout_agreement"])
        self.assertFalse(result["direct_core_bypass_detected"])

    def test_explicit_entity_overlap_exposes_core_bypass(self):
        rows = clean_bundle()
        rows[1]["entity_id"] = rows[0]["entity_id"]
        result = audit_core_holdout_conformance.audit(rows)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertTrue(result["direct_core_bypass_detected"])

    def test_explicit_dynamics_overlap_exposes_core_bypass(self):
        rows = clean_bundle()
        rows[2]["dynamics_id"] = rows[0]["dynamics_id"]
        result = audit_core_holdout_conformance.audit(rows)
        self.assertFalse(result["valid"])
        self.assertTrue(result["direct_core_bypass_detected"])

    def test_legacy_boolean_rejection_agrees(self):
        rows = clean_bundle()
        rows[1]["entity_id"] = rows[0]["entity_id"]
        rows[1]["entity_holdout"] = True
        result = audit_core_holdout_conformance.audit(rows)
        self.assertTrue(result["valid"], result)
        self.assertFalse(result["core_valid"])
        self.assertFalse(result["explicit_holdout_valid"])


if __name__ == "__main__":
    unittest.main()
