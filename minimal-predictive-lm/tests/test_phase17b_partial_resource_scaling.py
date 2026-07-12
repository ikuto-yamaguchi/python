from __future__ import annotations

import unittest

from minimal_predictive_lm.phase12a_experiment import calibration_interactions, synthetic_examples
from minimal_predictive_lm.phase17a_resource_scaling import PILOT_BUDGETS, validation_interactions
from minimal_predictive_lm.phase17b_partial_resource_scaling import (
    induce_partial_mixed_task_model,
    run_budget_point,
)


class Phase17bPartialResourceScalingTests(unittest.TestCase):
    def test_partial_induction_keeps_expressible_rules(self) -> None:
        rows = calibration_interactions()
        model, unresolved = induce_partial_mixed_task_model(
            rows,
            max_candidates_per_fit=20_000,
        )
        self.assertGreater(len(model.rules), 0)
        self.assertLess(unresolved, len(rows))
        self.assertGreater(model.candidate_evaluations, 0)

    def test_partial_budget_point_is_non_degenerate_and_bounded(self) -> None:
        budget = PILOT_BUDGETS[-1]
        row = run_budget_point(
            budget,
            seed=17,
            training=calibration_interactions(),
            validation=validation_interactions(),
            blind_examples=synthetic_examples(),
        )
        self.assertLessEqual(row["training_evidence_bits"], budget.evidence_bits)
        self.assertLessEqual(row["acquired_model_bits"], budget.acquired_bits)
        self.assertGreater(row["selected_rules"], 0)
        self.assertGreater(row["answered"], 0)
        self.assertGreater(row["correct"], 0)

    def test_tiny_point_remains_selective(self) -> None:
        budget = PILOT_BUDGETS[0]
        row = run_budget_point(
            budget,
            seed=29,
            training=calibration_interactions(),
            validation=validation_interactions(),
            blind_examples=synthetic_examples(),
        )
        self.assertLessEqual(row["acquired_model_bits"], budget.acquired_bits)
        self.assertLessEqual(row["answered"], row["examples"])
        self.assertLessEqual(row["correct"], row["answered"])


if __name__ == "__main__":
    unittest.main()
