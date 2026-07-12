from __future__ import annotations

import unittest

from minimal_predictive_lm.phase12a_experiment import (
    calibration_interactions,
    synthetic_examples,
)
from minimal_predictive_lm.phase17a_resource_scaling import validation_interactions
from minimal_predictive_lm.phase17c_factorial_resource_scaling import (
    ANCHOR,
    AXIS_SWEEPS,
    FACTORIAL_POINTS,
    FactorialBudget,
    induce_globally_budgeted_model,
    run_point,
)


class Phase17cFactorialResourceScalingTests(unittest.TestCase):
    def test_global_induction_budget_is_strict(self) -> None:
        rows = calibration_interactions()
        for candidate_budget in (0, 1, 500, 5_000):
            with self.subTest(candidate_budget=candidate_budget):
                model, unresolved, _ = induce_globally_budgeted_model(
                    rows,
                    global_candidate_budget=candidate_budget,
                    per_fit_ceiling=max(1, candidate_budget),
                )
                self.assertLessEqual(
                    model.candidate_evaluations,
                    candidate_budget,
                )
                self.assertGreaterEqual(unresolved, 0)
                self.assertLessEqual(unresolved, len(rows))

    def test_anchor_point_is_bounded_and_non_degenerate(self) -> None:
        row = run_point(
            ANCHOR,
            seed=17,
            training=calibration_interactions(),
            validation=validation_interactions(),
            blind_examples=synthetic_examples(),
        )
        self.assertLessEqual(
            row["training_evidence_bits"],
            ANCHOR.evidence_bits,
        )
        self.assertLessEqual(
            row["candidate_evaluations"],
            ANCHOR.induction_evaluations,
        )
        self.assertLessEqual(
            row["acquired_model_bits"],
            ANCHOR.acquired_bits,
        )
        self.assertGreater(row["selected_rules"], 0)
        self.assertGreater(row["answered"], 0)

    def test_low_global_search_point_remains_safe(self) -> None:
        budget = FactorialBudget(
            "test-low-search",
            "induction_evaluations",
            ANCHOR.acquired_bits,
            ANCHOR.evidence_bits,
            8,
            ANCHOR.inference_operations_per_item,
            8,
        )
        row = run_point(
            budget,
            seed=29,
            training=calibration_interactions(),
            validation=validation_interactions(),
            blind_examples=synthetic_examples(),
        )
        self.assertLessEqual(row["candidate_evaluations"], 8)
        self.assertLessEqual(row["correct"], row["answered"])
        self.assertLessEqual(row["answered"], row["examples"])

    def test_factorial_sweeps_share_one_anchor(self) -> None:
        names = {point.name for point in FACTORIAL_POINTS}
        self.assertIn("anchor", names)
        for axis, sweep_names in AXIS_SWEEPS.items():
            with self.subTest(axis=axis):
                self.assertEqual(sweep_names[-1], "anchor")
                self.assertTrue(set(sweep_names).issubset(names))


if __name__ == "__main__":
    unittest.main()
