from __future__ import annotations

import copy
import unittest

import evaluation_contract as contract


METHODS = sorted(contract.REQUIRED_METHODS)


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
            if method in contract.SHUFFLE_METHODS:
                peers = by_cell[contract._cell_key(row)]
                donor = peers[1] if peers[0]["instance_id"] == row["instance_id"] else peers[0]
                pred["control_source_instance_id"] = donor["instance_id"]
                pred["control_source_fingerprint"] = contract.instance_fingerprint(donor)
            result.append(pred)
    return result


class CoreAliasLeakageTests(unittest.TestCase):
    def test_clean_bundle_passes(self) -> None:
        data = dataset()
        self.assertTrue(contract.validate_dataset(data)["valid"])
        self.assertTrue(contract.score(data, predictions(data))["valid"])

    def test_camel_case_model_input_field_is_rejected(self) -> None:
        data = dataset()
        data[0]["model_input_fields"] = ["goldAction"]
        result = contract.validate_dataset(data)
        self.assertFalse(result["valid"])
        self.assertTrue(result["schema_alias_findings"])

    def test_nested_kebab_case_completed_trajectory_is_rejected(self) -> None:
        data = dataset()
        data[0]["model_input"] = {"history": {"completed-Trajectory": []}}
        result = contract.validate_dataset(data)
        self.assertFalse(result["valid"])
        self.assertTrue(result["schema_alias_findings"])

    def test_prediction_episode_return_alias_is_rejected(self) -> None:
        data = dataset()
        preds = predictions(data)
        preds[0]["episodeReturn"] = 1
        result = contract.score(data, preds)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertTrue(result["prediction_schema_alias_findings"])

    def test_allowed_field_alias_is_not_silently_canonicalized(self) -> None:
        data = dataset()
        preds = predictions(data)
        preds[0]["predAction"] = preds[0].pop("pred_action")
        result = contract.score(data, preds)
        self.assertFalse(result["valid"])
        self.assertTrue(any("missing" in error or "unregistered" in error for error in result["errors"]))

    def test_alias_collision_is_rejected(self) -> None:
        data = dataset()
        preds = predictions(data)
        preds[0]["pred-Action"] = preds[0]["pred_action"]
        result = contract.score(data, preds)
        self.assertFalse(result["valid"])
        self.assertTrue(any("alias-colliding" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
