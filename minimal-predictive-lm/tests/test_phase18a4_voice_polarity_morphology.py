from __future__ import annotations

import unittest

from minimal_predictive_lm import phase18a4_voice_polarity_morphology as phase


class Phase18a4VoicePolarityMorphologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.training = phase.training_observations()
        (
            cls.model,
            cls.fit,
            cls.memorizer,
            cls.suffix_model,
        ) = phase.infer_morphology(cls.training)
        cls.positive = phase.heldout_observations(
            phase.positive_family_voice_heldout_cells()
        )
        cls.negative = phase.heldout_observations(
            phase.globally_composed_negative_cells()
        )

    def test_campaign_passes_all_theorem_checks(self) -> None:
        payload = phase.run()
        failed = [
            name
            for name, passed in payload["theorem_checks"].items()
            if not passed
        ]
        self.assertEqual(failed, [])
        self.assertTrue(payload["all_theorem_checks_pass"])

    def test_global_unseen_voice_negative_compositions_transfer(self) -> None:
        self.assertEqual(phase.score(self.model, self.negative), (1.0, 1.0))
        self.assertEqual(
            phase.score(self.suffix_model, self.negative)[1],
            0.0,
        )

    def test_family_voice_recombination_transfers(self) -> None:
        self.assertEqual(phase.score(self.model, self.positive), (1.0, 1.0))
        self.assertEqual(
            phase.score(self.memorizer, self.positive)[1],
            0.0,
        )

    def test_morphology_is_factored_into_three_by_two(self) -> None:
        self.assertEqual(
            {
                self.model.active_prefix,
                self.model.passive_prefix,
                self.model.causative_prefix,
            },
            {"", "られ", "させ"},
        )
        self.assertEqual(
            {self.model.positive_ending, self.model.negative_ending},
            {"る", "ない"},
        )

    def test_nonidentifiable_or_conflicting_controls_reject(self) -> None:
        self.assertTrue(phase.missing_negative_anchor_is_rejected())
        self.assertTrue(phase.missing_passive_voice_is_rejected())
        self.assertTrue(phase.tied_surface_signature_is_rejected())

    def test_unknown_forms_and_wrong_arity_abstain(self) -> None:
        self.assertTrue(phase.unknown_morphology_abstains(self.model))
        self.assertTrue(phase.wrong_arity_abstains(self.model))

    def test_internal_voice_and_polarity_interventions_are_causal(self) -> None:
        self.assertTrue(phase.voice_intervention_preserves_event(self.model))
        self.assertTrue(phase.polarity_intervention_suppresses_event(self.model))


if __name__ == "__main__":
    unittest.main()
