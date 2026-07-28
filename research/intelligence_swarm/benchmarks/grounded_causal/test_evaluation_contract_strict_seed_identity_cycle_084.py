#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).with_name("evaluation_contract.py")
spec = importlib.util.spec_from_file_location("evaluation_contract", MODULE_PATH)
ec = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(ec)


class StrictSeedIdentityTests(unittest.TestCase):
    def test_real_json_integers_are_accepted(self):
        for value in (1, 7, 19):
            self.assertEqual(ec.strict_seed(value), value)

    def test_alias_types_are_rejected(self):
        for value in (True, False, 1.0, 1.9, "1", "１", None):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    ec.strict_seed(value)

    def test_cell_key_uses_strict_seed(self):
        base = {"domain": "RTFM", "split": "test", "condition": "entity_holdout"}
        self.assertEqual(ec._cell_key({**base, "seed": 1})[0], 1)
        for value in (True, 1.0, "1", "１"):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    ec._cell_key({**base, "seed": value})

    def test_dataset_reports_alias_seed_fail_closed(self):
        row = {
            "instance_id": "i1", "domain": "RTFM", "seed": True,
            "split": "train", "condition": "in_distribution",
            "utterance": "go", "state_before": {}, "gold_action": 0,
            "gold_state_after": {},
        }
        audit = ec.validate_dataset([row])
        self.assertFalse(audit["valid"])
        self.assertTrue(any("JSON integer" in error for error in audit["errors"]))
        self.assertTrue(audit.get("strict_seed_identity_required", False))


if __name__ == "__main__":
    unittest.main()
