from __future__ import annotations

from dataclasses import replace
import unittest

from minimal_predictive_lm.phase18b3_affine_equation_solving import (
    EquationSolution,
    calibration_problems,
    counterfactual_observation_sensitivity,
    fit_machine,
    heldout_problems,
    invalid_equations_abstain,
    memorizer_coverage,
    observed_value_baseline_accuracy,
    run,
    tampered_trace_rejected,
    verify_solution,
)


class Phase18b3AffineEquationTests(unittest.TestCase):
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

    def test_exact_negative_and_rational_solutions_verify(self) -> None:
        for solution, (problem, expected) in zip(
            self.solutions,
            self.heldout,
        ):
            self.assertIsNotNone(solution)
            self.assertEqual(solution.answer, expected)
            self.assertTrue(
                verify_solution(
                    problem,
                    solution,
                    self.machine.arithmetic,
                )
            )

    def test_empty_tampered_and_wrong_solution_traces_are_rejected(self) -> None:
        for solution, (problem, _) in zip(
            self.solutions,
            self.heldout,
        ):
            self.assertIsNotNone(solution)
            self.assertFalse(
                verify_solution(
                    problem,
                    EquationSolution(solution.answer, ()),
                    self.machine.arithmetic,
                )
            )
            self.assertTrue(
                tampered_trace_rejected(
                    problem,
                    solution,
                    self.machine.arithmetic,
                )
            )
            self.assertFalse(
                verify_solution(
                    problem,
                    replace(solution, answer=solution.answer + 1),
                    self.machine.arithmetic,
                )
            )

    def test_memorizer_and_observed_value_baselines_fail(self) -> None:
        self.assertEqual(
            memorizer_coverage(self.calibration, self.heldout),
            0.0,
        )
        self.assertLess(
            observed_value_baseline_accuracy(self.heldout),
            0.5,
        )

    def test_observation_counterfactual_changes_the_solution(self) -> None:
        self.assertEqual(
            counterfactual_observation_sensitivity(self.machine),
            1.0,
        )

    def test_nonunique_or_invalid_equations_abstain(self) -> None:
        controls = invalid_equations_abstain(self.machine)
        self.assertTrue(all(controls.values()), controls)

    def test_claim_boundary_remains_strict(self) -> None:
        boundary = run()["claim_boundary"]
        self.assertTrue(boundary["controlled_affine_equation_solving"])
        self.assertFalse(boundary["natural_word_problems"])
        self.assertFalse(boundary["general_algebra"])
        self.assertFalse(boundary["high_school_mathematics"])
        self.assertFalse(boundary["high_school_intelligence"])


if __name__ == "__main__":
    unittest.main()
