#!/usr/bin/env python3
from __future__ import annotations

import unittest

import evaluation_contract as contract


class InvalidPredictionStatisticsCoreTests(unittest.TestCase):
    def _dataset(self) -> list[dict]:
        rows: list[dict] = []
        for seed in sorted(contract.CANONICAL_SEEDS):
            rows.append({
                "instance_id": f"train-{seed}", "domain": "rtfm", "seed": seed,
                "split": "train", "condition": "in_distribution",
                "utterance": f"train utterance {seed}", "state_before": {"hp": 10},
                "gold_action": 0, "gold_state_after": {"hp": 9},
            })
            for index in range(2):
                rows.append({
                    "instance_id": f"test-{seed}-{index}", "domain": "rtfm", "seed": seed,
                    "split": "test", "condition": "in_distribution",
                    "utterance": f"test utterance {seed} {index}", "state_before": {"hp": 10 + index},
                    "gold_action": index, "gold_state_after": {"hp": 9 + index},
                })
        self.assertTrue(contract.validate_dataset(rows)["valid"])
        return rows

    def _predictions(self, data: list[dict]) -> list[dict]:
        eval_rows = [row for row in contract.adapt_dataset(data) if row["split"] == "test"]
        by_cell: dict[int, list[dict]] = {}
        for row in eval_rows:
            by_cell.setdefault(int(row["seed"]), []).append(row)
        predictions: list[dict] = []
        for method in sorted(contract.REQUIRED_METHODS):
            for row in eval_rows:
                pred = {
                    "instance_id": row["instance_id"],
                    "method": method,
                    "instance_fingerprint": contract.instance_fingerprint(row),
                    "pred_action": row["gold_action"],
                    "pred_state_after": row["gold_state_after"],
                }
                if method in contract.SHUFFLE_METHODS:
                    peers = by_cell[int(row["seed"])]
                    donor = peers[1] if peers[0]["instance_id"] == row["instance_id"] else peers[0]
                    pred["control_source_instance_id"] = donor["instance_id"]
                    pred["control_source_fingerprint"] = contract.instance_fingerprint(donor)
                predictions.append(pred)
        return predictions

    def test_valid_predictions_emit_statistics(self) -> None:
        data = self._dataset()
        report = contract.score(data, self._predictions(data))
        self.assertTrue(report["valid"], report["errors"])
        self.assertTrue(report["statistics_emitted"])
        self.assertTrue(report["cells"])
        self.assertTrue(report["summary"])
        self.assertTrue(report["paired_gaps_vs_correct"])

    def test_prediction_contract_error_suppresses_all_statistics(self) -> None:
        data = self._dataset()
        predictions = self._predictions(data)
        predictions[0]["gold_action"] = 0
        report = contract.score(data, predictions)
        self.assertFalse(report["valid"])
        self.assertEqual(report["classification"], "initial_reproduction_failure")
        self.assertTrue(any("forbidden" in error for error in report["errors"]))
        self.assertTrue(report["invalid_score_statistics_forbidden"])
        self.assertFalse(report["statistics_emitted"])
        self.assertEqual(report["cells"], [])
        self.assertEqual(report["summary"], {})
        self.assertEqual(report["paired_gaps_vs_correct"], {})


if __name__ == "__main__":
    unittest.main()
