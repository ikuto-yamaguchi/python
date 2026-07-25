#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("audit_shuffle_payloads", HERE / "audit_shuffle_payloads.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class Tests(unittest.TestCase):
    def dataset(self):
        rows = []
        for seed in (1, 7, 19):
            for index, action in enumerate((0, 1, 2, 3)):
                rows.append({
                    "instance_id": f"i-{seed}-{index}",
                    "domain": "rtfm_s1",
                    "seed": seed,
                    "split": "test",
                    "condition": "entity_holdout",
                    "utterance": [seed, index],
                    "state_before": [index],
                    "gold_action": action,
                    "gold_state_after": [index + 1],
                })
        return rows

    def predictions(self, rows):
        predictions = []
        for method, spec in mod.METHOD_SPECS.items():
            for seed in (1, 7, 19):
                cell = [row for row in rows if row["seed"] == seed]
                for index, target in enumerate(cell):
                    donor = cell[(index + 1) % len(cell)]
                    source = mod._source_value(donor, spec["source_keys"])
                    assert source is not None
                    value_hash = mod.stable_hash({"kind": spec["kind"], "value": source[1]})
                    predictions.append({
                        "instance_id": target["instance_id"],
                        "method": method,
                        "control_source_instance_id": donor["instance_id"],
                        "control_source_fingerprint": mod.instance_fingerprint(donor),
                        "control_source_value_sha256": value_hash,
                        "control_applied_value_sha256": value_hash,
                        "control_transform": spec["transform"],
                    })
        return predictions

    def test_valid_semantic_shuffle(self):
        rows = self.dataset()
        result = mod.audit(rows, self.predictions(rows))
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["classification"], "reproduced")
        self.assertTrue(result["semantic_payload_hash_required"])

    def test_rejects_declared_donor_but_wrong_applied_value(self):
        rows = self.dataset()
        predictions = self.predictions(rows)
        predictions[0]["control_applied_value_sha256"] = "0" * 64
        result = mod.audit(rows, predictions)
        self.assertFalse(result["valid"])
        self.assertTrue(any("applied control value" in error for error in result["errors"]))

    def test_rejects_wrong_method_transform(self):
        rows = self.dataset()
        predictions = self.predictions(rows)
        predictions[0]["control_transform"] = "shuffle_something_else"
        result = mod.audit(rows, predictions)
        self.assertFalse(result["valid"])
        self.assertTrue(any("control_transform" in error for error in result["errors"]))

    def test_rejects_no_value_change_cell(self):
        rows = self.dataset()
        for row in rows:
            row["gold_action"] = 1
            row["gold_state_after"] = [1]
        result = mod.audit(rows, self.predictions(rows))
        self.assertFalse(result["valid"])
        self.assertTrue(any("changes no semantic values" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
