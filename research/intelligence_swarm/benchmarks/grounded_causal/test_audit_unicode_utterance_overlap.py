#!/usr/bin/env python3
from __future__ import annotations

import unittest

import audit_unicode_utterance_overlap as target


class UnicodeUtteranceOverlapAuditTest(unittest.TestCase):
    def rows(self, train: object, test: object) -> list[dict[str, object]]:
        return [
            {"instance_id": "train-1", "split": "train", "utterance": train},
            {"instance_id": "test-1", "split": "test", "utterance": test},
        ]

    def test_distinct_utterances_pass(self) -> None:
        result = target.audit(self.rows("take red key", "take blue key"))
        self.assertTrue(result["valid"], result)

    def test_full_width_alias_fails(self) -> None:
        result = target.audit(self.rows("ＴＡＫＥ　ＲＥＤ", "take red"))
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")

    def test_combining_character_alias_fails(self) -> None:
        result = target.audit(self.rows("café", "cafe\u0301"))
        self.assertFalse(result["valid"])

    def test_zero_width_alias_fails(self) -> None:
        result = target.audit(self.rows("open door", "open\u200bdoor"))
        self.assertFalse(result["valid"])

    def test_token_sequence_overlap_fails(self) -> None:
        result = target.audit(self.rows([1, 2, 3], (1, 2, 3)))
        self.assertFalse(result["valid"])

    def test_missing_utterance_fails(self) -> None:
        result = target.audit([{"instance_id": "x", "split": "train"}])
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
