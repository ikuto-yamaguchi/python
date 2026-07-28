#!/usr/bin/env python3
from __future__ import annotations

import unittest

from audit_model_input_semantic_leakage import audit_rows


def base_row() -> dict:
    return {
        "instance_id": "i1",
        "state_before": {"x": 0},
        "gold_action": 2,
        "gold_state_after": {"x": 1},
        "model_input": {
            "utterance": [1, 2],
            "state_before": {"x": 0},
            "history": [{"state": {"x": -1}, "action": 0}],
            "valid_action_mask": [1, 1, 1, 0, 0],
        },
    }


class SemanticLeakageAuditTest(unittest.TestCase):
    def test_clean_prospective_input_passes(self) -> None:
        result = audit_rows([base_row()])
        self.assertTrue(result["valid"], result["errors"])

    def test_future_state_alias_fails(self) -> None:
        row = base_row()
        row["model_input"]["future_state"] = {"x": 1}
        result = audit_rows([row])
        self.assertFalse(result["valid"])
        self.assertTrue(any(item["kind"] == "future_or_outcome_alias" for item in result["findings"]))
        self.assertTrue(any(item["kind"] == "gold_after_value_match" for item in result["findings"]))

    def test_completed_rollout_alias_fails(self) -> None:
        row = base_row()
        row["model_input"]["rollout_context"] = [{"state": {"x": 1}, "reward": 1}]
        result = audit_rows([row])
        self.assertFalse(result["valid"])
        self.assertTrue(any(item["kind"] == "future_or_outcome_alias" for item in result["findings"]))

    def test_action_label_alias_fails(self) -> None:
        row = base_row()
        row["model_input"]["target_action"] = 2
        result = audit_rows([row])
        self.assertFalse(result["valid"])
        self.assertTrue(any(item["kind"] == "gold_action_value_under_alias" for item in result["findings"]))


if __name__ == "__main__":
    unittest.main()
