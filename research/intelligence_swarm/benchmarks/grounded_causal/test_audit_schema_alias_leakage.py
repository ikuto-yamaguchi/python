from __future__ import annotations

import copy
import unittest

import audit_schema_alias_leakage as audit
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
                    "model_input_fields": ["utterance", "state_before", "valid_action_mask"],
                    "model_input": {
                        "utterance": f"utterance-{iid}",
                        "state_before": {"x": item},
                        "valid_action_mask": [True, True],
                    },
                })
    return rows


def predictions(data: list[dict]) -> list[dict]:
    result = []
    eval_rows = [row for row in contract.adapt_dataset(data) if row["split"] == "test"]
    by_cell = {}
    for row in eval_rows:
        by_cell.setdefault(contract._cell_key(row), []).append(row)
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


class AliasLeakageAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = dataset()
        self.preds = predictions(self.data)

    def test_clean_bundle_passes(self) -> None:
        result = audit.audit(self.data, self.preds)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["findings"], [])

    def test_camel_case_gold_after_in_nested_model_input_is_rejected(self) -> None:
        bad = copy.deepcopy(self.data)
        bad[0]["model_input"]["cache"] = {"goldStateAfter": {"x": 999}}
        result = audit.audit(bad, self.preds)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertTrue(any(item["canonical_forbidden_key"] == "gold_state_after" for item in result["findings"]))

    def test_kebab_case_completed_trajectory_is_rejected(self) -> None:
        bad = copy.deepcopy(self.data)
        bad[0]["model_input"]["cache"] = {"completed-trajectory": [{"reward": 1}]}
        result = audit.audit(bad, self.preds)
        self.assertFalse(result["valid"])
        self.assertTrue(any(item["canonical_forbidden_key"] == "completed_trajectory" for item in result["findings"]))

    def test_camel_case_model_input_field_is_rejected(self) -> None:
        bad = copy.deepcopy(self.data)
        bad[0]["model_input_fields"].append("goldAction")
        result = audit.audit(bad, self.preds)
        self.assertFalse(result["valid"])
        self.assertTrue(any(item["source"] == "dataset.model_input_fields" for item in result["findings"]))

    def test_prediction_alias_is_rejected(self) -> None:
        bad = copy.deepcopy(self.preds)
        bad[0]["episodeReturn"] = 1.0
        result = audit.audit(self.data, bad)
        self.assertFalse(result["valid"])
        self.assertTrue(any(item["canonical_forbidden_key"] == "episode_return" for item in result["findings"]))

    def test_unknown_prediction_key_is_rejected(self) -> None:
        bad = copy.deepcopy(self.preds)
        bad[0]["debugPayload"] = {"x": 1}
        result = audit.audit(self.data, bad)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unregistered prediction key" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
