from __future__ import annotations

import hashlib
import json
import unittest

from minimal_predictive_lm.public_benchmarks import git_blob_sha1, parse_gsm8k_test


class PublicBenchmarkTests(unittest.TestCase):
    def test_git_blob_hash_matches_git_encoding(self) -> None:
        payload = b"public benchmark\n"
        expected = hashlib.sha1(
            f"blob {len(payload)}\0".encode("ascii") + payload
        ).hexdigest()
        self.assertEqual(git_blob_sha1(payload), expected)

    def test_gsm8k_parser_extracts_only_final_answer(self) -> None:
        payload = (
            json.dumps(
                {
                    "question": "A has 2 and gets 3. How many?",
                    "answer": "First 2+3=5.\n#### 5",
                }
            )
            + "\n"
            + json.dumps(
                {
                    "question": "A value is one half.",
                    "answer": "The result is 1/2.\n#### 1/2",
                }
            )
            + "\n"
        ).encode("utf-8")
        examples = parse_gsm8k_test(payload, limit=2)
        self.assertEqual(len(examples), 2)
        self.assertEqual(examples[0].target, "5")
        self.assertEqual(examples[1].target, "1/2")
        self.assertEqual(examples[0].answer_type, "numeric")


if __name__ == "__main__":
    unittest.main()
