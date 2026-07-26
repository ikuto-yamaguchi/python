#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit_artifact_path_containment.py")
spec = importlib.util.spec_from_file_location("audit_artifact_path_containment", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ArtifactPathContainmentTests(unittest.TestCase):
    def _bundle(self, root: Path) -> dict:
        for name in ("model.bin", "data.jsonl", "raw.log", "predictions.jsonl", "statistics.json"):
            (root / name).write_bytes(b"evidence\n")
        return {
            "statistics_path": "statistics.json",
            "runs": [
                {
                    "model_path": "model.bin",
                    "data_path": "data.jsonl",
                    "raw_log_path": "raw.log",
                    "predictions_path": "predictions.jsonl",
                }
            ],
        }

    def test_clean_self_contained_bundle_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = module.audit(self._bundle(root), root)
            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(result["classification"], "qualified")

    def test_absolute_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            manifest = self._bundle(root)
            external = Path(outside) / "model.bin"
            external.write_bytes(b"external\n")
            manifest["runs"][0]["model_path"] = str(external)
            result = module.audit(manifest, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("absolute artifact paths" in error for error in result["errors"]))
            self.assertEqual(result["classification"], "initial_reproduction_failure")

    def test_parent_directory_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "bundle"
            root.mkdir()
            manifest = self._bundle(root)
            (parent / "outside.log").write_bytes(b"outside\n")
            manifest["runs"][0]["raw_log_path"] = "../outside.log"
            result = module.audit(manifest, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("parent-directory components" in error for error in result["errors"]))
            self.assertTrue(any("escapes bundle root" in error for error in result["errors"]))

    def test_symlink_to_external_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            manifest = self._bundle(root)
            external = Path(outside) / "model.bin"
            external.write_bytes(b"external\n")
            link = root / "linked-model.bin"
            try:
                link.symlink_to(external)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable")
            manifest["runs"][0]["model_path"] = link.name
            result = module.audit(manifest, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("symlink traversal" in error for error in result["errors"]))

    def test_empty_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._bundle(root)
            (root / "statistics.json").write_bytes(b"")
            result = module.audit(manifest, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("artifact is empty" in error for error in result["errors"]))

    def test_manifest_without_paths_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = module.audit({"runs": []}, Path(tmp))
            self.assertFalse(result["valid"])
            self.assertTrue(any("no auditable artifact" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
