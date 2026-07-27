#!/usr/bin/env python3
from __future__ import annotations

import unittest

from research.intelligence_swarm.governance.audit_normalized_holdout_identity import audit_rows


class NormalizedHoldoutIdentityAuditTests(unittest.TestCase):
    def _row(self, instance_id: str, split: str, condition: str, *, entity=None, dynamics=None):
        row = {
            "instance_id": instance_id,
            "domain": "rtfm",
            "seed": 1,
            "split": split,
            "condition": condition,
            "utterance": f"utterance-{instance_id}",
            "state_before": {"x": 0},
            "gold_action": 0,
            "gold_state_after": {"x": 1},
        }
        if entity is not None:
            row["entity_id"] = entity
        if dynamics is not None:
            row["dynamics_signature"] = dynamics
        return row

    def test_distinct_normalized_holdout_passes(self):
        rows = [
            self._row("train", "train", "in_distribution", entity="goblin"),
            self._row("eval", "test", "entity_holdout", entity="dragon"),
        ]
        result = audit_rows(rows)
        self.assertTrue(result["valid"], result["errors"])

    def test_fullwidth_case_alias_is_rejected(self):
        rows = [
            self._row("train", "train", "in_distribution", entity="Goblin"),
            self._row("eval", "test", "entity_holdout", entity="ＧＯＢＬＩＮ"),
        ]
        result = audit_rows(rows)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertTrue(any("normalized entity_holdout leakage" in error for error in result["errors"]))

    def test_numeric_string_alias_is_rejected(self):
        rows = [
            self._row("train", "train", "in_distribution", entity=7),
            self._row("eval", "test", "entity_holdout", entity="７"),
        ]
        result = audit_rows(rows)
        self.assertFalse(result["valid"])

    def test_control_and_whitespace_alias_is_rejected(self):
        rows = [
            self._row("train", "train", "in_distribution", entity="dark knight"),
            self._row("eval", "validation", "entity_holdout", entity="dark\u200bknight"),
        ]
        result = audit_rows(rows)
        self.assertFalse(result["valid"])

    def test_structured_dynamics_alias_is_rejected(self):
        rows = [
            self._row(
                "train",
                "train",
                "in_distribution",
                dynamics={"Mode": "CHASE", "rate": "１"},
            ),
            self._row(
                "eval",
                "eval",
                "dynamics_holdout",
                dynamics={"ｍｏｄｅ": "chase", "rate": 1},
            ),
        ]
        result = audit_rows(rows)
        self.assertFalse(result["valid"])
        self.assertTrue(any("normalized dynamics_holdout leakage" in error for error in result["errors"]))

    def test_missing_identity_is_fail_closed(self):
        rows = [
            self._row("train", "train", "in_distribution", entity="goblin"),
            self._row("eval", "test", "entity_holdout"),
        ]
        result = audit_rows(rows)
        self.assertFalse(result["valid"])
        self.assertTrue(any("requires entity_id or entity_signature" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
