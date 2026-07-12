from __future__ import annotations

import unittest

from minimal_predictive_lm.aggregate_routing import phase12_prompt_eligibility


class Phase16bAggregateRoutingTests(unittest.TestCase):
    def test_explicit_records_and_compact_arithmetic_are_eligible(self) -> None:
        self.assertTrue(phase12_prompt_eligibility("state_count=40 delta=12").eligible)
        self.assertTrue(phase12_prompt_eligibility("What is 3011 times 31?").eligible)

    def test_long_formal_text_with_isolated_product_number_is_rejected(self) -> None:
        prompt = (
            '"Some football fans admire clubs. An expert of Bayer 04 Leverkusen '
            'is discussed in a long argument."\n'
            "Is the argument, given the explicitly stated premises, deductively valid or invalid?\n"
            "Options:\n- valid\n- invalid"
        )
        decision = phase12_prompt_eligibility(prompt)
        self.assertFalse(decision.eligible)
        self.assertEqual(decision.reason, "multiline_unstructured_text")
        self.assertEqual(decision.number_count, 1)

    def test_single_year_version_or_model_number_is_not_an_argument_program(self) -> None:
        for prompt in (
            "The report was published in 2025.",
            "The deployed version is 8.",
            "The product is Model 04.",
        ):
            with self.subTest(prompt=prompt):
                decision = phase12_prompt_eligibility(prompt)
                self.assertFalse(decision.eligible)
                self.assertEqual(decision.reason, "insufficient_numeric_arguments")

    def test_multiline_text_is_rejected_even_with_two_numbers(self) -> None:
        decision = phase12_prompt_eligibility(
            "The report compares Model 7 and Model 8.\nExplain the conclusion."
        )
        self.assertFalse(decision.eligible)
        self.assertEqual(decision.reason, "multiline_unstructured_text")


if __name__ == "__main__":
    unittest.main()
