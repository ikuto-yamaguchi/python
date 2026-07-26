#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "aggregate_r02_three_seed_results.py"
SEEDS = (1, 7, 19)
METHODS = ("environment_first", "end_to_end", "state_only")


def write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def comparison(seed: int) -> dict:
    evaluations = []
    for index, method in enumerate(METHODS):
        evaluations.append(
            {
                "method": method,
                "conditions": {
                    "all": {"n": 10, "typed_next_state_loss": 0.4 + index * 0.1},
                    "dynamics_holdout": {"n": 4, "typed_next_state_loss": 0.5 + index * 0.1},
                },
            }
        )
    return {
        "seed": seed,
        "config": {"env_epochs": 8, "lang_epochs": 8, "num_actions": 6},
        "dataset": {"n_train": 20, "n_test": 10},
        "evaluations": evaluations,
        "training": {
            "environment_pretraining_seconds": 1.0,
            "environment_first_language_seconds": 2.0,
            "end_to_end_seconds": 3.0,
            "state_only_seconds": 1.5,
            "peak_rss_kib": 12345 + seed,
        },
    }


def policy(seed: int) -> dict:
    return {
        "seed": seed,
        "evaluations": [
            {
                "method": method,
                "checkpoint": {"bytes": 1000 + index},
                "conditions": {
                    "all": {"n": 10, "policy_action_accuracy_valid_masked": 0.7 - index * 0.1},
                    "dynamics_holdout": {"n": 4, "policy_action_accuracy_valid_masked": 0.6 - index * 0.1},
                },
            }
            for index, method in enumerate(METHODS)
        ],
    }


def online(seed: int) -> dict:
    episode_seeds = [seed * 100 + i for i in range(3)]
    wins = {
        "environment_first": [1, 1, 0],
        "end_to_end": [1, 0, 0],
        "state_only": [0, 0, 0],
    }
    return {
        "seed": seed,
        "runs": [
            {
                "method": method,
                "win_rate": sum(wins[method]) / len(episode_seeds),
                "return_mean": sum(wins[method]) / len(episode_seeds),
                "cpu_inference_ms_per_step": 0.2 + index * 0.1,
                "episode_records": [
                    {"episode_seed": episode_seed, "win": win, "return": float(win)}
                    for episode_seed, win in zip(episode_seeds, wins[method])
                ],
            }
            for index, method in enumerate(METHODS)
        ],
    }


class AggregateR02ThreeSeedResultsTest(unittest.TestCase):
    def populate(self, root: Path) -> None:
        for seed in SEEDS:
            write(root / f"SILG_RTFM_R02_TYPED_COMPARISON_SEED_{seed}.json", comparison(seed))
            write(root / f"SILG_RTFM_R02_OFFLINE_POLICY_METRICS_SEED_{seed}.json", policy(seed))
            write(root / f"SILG_RTFM_R02_ONLINE_SEED_{seed}.json", online(seed))

    def run_script(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--results", str(root), "--out", str(root / "summary.json")],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_writes_three_seed_paired_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.populate(root)
            result = self.run_script(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads((root / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["seeds"], [1, 7, 19])
            self.assertEqual(payload["holdout_scope"]["entity"], "inapplicable for RTFM S1")
            paired = payload["paired_environment_first_minus_control"]
            self.assertEqual(paired["end_to_end"]["paired_instances"], 9)
            self.assertGreater(paired["end_to_end"]["task_success_mean_gap"], 0.0)
            self.assertGreater(paired["state_only"]["task_success_min_seed_gap"], 0.0)

    def test_rejects_cross_seed_configuration_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.populate(root)
            path = root / "SILG_RTFM_R02_TYPED_COMPARISON_SEED_19.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["config"]["lang_epochs"] = 9
            write(path, payload)
            result = self.run_script(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("configuration changed across seeds", result.stderr)

    def test_rejects_incomplete_paired_episode_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.populate(root)
            path = root / "SILG_RTFM_R02_ONLINE_SEED_7.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["runs"][1]["episode_records"].pop()
            write(path, payload)
            result = self.run_script(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("incomplete paired coverage", result.stderr)


if __name__ == "__main__":
    unittest.main()
