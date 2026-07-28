#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from build_r02_preregistered_holdout_manifest import build_manifest


class BuildR02PreregisteredHoldoutManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.metadata_path = root / "metadata.jsonl"
        self.spec_path = root / "spec.json"
        self.metadata_path.write_text("{}\n", encoding="utf-8")
        self.spec_path.write_text("{}\n", encoding="utf-8")

    @staticmethod
    def row(split: str, seed: int, suffix: str) -> dict:
        return {
            "domain": "silg:rtfm_test_s1-v0" if split == "test" else "silg:rtfm_train_s1-v0",
            "split": split,
            "seed": seed,
            "episode_seed": seed * 1_000_003 + int(suffix),
            "entity_signature": f"entity-{suffix}",
            "dynamics_signature": f"dynamics-{suffix}",
            "language_form_signature": f"language-{suffix}",
        }

    @staticmethod
    def spec() -> dict:
        return {
            "version": 1,
            "entity_holdout": ["entity-9"],
            "dynamics_holdout": ["dynamics-9"],
            "language_holdout": ["language-9"],
        }

    def test_builds_three_seed_manifest_without_outcome_fields(self) -> None:
        rows = []
        for seed in (1, 7, 19):
            rows.extend([self.row("train", seed, "1"), self.row("test", seed, "9")])
        manifest, summary = build_manifest(rows, self.spec(), self.metadata_path, self.spec_path)
        held_out = [row for row in manifest if row["entity_holdout"]]
        self.assertEqual(len(held_out), 3)
        self.assertEqual(summary["held_out_seed_coverage"]["entity_holdout"], [1, 7, 19])
        self.assertTrue(all(not row["entity_holdout"] for row in manifest if row["split"] == "train"))

    def test_rejects_model_or_outcome_fields(self) -> None:
        rows = [self.row("test", seed, "9") for seed in (1, 7, 19)]
        rows[0]["task_success"] = 1.0
        with self.assertRaisesRegex(ValueError, "outcome/model fields forbidden"):
            build_manifest(rows, self.spec(), self.metadata_path, self.spec_path)

    def test_rejects_absent_preregistered_signature(self) -> None:
        rows = [self.row("test", seed, "8") for seed in (1, 7, 19)]
        with self.assertRaisesRegex(ValueError, "absent from test metadata"):
            build_manifest(rows, self.spec(), self.metadata_path, self.spec_path)

    def test_rejects_holdout_missing_one_seed(self) -> None:
        rows = [self.row("test", 1, "9"), self.row("test", 7, "9"), self.row("test", 19, "8")]
        spec = self.spec()
        spec["entity_holdout"] = ["entity-9", "entity-8"]
        spec["dynamics_holdout"] = ["dynamics-9", "dynamics-8"]
        spec["language_holdout"] = ["language-9"]
        with self.assertRaisesRegex(ValueError, "language_holdout lacks canonical seed coverage"):
            build_manifest(rows, spec, self.metadata_path, self.spec_path)

    def test_duplicate_episode_metadata_is_rejected(self) -> None:
        item = self.row("test", 1, "9")
        with self.assertRaisesRegex(ValueError, "duplicate episode metadata key"):
            build_manifest([item, dict(item)], self.spec(), self.metadata_path, self.spec_path)


if __name__ == "__main__":
    unittest.main()
