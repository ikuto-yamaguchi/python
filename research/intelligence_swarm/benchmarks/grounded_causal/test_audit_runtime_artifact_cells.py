#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from audit_runtime_artifact_cells import CANONICAL_SEEDS, REQUIRED_METHODS, audit


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RuntimeArtifactCellAuditTests(unittest.TestCase):
    def _bundle(self, root: Path):
        data = root / "data.jsonl"
        data.write_text("{}\n", encoding="utf-8")
        rows = []
        for method_index, method in enumerate(sorted(REQUIRED_METHODS)):
            for seed in sorted(CANONICAL_SEEDS):
                pred = root / f"pred-{method}-{seed}.jsonl"
                log = root / f"log-{method}-{seed}.txt"
                pred.write_text(f'{{"method":"{method}","seed":{seed}}}\n', encoding="utf-8")
                log.write_text(f"method={method} seed={seed}\n", encoding="utf-8")
                row = {
                    "method": method,
                    "seed": seed,
                    "domain": "rtfm",
                    "split": "test",
                    "condition": "in_distribution",
                    "prediction_path": pred.name,
                    "prediction_sha256": sha(pred),
                    "data_path": data.name,
                    "data_sha256": sha(data),
                    "raw_log_path": log.name,
                    "raw_log_sha256": sha(log),
                    "code_commit": f"{seed + method_index:040x}"[-40:],
                    "peak_rss_bytes": 100_000_000 + seed + method_index,
                    "training_wall_seconds": 0 if method == "random" else 10 + seed + method_index,
                    "cpu_inference_ms_per_item": 0.1 + seed / 1000 + method_index / 100,
                }
                if method != "random":
                    model = root / f"model-{method}-{seed}.bin"
                    model.write_bytes((method + str(seed)).encode())
                    row.update({
                        "model_path": model.name,
                        "model_sha256": sha(model),
                        "model_bytes": model.stat().st_size,
                    })
                rows.append(row)
        return rows

    def test_complete_three_seed_bundle_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = audit(self._bundle(root), root)
            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(result["classification"], "audited")

    def test_checksum_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = self._bundle(root)
            (root / rows[0]["prediction_path"]).write_text("changed\n", encoding="utf-8")
            result = audit(rows, root)
            self.assertFalse(result["valid"])
            self.assertEqual(result["classification"], "initial_reproduction_failure")
            self.assertTrue(any("checksum mismatch" in error for error in result["errors"]))

    def test_missing_seed_cell_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = self._bundle(root)
            rows = [row for row in rows if not (row["method"] == "state_only" and row["seed"] == 19)]
            result = audit(rows, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("cell coverage differs" in error for error in result["errors"]))

    def test_checkpoint_switch_across_conditions_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = self._bundle(root)
            base = next(row for row in rows if row["method"] == "correct" and row["seed"] == 1)
            second = dict(base)
            second["condition"] = "entity_holdout"
            model = root / "alternate-model.bin"
            model.write_bytes(b"alternate")
            second["model_path"] = model.name
            second["model_sha256"] = sha(model)
            second["model_bytes"] = model.stat().st_size
            pred = root / "alternate-pred.jsonl"
            pred.write_text("{}\n", encoding="utf-8")
            second["prediction_path"] = pred.name
            second["prediction_sha256"] = sha(pred)
            rows.append(second)
            result = audit(rows, root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("checkpoint changes" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
