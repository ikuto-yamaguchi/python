#!/usr/bin/env python3
from __future__ import annotations

import unittest

from audit_canonical_split_identity import audit_payload, audit_split_rows, canonical_split


class CanonicalSplitIdentityAuditTests(unittest.TestCase):
    def test_canonical_split_collapses_unicode_and_invisible_aliases(self) -> None:
        self.assertEqual(canonical_split("ＴＥＳＴ"), "test")
        self.assertEqual(canonical_split("te\u200bst"), "test")
        self.assertEqual(canonical_split(" validation \n"), "validation")

    def test_exact_canonical_dataset_split_passes(self) -> None:
        result = audit_split_rows([
            {"split": "train"},
            {"split": "test"},
            {"split": "validation"},
        ])
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["classification"], "reproduced")

    def test_fullwidth_and_invisible_aliases_fail_closed(self) -> None:
        for raw in ("ＴＲＡＩＮ", "te\u200bst", " validation "):
            with self.subTest(raw=raw):
                result = audit_split_rows([{"split": raw}])
                self.assertFalse(result["valid"])
                self.assertEqual(result["classification"], "initial_reproduction_failure")
                self.assertTrue(any("exact canonical spelling" in error for error in result["errors"]))

    def test_alias_collision_is_saved(self) -> None:
        result = audit_split_rows([{"split": "test"}, {"split": "ＴＥＳＴ"}])
        self.assertFalse(result["valid"])
        self.assertEqual(result["split_label_collisions"], {"test": ["test", "ＴＥＳＴ"]})

    def test_empty_after_canonicalization_fails(self) -> None:
        result = audit_split_rows([{"split": "\u200b \n"}])
        self.assertFalse(result["valid"])
        self.assertTrue(any("non-empty after canonicalization" in error for error in result["errors"]))

    def test_resource_manifest_is_evaluation_only(self) -> None:
        accepted = audit_payload({"runs": [{"split": "test"}]})
        rejected_train = audit_payload({"runs": [{"split": "train"}]})
        rejected_alias = audit_payload({"runs": [{"split": "ＴＥＳＴ"}]})
        self.assertTrue(accepted["valid"], accepted["errors"])
        self.assertFalse(rejected_train["valid"])
        self.assertFalse(rejected_alias["valid"])


if __name__ == "__main__":
    unittest.main()
