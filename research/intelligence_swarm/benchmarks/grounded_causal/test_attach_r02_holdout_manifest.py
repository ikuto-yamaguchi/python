#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from attach_r02_holdout_manifest import attach


class AttachHoldoutManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.manifest_path = Path(self.tmp.name) / "manifest.jsonl"
        self.manifest_path.write_text("{}\n", encoding="utf-8")

    @staticmethod
    def trajectory(split: str, seed: int, episode_seed: int, step: int = 0) -> dict:
        return {
            "instance_id": f"{split}-{seed}-{episode_seed}-{step}",
            "episode_id": f"{split}-{seed}-{episode_seed}",
            "domain": "silg:rtfm_test_s1-v0" if split == "test" else "silg:rtfm_train_s1-v0",
            "split": split,
            "seed": seed,
            "episode_seed": episode_seed,
            "entity_holdout": False,
            "dynamics_holdout": False,
            "language_holdout": split == "test",
        }

    @staticmethod
    def manifest(row: dict, *, entity: bool = False, dynamics: bool = False, language: bool = False) -> dict:
        return {
            "domain": row["domain"],
            "split": row["split"],
            "seed": row["seed"],
            "episode_seed": row["episode_seed"],
            "entity_signature": f"entity-{row['episode_seed']}",
            "dynamics_signature": f"dynamics-{row['episode_seed']}",
            "language_form_signature": f"language-{row['episode_seed']}",
            "entity_holdout": entity,
            "dynamics_holdout": dynamics,
            "language_holdout": language,
        }

    def test_exact_episode_join_overwrites_placeholders(self) -> None:
        train = self.trajectory("train", 1, 100)
        test = self.trajectory("test", 1, 200)
        rows, summary = attach(
            [train, test, dict(test, instance_id="test-step-1")],
            [self.manifest(train), self.manifest(test, entity=True, language=True)],
            self.manifest_path,
        )
        self.assertEqual(summary["episodes"], 2)
        self.assertTrue(rows[1]["entity_holdout"])
        self.assertTrue(rows[2]["entity_holdout"])
        self.assertTrue(rows[1]["language_holdout"])
        self.assertIn("holdout_manifest_sha256", rows[0])

    def test_missing_episode_assignment_is_rejected(self) -> None:
        train = self.trajectory("train", 1, 100)
        test = self.trajectory("test", 1, 200)
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            attach([train, test], [self.manifest(train)], self.manifest_path)

    def test_train_holdout_is_rejected(self) -> None:
        train = self.trajectory("train", 1, 100)
        with self.assertRaisesRegex(ValueError, "train episodes cannot be marked held out"):
            attach([train], [self.manifest(train, dynamics=True)], self.manifest_path)

    def test_duplicate_manifest_key_is_rejected(self) -> None:
        test = self.trajectory("test", 7, 200)
        item = self.manifest(test, language=True)
        with self.assertRaisesRegex(ValueError, "duplicate manifest key"):
            attach([test], [item, dict(item)], self.manifest_path)


if __name__ == "__main__":
    unittest.main()
