#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit_artifact_eval_split_scope.py")
SPEC = importlib.util.spec_from_file_location("audit_artifact_eval_split_scope", MODULE_PATH)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)

METHODS = {
    "correct",
    "random",
    "language_blind",
    "state_only",
    "target_label_shuffle",
    "outcome_shuffle",
}
SEEDS = {1, 7, 19}


def manifest(split: str = "test") -> dict:
    return {
        "runs": [
            {
                "method": method,
                "seed": seed,
                "domain": "rtfm",
                "split": split,
                "condition": "in_distribution",
            }
            for method in sorted(METHODS)
            for seed in sorted(SEEDS)
        ]
    }


class ArtifactEvalSplitScopeTest(unittest.TestCase):
    def test_registered_test_split_passes(self) -> None:
        result = AUDIT.audit(manifest("test"))
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["classification"], "reproduced")

    def test_registered_validation_alias_passes(self) -> None:
        result = AUDIT.audit(manifest("VALIDATION"))
        self.assertTrue(result["valid"], result["errors"])

    def test_train_resource_cell_fails_closed(self) -> None:
        result = AUDIT.audit(manifest("train"))
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertTrue(any("not a registered evaluation split" in error for error in result["errors"]))

    def test_debug_resource_cell_fails_closed(self) -> None:
        result = AUDIT.audit(manifest("debug"))
        self.assertFalse(result["valid"])
        self.assertTrue(result["unregistered_resource_cells_forbidden"])

    def test_posthoc_resource_cell_fails_closed(self) -> None:
        result = AUDIT.audit(manifest("posthoc"))
        self.assertFalse(result["valid"])

    def test_missing_split_fails_closed(self) -> None:
        data = manifest("test")
        del data["runs"][0]["split"]
        result = AUDIT.audit(data)
        self.assertFalse(result["valid"])
        self.assertTrue(any("split must be non-empty" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
