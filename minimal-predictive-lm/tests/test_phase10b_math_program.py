from __future__ import annotations

from fractions import Fraction
import unittest

from minimal_predictive_lm.minimal_math_program import (
    MathTrace,
    induce_math_grounder,
    infer_program,
)
from minimal_predictive_lm.phase10b_experiment import TRAINING, run


class Phase10bMathProgramTests(unittest.TestCase):
    def test_program_is_inferred_from_answer_not_given_label(self) -> None:
        self.assertEqual(infer_program(MathTrace("17から5を引く", Fraction(12))), "SUB")
        self.assertEqual(infer_program(MathTrace("200の15%", Fraction(30))), "PERCENT_OF")

    def test_unseen_numbers_use_same_small_program(self) -> None:
        grounder = induce_math_grounder(TRAINING)
        result = grounder.predict("125の24%を求めて")
        self.assertEqual(result.program, "PERCENT_OF")
        self.assertEqual(result.answer, Fraction(30))

    def test_phase10b_results_and_stage_c_gate(self) -> None:
        payload = run()
        self.assertEqual(payload["heldout"]["exact_surface_accuracy"], 0.0)
        self.assertEqual(payload["heldout"]["program_accuracy"], 1.0)
        self.assertEqual(payload["numeric_generalization"]["accuracy"], 1.0)
        self.assertLess(payload["lexical_shift"]["accuracy_before"], 0.5)
        self.assertEqual(payload["lexical_shift"]["accuracy_after"], 1.0)
        self.assertFalse(payload["stage_c_after_math"]["stage_c_ready"])
        self.assertEqual(payload["stage_c_after_math"]["points"], 7)


if __name__ == "__main__":
    unittest.main()
