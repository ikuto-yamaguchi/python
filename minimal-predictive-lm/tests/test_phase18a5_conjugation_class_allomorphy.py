from __future__ import annotations

import unittest

from minimal_predictive_lm import phase18a5_conjugation_class_allomorphy as phase


class Phase18a5ConjugationClassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.training = phase.training_observations()
        (
            cls.model,
            cls.fit,
            cls.memorizer,
            cls.global_model,
        ) = phase.induce_conjugation_classes(cls.training)
        cls.heldout = phase.heldout_observations()

    def test_campaign_passes_all_gates(self) -> None:
        payload = phase.run()
        failed = [
            name
            for name, passed in payload["theorem_checks"].items()
            if not passed
        ]
        self.assertEqual(failed, [])
        self.assertTrue(payload["all_theorem_checks_pass"])

    def test_three_classes_and_nine_families_are_induced(self) -> None:
        self.assertEqual(len(self.model.paradigms), 3)
        self.assertEqual(len(self.model.families), 9)
        self.assertTrue(
            all(
                count == 2
                for _, count in self.fit.support_families_per_class
            )
        )

    def test_target_analysis_and_generation_are_perfect(self) -> None:
        self.assertEqual(phase.score(self.model, self.heldout), (1.0, 1.0))
        self.assertEqual(phase.generation_accuracy(self.model), 1.0)
        self.assertEqual(
            phase.score(self.memorizer, self.heldout)[1],
            0.0,
        )

    def test_class_conditioning_rejects_wrong_allomorphs(self) -> None:
        decoys = phase.wrong_class_decoys(self.model)
        self.assertGreater(len(decoys), 0)
        self.assertEqual(phase.score(self.model, decoys)[1], 0.0)
        self.assertGreater(
            phase.score(self.global_model, decoys)[1],
            0.0,
        )

    def test_single_global_generator_is_insufficient(self) -> None:
        self.assertLess(
            phase.class_agnostic_generation_accuracy(self.model),
            1.0,
        )

    def test_identifiability_controls_reject(self) -> None:
        self.assertTrue(phase.target_negative_anchor_is_necessary())
        self.assertTrue(phase.recurring_support_is_necessary())
        self.assertTrue(phase.unknown_anchor_abstains(self.model))


if __name__ == "__main__":
    unittest.main()
