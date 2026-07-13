from __future__ import annotations

from dataclasses import replace
import unittest

from minimal_predictive_lm.phase18b1_text_qa_verified_trace import (
    Solution,
    calibration_problems,
    counterfactual_sensitivity_rate,
    fit_machine,
    heldout_problems,
    no_execution_accuracy,
    problem_memorizer_coverage,
    run,
    tampered_trace_is_rejected,
    verify_solution,
)


class Phase18b1TextQuestionAnsweringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.machine = fit_machine()
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

    def test_text_only_answers_are_exact(self) -> None:
        for solution, (_, expected) in zip(self.solutions, self.heldout):
            self.assertIsNotNone(solution)
            self.assertEqual(solution.answer, expected)

    def test_every_trace_is_independently_replayed(self) -> None:
        for solution, (problem, _) in zip(self.solutions, self.heldout):
            self.assertIsNotNone(solution)
            self.assertTrue(
                verify_solution(
                    problem,
                    solution,
                    self.machine.discourse,
                )
            )

    def test_empty_tampered_or_wrong_answer_traces_are_rejected(self) -> None:
        for solution, (problem, _) in zip(self.solutions, self.heldout):
            self.assertIsNotNone(solution)
            self.assertFalse(
                verify_solution(
                    problem,
                    Solution(solution.answer, ()),
                    self.machine.discourse,
                )
            )
            self.assertTrue(
                tampered_trace_is_rejected(
                    problem,
                    solution,
                    self.machine.discourse,
                )
            )
            self.assertFalse(
                verify_solution(
                    problem,
                    replace(solution, answer=solution.answer + 1),
                    self.machine.discourse,
                )
            )

    def test_memorizer_and_no_execution_baselines_fail(self) -> None:
        self.assertEqual(
            problem_memorizer_coverage(
                self.calibration,
                self.heldout,
            ),
            0.0,
        )
        self.assertLess(no_execution_accuracy(self.heldout), 0.5)

    def test_every_problem_has_a_sensitive_counterfactual(self) -> None:
        self.assertEqual(counterfactual_sensitivity_rate(self.machine), 1.0)

    def test_claim_boundary_remains_strict(self) -> None:
        boundary = run()["claim_boundary"]
        self.assertTrue(boundary["controlled_text_only_qa"])
        self.assertTrue(boundary["independently_replayable_derivation"])
        self.assertFalse(boundary["natural_unstructured_word_problems"])
        self.assertFalse(boundary["general_mathematics"])
        self.assertFalse(boundary["high_school_intelligence"])


if __name__ == "__main__":
    unittest.main()
