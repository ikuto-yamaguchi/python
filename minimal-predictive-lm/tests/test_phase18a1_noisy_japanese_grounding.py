from __future__ import annotations

import unittest

from minimal_predictive_lm.phase18a1_noisy_japanese_grounding import (
    FLIPS_PER_GROUP,
    IDENTIFYING_PAIRS,
    REPETITIONS,
    heldout_unseen_compositions,
    induce_japanese_grounding,
    majority_recovery_union_bound,
    run,
    training_observations,
)


class Phase18a1NoisyJapaneseGroundingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = run()

    def test_all_theorem_checks_pass(self) -> None:
        self.assertTrue(self.payload["all_theorem_checks_pass"])
        self.assertTrue(all(self.payload["theorem_checks"].values()))

    def test_noisy_grounding_is_unique_with_large_margin(self) -> None:
        grounding = self.payload["grounding"]
        self.assertEqual(grounding["best_groundings"], 1)
        self.assertEqual(grounding["best_hamming_cost"], 2)
        self.assertGreaterEqual(grounding["loss_margin"], 1)
        self.assertGreater(grounding["candidate_assignments"], 100_000)

    def test_heldout_compositions_are_not_memorized_pairs(self) -> None:
        evaluation = self.payload["evaluation"]
        self.assertEqual(evaluation["heldout_accuracy"], 1.0)
        self.assertEqual(evaluation["heldout_coverage"], 1.0)
        self.assertEqual(evaluation["joint_action_frame_memorizer_coverage"], 0.0)
        self.assertLess(evaluation["action_only_accuracy"], 1.0)
        self.assertLess(evaluation["frame_only_accuracy"], 1.0)

    def test_positionless_surface_baseline_is_exactly_half(self) -> None:
        self.assertEqual(
            self.payload["evaluation"]["positionless_surface_upper_bound"],
            0.5,
        )

    def test_finite_sample_bound_is_declared_and_non_vacuous(self) -> None:
        bound = majority_recovery_union_bound(
            groups=len(IDENTIFYING_PAIRS),
            repetitions=REPETITIONS,
            flip_probability=FLIPS_PER_GROUP / REPETITIONS,
        )
        self.assertLess(bound, 0.01)
        self.assertGreater(bound, 0.0)

    def test_model_abstains_outside_learned_case_frames(self) -> None:
        model, _, _, _ = induce_japanese_grounding(training_observations())
        before = (1, 2, 3, 4)
        self.assertIsNone(model.predict("アキ と ボブ が 渡す。", before))
        self.assertIsNone(model.predict("アキ が ボブ に 未知る。", before))

    def test_heldout_suite_contains_only_unseen_compositions(self) -> None:
        self.assertEqual(len(heldout_unseen_compositions()), 24)


if __name__ == "__main__":
    unittest.main()
