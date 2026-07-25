#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from audit_gaddy_klein_component_mapping import audit


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
MANIFEST = HERE / "GADDY_KLEIN_SILG_COMPONENT_MAPPING.json"


class ComponentMappingAuditTest(unittest.TestCase):
    def test_canonical_mapping_passes(self) -> None:
        result = audit(MANIFEST, REPO_ROOT)
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertEqual(result["component_count"], 10)
        self.assertFalse(result["new_architecture"])
        self.assertFalse(result["capability_progress_claimed"])

    def test_missing_local_symbol_fails_closed(self) -> None:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        broken = copy.deepcopy(payload)
        broken["components"][0]["local_symbols"].append("InventedToyMechanism")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(broken), encoding="utf-8")
            result = audit(path, REPO_ROOT)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertTrue(any("InventedToyMechanism" in error for error in result["errors"]))

    def test_public_revision_drift_fails_closed(self) -> None:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        payload["public_reference"]["commit"] = "0" * 40
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = audit(path, REPO_ROOT)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("unexpected public reference commit" in error for error in result["errors"]))

    def test_fake_holdout_claim_fails_closed(self) -> None:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        payload["fixed_method_properties"]["formal_rtfm_s1_holdouts"]["entity"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = audit(path, REPO_ROOT)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("holdout declaration changed" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
