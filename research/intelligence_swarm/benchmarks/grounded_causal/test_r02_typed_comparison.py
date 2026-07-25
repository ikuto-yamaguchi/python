#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "r02_typed_comparison.py"


class TypedComparisonTest(unittest.TestCase):
    def make_rows(self, seed: int) -> list[dict]:
        schema = [
            {"name": "entity", "kind": "categorical", "shape": [1], "cardinality": 4},
            {"name": "valid", "kind": "binary", "shape": [2], "cardinality": None},
            {"name": "position", "kind": "continuous", "shape": [2], "cardinality": None},
        ]
        rows = []
        for split, count in (("train", 12), ("test", 6)):
            for index in range(count):
                entity = index % 4
                action = index % 2
                rows.append(
                    {
                        "instance_id": f"{split}-{index}",
                        "episode_id": f"{split}-episode-{index // 2}",
                        "episode_seed": seed,
                        "split": split,
                        "text_tokens": [1 + entity, 5 + action],
                        "action": action,
                        "state_schema": schema,
                        "state_before_fields": {
                            "entity": [entity],
                            "valid": [1, action],
                            "position": [float(index), 0.0],
                        },
                        "state_after_fields": {
                            "entity": [(entity + action) % 4],
                            "valid": [1, action],
                            "position": [float(index + action), 0.0],
                        },
                        "entity_holdout": split == "test" and index < 2,
                        "dynamics_holdout": split == "test" and 2 <= index < 4,
                        "language_holdout": split == "test" and index >= 4,
                        "task_success": split == "test" and index % 2 == 0,
                    }
                )
        return rows

    def test_comparison_writes_matched_metrics_and_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data = tmp_path / "typed.jsonl"
            out = tmp_path / "result.json"
            data.write_text("".join(json.dumps(row) + "\n" for row in self.make_rows(1)))
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--data",
                    str(data),
                    "--out",
                    str(out),
                    "--seed",
                    "1",
                    "--env-epochs",
                    "1",
                    "--lang-epochs",
                    "1",
                ],
                check=True,
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )
            result = json.loads(out.read_text())
            self.assertTrue(result["parameter_budget"]["equal"])
            self.assertEqual(
                result["parameter_budget"]["environment_first_inference_bytes"],
                result["parameter_budget"]["end_to_end_inference_bytes"],
            )
            self.assertEqual(
                {item["method"] for item in result["evaluations"]},
                {"environment_first", "end_to_end", "state_only"},
            )
            for evaluation in result["evaluations"]:
                self.assertEqual(evaluation["conditions"]["all"]["n"], 6)
                self.assertEqual(evaluation["conditions"]["entity_holdout"]["n"], 2)
                self.assertEqual(evaluation["conditions"]["dynamics_holdout"]["n"], 2)
                self.assertEqual(evaluation["conditions"]["language_holdout"]["n"], 2)
                self.assertIsNotNone(evaluation["conditions"]["all"]["action_accuracy"])
                self.assertIsNotNone(evaluation["conditions"]["all"]["typed_next_state_loss"])
                self.assertIsNotNone(evaluation["conditions"]["all"]["task_success"])
                self.assertGreater(evaluation["cpu_inference_ms_per_instance_mean"], 0)
            for checkpoint in result["checkpoints"].values():
                self.assertTrue(Path(checkpoint["path"]).is_file())
                self.assertGreater(checkpoint["bytes"], 0)
                self.assertEqual(len(checkpoint["sha256"]), 64)

    def test_wrong_seed_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data = tmp_path / "typed.jsonl"
            out = tmp_path / "result.json"
            data.write_text("".join(json.dumps(row) + "\n" for row in self.make_rows(7)))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--data",
                    str(data),
                    "--out",
                    str(out),
                    "--seed",
                    "1",
                    "--env-epochs",
                    "1",
                    "--lang-epochs",
                    "1",
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("dataset seed mismatch", completed.stderr)


if __name__ == "__main__":
    unittest.main()
