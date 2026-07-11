from __future__ import annotations

import json
import unittest

from minimal_predictive_lm.minimal_math_program import induce_math_grounder
from minimal_predictive_lm.phase10h_worker import ENGLISH_CALIBRATION
from minimal_predictive_lm.public_benchmarks import parse_bigbench_arithmetic_task


class BigBenchArithmeticTests(unittest.TestCase):
    def test_english_operator_grounding_generalizes_numbers(self) -> None:
        grounder = induce_math_grounder(ENGLISH_CALIBRATION)
        cases = {
            "What is 132 plus 762?": 894,
            "What is 76 minus 23?": 53,
            "What is 11 times 11?": 121,
            "What is 27 divided by 9?": 3,
        }
        for prompt, expected in cases.items():
            with self.subTest(prompt=prompt):
                self.assertEqual(grounder.predict(prompt).answer, expected)

    def test_bigbench_parser_preserves_public_examples(self) -> None:
        payload = json.dumps(
            {
                "name": "1_digit_addition",
                "examples": [
                    {"input": "What is 0 plus 0?", "target": "0"},
                    {"input": "What is 0 plus 1?", "target": "1"},
                ],
            }
        ).encode("utf-8")
        examples = parse_bigbench_arithmetic_task(
            payload,
            task_name="1_digit_addition",
            limit=2,
        )
        self.assertEqual([item.prompt for item in examples], ["What is 0 plus 0?", "What is 0 plus 1?"])
        self.assertEqual([item.target for item in examples], ["0", "1"])


if __name__ == "__main__":
    unittest.main()
