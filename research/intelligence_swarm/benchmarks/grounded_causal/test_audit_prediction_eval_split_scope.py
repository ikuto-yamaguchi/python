#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from audit_prediction_eval_split_scope import REQUIRED_METHODS, audit


def dataset() -> list[dict]:
    rows = []
    for seed in (1, 7, 19):
        rows.append({"instance_id": f"train-{seed}", "seed": seed, "domain": "rtfm", "split": "train", "condition": "in_distribution"})
        rows.append({"instance_id": f"test-{seed}", "seed": seed, "domain": "rtfm", "split": "test", "condition": "entity_holdout"})
    return rows


def predictions(rows: list[dict]) -> list[dict]:
    eval_ids = [row["instance_id"] for row in rows if row["split"] == "test"]
    return [{"instance_id": iid, "method": method} for method in sorted(REQUIRED_METHODS) for iid in eval_ids]


class SplitScopeTests(unittest.TestCase):
    def test_registered_train_and_test_pass(self) -> None:
        rows = dataset()
        self.assertTrue(audit(rows, predictions(rows))["valid"])

    def test_debug_split_fails_even_with_predictions(self) -> None:
        rows = dataset()
        rows.append({"instance_id": "debug-1", "seed": 1, "domain": "rtfm", "split": "debug", "condition": "in_distribution"})
        preds = predictions(rows)
        preds.extend({"instance_id": "debug-1", "method": method} for method in REQUIRED_METHODS)
        result = audit(rows, preds)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unregistered split='debug'" in error for error in result["errors"]))

    def test_calibration_prediction_fails(self) -> None:
        rows = dataset()
        extra = {"instance_id": "cal-1", "seed": 1, "domain": "rtfm", "split": "calibration", "condition": "in_distribution"}
        rows.append(extra)
        preds = predictions(rows)
        preds.append({"instance_id": "cal-1", "method": "correct"})
        result = audit(rows, preds)
        self.assertFalse(result["valid"])
        self.assertTrue(any("non-evaluation split='calibration'" in error for error in result["errors"]))

    def test_train_prediction_fails(self) -> None:
        rows = dataset()
        preds = predictions(rows)
        preds.append({"instance_id": "train-1", "method": "correct"})
        result = audit(rows, preds)
        self.assertFalse(result["valid"])
        self.assertTrue(any("non-evaluation split='train'" in error for error in result["errors"]))

    def test_missing_method_cell_fails(self) -> None:
        rows = dataset()
        preds = predictions(rows)
        preds = [row for row in preds if not (row["method"] == "outcome_shuffle" and row["instance_id"] == "test-19")]
        result = audit(rows, preds)
        self.assertFalse(result["valid"])
        self.assertTrue(any("outcome_shuffle" in error and "missing" in error for error in result["errors"]))

    def test_noncanonical_eval_seed_fails(self) -> None:
        rows = dataset()
        mutated = copy.deepcopy(rows)
        for row in mutated:
            if row["seed"] == 19:
                row["seed"] = 23
                row["instance_id"] = row["instance_id"].replace("19", "23")
        result = audit(mutated, predictions(mutated))
        self.assertFalse(result["valid"])
        self.assertTrue(any("seeds must be exactly" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
