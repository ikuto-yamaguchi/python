#!/usr/bin/env python3
from __future__ import annotations

import unittest

import evaluation_contract as contract


class CoreScoreDatasetBindingTests(unittest.TestCase):
    def test_invalid_dataset_suppresses_all_statistical_sections(self) -> None:
        row = {
            "instance_id": "dup",
            "domain": "rtfm",
            "seed": 1,
            "split": "test",
            "condition": "entity_holdout",
            "utterance": "attack goblin",
            "state_before": {"hp": 10},
            "gold_action": 0,
            "gold_state_after": {"hp": 9},
            "entity_id": "goblin",
        }
        data = [dict(row), dict(row)]
        report = contract.score(data, [])
        self.assertFalse(report["valid"])
        self.assertEqual(report["classification"], "initial_reproduction_failure")
        self.assertTrue(report["dataset_contract_binding"])
        self.assertFalse(report["dataset_contract_valid"])
        self.assertTrue(report["dataset_contract_errors"])
        self.assertEqual(report["cells"], [])
        self.assertEqual(report["summary"], {})
        self.assertEqual(report["paired_gaps_vs_correct"], {})

    def test_score_validity_matches_dataset_contract(self) -> None:
        data = []
        dataset = contract.validate_dataset(data)
        report = contract.score(data, [])
        self.assertIs(report["dataset_contract_valid"], dataset["valid"])
        self.assertEqual(report["dataset_contract_errors"], dataset["errors"])
        self.assertTrue(report["invalid_dataset_statistics_forbidden"])


if __name__ == "__main__":
    unittest.main()
