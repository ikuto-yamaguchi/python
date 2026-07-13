from __future__ import annotations

from dataclasses import replace
import unittest

from minimal_predictive_lm.phase18b1_text_qa_verified_trace import Solution
from minimal_predictive_lm.phase18b2_induced_integer_operations import (
    TRUE_OPERATIONS,
    ArithmeticQuestionMachine,
    calibration_problems,
    heldout_problems,
    induce,
    no_execution_accuracy,
    nonidentifiability_controls,
    orderless_bound,
    program_memorizer_coverage,
    run,
    tampered_trace_rejected,
    training_observations,
    verify_solution,
)


class Phase18b2InducedIntegerOperationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.training_rows = training_observations()
        cls.model, cls.fit = induce(cls.training_rows)
        cls.machine = ArithmeticQuestionMachine(cls.model)
        cls.calibration = calibration_problems()
        cls.heldout = heldout_problems()
        cls.solutions = tuple(
            cls.machine.solve(problem)
            for problem, _ in cls.heldout
        )

    def test_campaign_passes_every_theorem_gate(self) -> None:
        payload = run()
        failed = [
            name
            for name, passed in payload["theorem_checks"].items()
            if not passed
        ]
        self.assertEqual(failed, [])
        self.assertTrue(payload["all_theorem_checks_pass"])

    def test_operation_mapping_is_uniquely_recovered(self) -> None:
        self.assertEqual(dict(self.model.operations), TRUE_OPERATIONS)
        self.assertEqual(self.fit["candidates"], 6)
        self.assertEqual(self.fit["errors"], 6)
        self.assertIsNotNone(self.fit["second"])
        self.assertGreater(self.fit["second"], self.fit["errors"])

    def test_recursive_arithmetic_answers_and_traces_are_exact(self) -> None:
        for solution, (problem, expected) in zip(
            self.solutions,
            self.heldout,
        ):
            self.assertIsNotNone(solution)
            self.assertEqual(solution.answer, expected)
            self.assertTrue(
                verify_solution(problem, solution, self.model)
            )

    def test_empty_tampered_and_wrong_answer_traces_are_rejected(self) -> None:
        for solution, (problem, _) in zip(
            self.solutions,
            self.heldout,
        ):
            self.assertIsNotNone(solution)
            self.assertFalse(
                verify_solution(
                    problem,
                    Solution(solution.answer, ()),
                    self.model,
                )
            )
            self.assertTrue(
                tampered_trace_rejected(
                    problem,
                    solution,
                    self.model,
                )
            )
            self.assertFalse(
                verify_solution(
                    problem,
                    replace(solution, answer=solution.answer + 1),
                    self.model,
                )
            )

    def test_memorizer_no_execution_and_orderless_baselines_fail(self) -> None:
        self.assertEqual(
            program_memorizer_coverage(
                self.calibration,
                self.heldout,
            ),
            0.0,
        )
        self.assertLess(no_execution_accuracy(self.heldout), 0.5)
        self.assertEqual(orderless_bound(self.model), 0.5)

    def test_degenerate_examples_do_not_identify_operations(self) -> None:
        controls = nonidentifiability_controls()
        self.assertTrue(all(controls.values()), controls)

    def test_claim_boundary_remains_strict(self) -> None:
        boundary = run()["claim_boundary"]
        self.assertTrue(boundary["controlled_recursive_integer_arithmetic"])
        self.assertFalse(boundary["natural_word_problems"])
        self.assertFalse(boundary["algebra"])
        self.assertFalse(boundary["high_school_mathematics"])
        self.assertFalse(boundary["high_school_intelligence"])


if __name__ == "__main__":
    unittest.main()
