from __future__ import annotations

import unittest

from minimal_predictive_lm.mixed_task_learner import MixedTaskModel
from minimal_predictive_lm.phase12a_experiment import calibration_interactions, synthetic_examples
from minimal_predictive_lm.phase17a_resource_scaling import (
    PILOT_BUDGETS,
    consolidate_to_budget,
    evaluate_blind_suite,
    run_budget_point,
    select_training_evidence,
    validation_interactions,
)


class Phase17aResourceScalingTests(unittest.TestCase):
    def test_budget_ladder_is_strictly_increasing(self) -> None:
        self.assertEqual(len(PILOT_BUDGETS), 5)
        for left, right in zip(PILOT_BUDGETS, PILOT_BUDGETS[1:]):
            self.assertLess(left.acquired_bits, right.acquired_bits)
            self.assertLess(left.evidence_bits, right.evidence_bits)
            self.assertLess(left.candidate_cap_per_fit, right.candidate_cap_per_fit + 1)
            self.assertLess(
                left.inference_operations_per_item,
                right.inference_operations_per_item,
            )

    def test_evidence_selection_never_exceeds_budget(self) -> None:
        rows = calibration_interactions()
        for budget in (0, 512, 4_096, 65_536):
            selected, used = select_training_evidence(
                rows,
                evidence_budget_bits=budget,
                seed=17,
            )
            self.assertLessEqual(used, budget)
            self.assertLessEqual(len(selected), len(rows))

    def test_empty_model_respects_inference_abstention(self) -> None:
        model = MixedTaskModel(tuple(), 0, 0)
        score = evaluate_blind_suite(
            model,
            synthetic_examples(),
            operation_cap=1,
        )
        self.assertEqual(score["answered"], 0)
        self.assertEqual(score["correct"], 0)

    def test_consolidation_never_exceeds_size_cap(self) -> None:
        model = MixedTaskModel(tuple(), 0, 0)
        consolidated = consolidate_to_budget(
            model,
            acquired_budget_bits=model.description_bits,
            validation=validation_interactions(),
            operation_cap=32,
        )
        self.assertLessEqual(consolidated.description_bits, model.description_bits)

    def test_small_budget_point_is_fully_accounted(self) -> None:
        budget = PILOT_BUDGETS[0]
        row = run_budget_point(
            budget,
            seed=17,
            training=calibration_interactions(),
            validation=validation_interactions(),
            blind_examples=synthetic_examples(),
        )
        self.assertLessEqual(row.training_evidence_bits, budget.evidence_bits)
        self.assertLessEqual(row.acquired_model_bits, budget.acquired_bits)
        self.assertEqual(row.examples, len(synthetic_examples()))
        self.assertGreaterEqual(row.coverage, 0.0)
        self.assertLessEqual(row.coverage, 1.0)


if __name__ == "__main__":
    unittest.main()
