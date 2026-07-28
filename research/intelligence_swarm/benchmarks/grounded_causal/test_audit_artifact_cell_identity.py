#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "audit_artifact_cell_identity", HERE / "audit_artifact_cell_identity.py"
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

METHODS = sorted(mod.REQUIRED_METHODS)


def manifest() -> dict:
    runs = []
    for seed in sorted(mod.CANONICAL_SEEDS):
        for condition in ("in_distribution", "dynamics_holdout"):
            for method in METHODS:
                runs.append(
                    {
                        "method": method,
                        "seed": seed,
                        "domain": "rtfm_s1",
                        "split": "test",
                        "condition": condition,
                        "data_path": f"data/{seed}-{condition}.jsonl",
                        "data_sha256": ("a" if condition == "in_distribution" else "b") * 64,
                        "code_commit": "c" * 40,
                    }
                )
    return {"runs": runs}


class Tests(unittest.TestCase):
    def test_valid_matched_bundle(self):
        result = mod.audit(manifest())
        self.assertTrue(result["valid"], result["errors"])
        self.assertTrue(result["same_dataset_per_cell_required"])
        self.assertTrue(result["single_code_commit_required"])

    def test_rejects_method_specific_dataset_hash(self):
        value = manifest()
        row = next(
            run
            for run in value["runs"]
            if run["seed"] == 7
            and run["condition"] == "dynamics_holdout"
            and run["method"] == "state_only"
        )
        row["data_sha256"] = "d" * 64
        result = mod.audit(value)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertTrue(any("different data_sha256" in error for error in result["errors"]))

    def test_rejects_method_specific_dataset_path(self):
        value = manifest()
        value["runs"][0]["data_path"] = "data/private-copy.jsonl"
        result = mod.audit(value)
        self.assertFalse(result["valid"])
        self.assertTrue(any("different data_path" in error for error in result["errors"]))

    def test_rejects_mixed_code_commits(self):
        value = manifest()
        value["runs"][-1]["code_commit"] = "e" * 40
        result = mod.audit(value)
        self.assertFalse(result["valid"])
        self.assertTrue(any("exactly one code_commit" in error for error in result["errors"]))

    def test_rejects_missing_method_in_one_cell(self):
        value = manifest()
        value["runs"] = [
            run
            for run in value["runs"]
            if not (
                run["seed"] == 19
                and run["condition"] == "dynamics_holdout"
                and run["method"] == "outcome_shuffle"
            )
        ]
        result = mod.audit(value)
        self.assertFalse(result["valid"])
        self.assertTrue(any("methods must be exactly" in error for error in result["errors"]))

    def test_rejects_extra_method(self):
        value = manifest()
        extra = dict(value["runs"][0])
        extra["method"] = "unregistered_method"
        value["runs"].append(extra)
        result = mod.audit(value)
        self.assertFalse(result["valid"])
        self.assertTrue(any("bundle methods must be exactly" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
