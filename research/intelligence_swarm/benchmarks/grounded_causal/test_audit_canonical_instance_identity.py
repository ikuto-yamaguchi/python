#!/usr/bin/env python3
from __future__ import annotations

import unittest

from audit_canonical_instance_identity import audit


class CanonicalInstanceIdentityAuditTests(unittest.TestCase):
    def test_distinct_ids_pass(self) -> None:
        result = audit([{"instance_id": "episode-1"}, {"instance_id": "episode-2"}])
        self.assertTrue(result["valid"])
        self.assertEqual(result["collisions"], {})

    def test_unicode_width_case_alias_fails(self) -> None:
        result = audit([{"instance_id": "Episode-1"}, {"instance_id": "ＥＰＩＳＯＤＥ－１"}])
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertTrue(result["collisions"])

    def test_whitespace_and_format_alias_fails(self) -> None:
        result = audit([{"instance_id": "trial 7"}, {"instance_id": "trial\u200b7"}])
        self.assertFalse(result["valid"])

    def test_empty_after_normalization_fails(self) -> None:
        result = audit([{"instance_id": "\u200b \t"}])
        self.assertFalse(result["valid"])

    def test_prediction_alias_must_not_resolve_silently(self) -> None:
        result = audit(
            [{"instance_id": "eval-1"}],
            [{"instance_id": "ＥＶＡＬ－１", "method": "correct"}],
        )
        self.assertFalse(result["valid"])
        self.assertIn("non-exact alias", "\n".join(result["errors"]))

    def test_exact_prediction_id_passes(self) -> None:
        result = audit(
            [{"instance_id": "eval-1"}],
            [{"instance_id": "eval-1", "method": "correct"}],
        )
        self.assertTrue(result["valid"])


if __name__ == "__main__":
    unittest.main()
