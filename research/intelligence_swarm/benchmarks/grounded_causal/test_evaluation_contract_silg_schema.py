#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("evaluation_contract", HERE / "evaluation_contract.py")
assert SPEC and SPEC.loader
EC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EC)


def silg_rows() -> list[dict]:
    rows = []
    for seed in (1, 7, 19):
        rows.append({
            "instance_id": f"train-{seed}-0-0",
            "episode_id": f"train-{seed}-0",
            "episode_seed": seed * 1_000_003,
            "domain": "silg:rtfm_train_s1-v0",
            "seed": seed,
            "split": "train",
            "observation_fingerprint": f"trainfp-{seed}",
            "text_tokens": [10, seed, 0, 20],
            "state_before": [0, seed],
            "state_after": [1, seed],
            "action": 1,
            "reward": 0.0,
            "done": False,
            "entity_holdout": False,
            "dynamics_holdout": False,
            "language_holdout": False,
        })
        rows.append({
            "instance_id": f"test-{seed}-0-0",
            "episode_id": f"test-{seed}-0",
            "episode_seed": seed * 1_000_003 + 999,
            "domain": "silg:rtfm_test_s1-v0",
            "seed": seed,
            "split": "test",
            "observation_fingerprint": f"testfp-{seed}",
            "text_tokens": [30, seed, 0, 40],
            "state_before": [0, seed],
            "state_after": [1, seed],
            "action": 1,
            "reward": 1.0,
            "done": True,
            "entity_holdout": False,
            "dynamics_holdout": False,
            "language_holdout": True,
        })
    return rows


class SILGSchemaTests(unittest.TestCase):
    def test_export_schema_is_adapted_without_outcome_leakage(self) -> None:
        result = EC.validate_dataset(silg_rows())
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["silg_rows_adapted"], 6)
        self.assertTrue(result["silg_text_tokens_supported"])
        row = EC.adapt_row(silg_rows()[0])
        self.assertEqual(row["utterance"], [10, 1, 0, 20])
        self.assertEqual(row["gold_action"], 1)
        self.assertEqual(row["gold_state_after"], [1, 1])
        self.assertNotIn("reward", row["model_input_fields"])
        self.assertNotIn("done", row["model_input_fields"])

    def test_episode_seed_cannot_cross_train_test(self) -> None:
        rows = silg_rows()
        rows[1]["episode_seed"] = rows[0]["episode_seed"]
        result = EC.validate_dataset(rows)
        self.assertFalse(result["valid"])
        self.assertTrue(any("episode_seed leakage" in error for error in result["errors"]))

    def test_observation_fingerprint_cannot_cross_train_test(self) -> None:
        rows = silg_rows()
        rows[1]["observation_fingerprint"] = rows[0]["observation_fingerprint"]
        result = EC.validate_dataset(rows)
        self.assertFalse(result["valid"])
        self.assertTrue(any("observation_fingerprint leakage" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
