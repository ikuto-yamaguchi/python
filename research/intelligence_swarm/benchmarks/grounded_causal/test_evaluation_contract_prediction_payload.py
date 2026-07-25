from __future__ import annotations

import copy
import math
import unittest

import evaluation_contract as contract


METHODS = sorted(contract.REQUIRED_METHODS)
SHUFFLES = contract.SHUFFLE_METHODS


def dataset() -> list[dict]:
    rows = []
    for seed in sorted(contract.CANONICAL_SEEDS):
        for split in ("train", "test"):
            for item in range(2):
                iid = f"{split}-{seed}-{item}"
                rows.append({
                    "instance_id": iid,
                    "domain": "rtfm_s1",
                    "seed": seed,
                    "split": split,
                    "condition": "in_distribution",
                    "utterance": f"utterance-{iid}",
                    "state_before": {"x": item},
                    "gold_action": item,
                    "gold_state_after": {"x": item + 1},
                    "valid_action_mask": [True, True],
                    "entity_signature": f"entity-{iid}",
                    "dynamics_signature": f"dynamics-{iid}",
                    "episode_id": f"episode-{iid}",
                    "episode_seed": f"episode-seed-{iid}",
                    "observation_fingerprint": f"observation-{iid}",
                })
    return rows


def predictions(data: list[dict]) -> list[dict]:
    eval_rows = [row for row in contract.adapt_dataset(data) if row["split"] == "test"]
    by_cell: dict[tuple, list[dict]] = {}
    for row in eval_rows:
        by_cell.setdefault(contract._cell_key(row), []).append(row)

    result = []
    for row in eval_rows:
        for method in METHODS:
            pred = {
                "instance_id": row["instance_id"],
                "method": method,
                "instance_fingerprint": contract.instance_fingerprint(row),
                "pred_action": row["gold_action"],
                "pred_state_after": row["gold_state_after"],
            }
            if method in SHUFFLES:
                peers = by_cell[contract._cell_key(row)]
                donor = peers[1] if peers[0]["instance_id"] == row["instance_id"] else peers[0]
                pred["control_source_instance_id"] = donor["instance_id"]
                pred["control_source_fingerprint"] = contract.instance_fingerprint(donor)
            result.append(pred)
    return result


class PredictionPayloadContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = dataset()
        self.preds = predictions(self.data)

    def test_clean_payload_passes(self) -> None:
        result = contract.score(self.data, self.preds)
        self.assertTrue(result["valid"], result["errors"])
        self.assertTrue(result["strict_prediction_schema"])
        self.assertEqual(result["prediction_payload_findings"], [])

    def test_gold_after_state_is_rejected(self) -> None:
        bad = copy.deepcopy(self.preds)
        bad[0]["gold_state_after"] = {"x": 999}
        result = contract.score(self.data, bad)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertTrue(any("forbidden gold/outcome" in error for error in result["errors"]))

    def test_completed_trajectory_is_rejected(self) -> None:
        bad = copy.deepcopy(self.preds)
        bad[0]["completed_trajectory"] = [{"reward": 1}]
        result = contract.score(self.data, bad)
        self.assertFalse(result["valid"])
        self.assertTrue(any("completed_trajectory" in error for error in result["errors"]))

    def test_unregistered_debug_payload_is_rejected(self) -> None:
        bad = copy.deepcopy(self.preds)
        bad[0]["debug_hidden_state"] = [1, 2, 3]
        result = contract.score(self.data, bad)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unregistered fields" in error for error in result["errors"]))

    def test_non_finite_prediction_is_rejected(self) -> None:
        bad = copy.deepcopy(self.preds)
        bad[0]["pred_state_after"] = {"x": math.nan}
        result = contract.score(self.data, bad)
        self.assertFalse(result["valid"])
        self.assertTrue(any("non-finite" in error for error in result["errors"]))

    def test_invalid_action_is_rejected(self) -> None:
        bad = copy.deepcopy(self.preds)
        bad[0]["pred_action"] = 7
        result = contract.score(self.data, bad)
        self.assertFalse(result["valid"])
        self.assertTrue(any("valid-action schema" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
