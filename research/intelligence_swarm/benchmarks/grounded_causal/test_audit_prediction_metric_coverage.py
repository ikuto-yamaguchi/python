#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from audit_prediction_metric_coverage import REQUIRED_METHODS, audit


SEEDS = (1, 7, 19)


def make_dataset(include_inverse: bool = True) -> list[dict]:
    rows = []
    for seed in SEEDS:
        rows.append({
            "instance_id": f"train-{seed}",
            "seed": seed,
            "domain": "rtfm",
            "split": "train",
            "condition": "in_distribution",
        })
        for item in range(2):
            row = {
                "instance_id": f"test-{seed}-{item}",
                "seed": seed,
                "domain": "rtfm",
                "split": "test",
                "condition": "in_distribution",
            }
            if include_inverse:
                row["gold_inverse"] = item
            rows.append(row)
    return rows


def make_predictions(dataset: list[dict], include_inverse: bool = True) -> list[dict]:
    rows = []
    for item in dataset:
        if item["split"] == "train":
            continue
        for method in sorted(REQUIRED_METHODS):
            row = {
                "instance_id": item["instance_id"],
                "method": method,
                "pred_action": 0,
                "pred_state_after": {},
            }
            if include_inverse:
                row["pred_inverse"] = 0
            rows.append(row)
    return rows


class PredictionMetricCoverageTest(unittest.TestCase):
    def test_complete_matched_metric_bundle_passes(self) -> None:
        data = make_dataset()
        result = audit(data, make_predictions(data))
        self.assertTrue(result["valid"], result["errors"])
        self.assertTrue(result["metric_contract"]["inverse"]["required"])

    def test_one_method_selectively_omits_inverse(self) -> None:
        data = make_dataset()
        predictions = make_predictions(data)
        del next(row for row in predictions if row["method"] == "state_only")["pred_inverse"]
        result = audit(data, predictions)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertTrue(any("state_only omits pred_inverse" in error for error in result["errors"]))

    def test_gold_inverse_partial_coverage_fails(self) -> None:
        data = make_dataset()
        del next(row for row in data if row["split"] == "test")["gold_inverse"]
        result = audit(data, make_predictions(data))
        self.assertFalse(result["valid"])
        self.assertTrue(any("gold field gold_inverse is present on only" in error for error in result["errors"]))

    def test_prediction_inverse_without_gold_fails(self) -> None:
        data = make_dataset(include_inverse=False)
        result = audit(data, make_predictions(data, include_inverse=True))
        self.assertFalse(result["valid"])
        self.assertTrue(any("supplies pred_inverse without gold_inverse" in error for error in result["errors"]))

    def test_one_method_missing_one_instance_fails(self) -> None:
        data = make_dataset()
        predictions = make_predictions(data)
        predictions.remove(next(row for row in predictions if row["method"] == "outcome_shuffle"))
        result = audit(data, predictions)
        self.assertFalse(result["valid"])
        self.assertTrue(any("outcome_shuffle: incomplete instance coverage" in error for error in result["errors"]))

    def test_unregistered_split_fails(self) -> None:
        data = make_dataset()
        target = next(row for row in data if row["split"] == "test")
        target["split"] = "posthoc"
        result = audit(data, make_predictions(data))
        self.assertFalse(result["valid"])
        self.assertTrue(any("unregistered evaluation split='posthoc'" in error for error in result["errors"]))

    def test_noncanonical_seed_fails(self) -> None:
        data = make_dataset()
        target = next(row for row in data if row["split"] == "test")
        old_id = target["instance_id"]
        target["seed"] = 23
        predictions = make_predictions(data)
        self.assertTrue(any(row["instance_id"] == old_id for row in predictions))
        result = audit(data, predictions)
        self.assertFalse(result["valid"])
        self.assertTrue(any("noncanonical seed=23" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
