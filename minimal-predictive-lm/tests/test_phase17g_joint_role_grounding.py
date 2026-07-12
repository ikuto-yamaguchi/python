from __future__ import annotations

import unittest

from minimal_predictive_lm.phase17g_joint_role_grounding import (
    distractor_collision_control,
    duplicate_entity_signature_control,
    enumerate_entity_groundings,
    enumerate_joint_models,
    heldout_role_reversal_pairs,
    induce_joint_grounding,
    positionless_surface_upper_bound,
    run,
    semantic_accuracy,
    training_observations,
)


class Phase17gJointRoleGroundingTests(unittest.TestCase):
    def test_positive_grounding_is_unique(self) -> None:
        training = training_observations()
        self.assertEqual(len(enumerate_entity_groundings(training)), 1)
        self.assertEqual(len(enumerate_joint_models(training)), 1)

    def test_ambiguous_signatures_are_not_forced(self) -> None:
        self.assertGreater(duplicate_entity_signature_control(), 1)
        self.assertGreater(distractor_collision_control(), 1)

    def test_unseen_compositions_transfer(self) -> None:
        model = induce_joint_grounding(training_observations())
        heldout = heldout_role_reversal_pairs()
        accuracy, coverage = semantic_accuracy(model, heldout)
        self.assertEqual(accuracy, 1.0)
        self.assertEqual(coverage, 1.0)
        self.assertEqual(positionless_surface_upper_bound(heldout), 0.5)

    def test_all_theorem_checks_pass(self) -> None:
        payload = run()
        self.assertTrue(payload["all_theorem_checks_pass"])
        self.assertFalse(
            payload["claim_boundary"]["natural_language_understanding_demonstrated"]
        )
        self.assertFalse(payload["claim_boundary"]["general_llm_parity_allowed"])


if __name__ == "__main__":
    unittest.main()
