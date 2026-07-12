from __future__ import annotations

import unittest

from minimal_predictive_lm.phase18a2_continuous_japanese_grounding import (
    ACTION_LEXEMES,
    ENTITY_LEXEMES,
    boundary_ablation_optima,
    collision_control_optima,
    extract_segmented_factor,
    heldout_unseen_compositions,
    induce_continuous_japanese,
    normalize_continuous,
    run,
    semantic_training_observations,
    training_observations,
)


class Phase18a2ContinuousJapaneseTests(unittest.TestCase):
    def test_full_campaign_passes_all_declared_checks(self) -> None:
        payload = run()
        self.assertTrue(payload["all_theorem_checks_pass"])
        self.assertTrue(all(payload["theorem_checks"].values()))

    def test_grounding_and_action_lexicons_are_recovered(self) -> None:
        model, grounding, action_search, skipped = induce_continuous_japanese(
            training_observations()
        )
        self.assertEqual(
            dict(model.entity_lexicon),
            {lexeme: index for index, lexeme in enumerate(ENTITY_LEXEMES)},
        )
        self.assertEqual(set(model.action_lexicon), set(ACTION_LEXEMES))
        self.assertEqual(len(grounding.best_mappings), 1)
        self.assertGreater(grounding.margin or 0, 0)
        self.assertEqual(action_search.best_models, 1)
        self.assertEqual(skipped, 2)

    def test_raw_inputs_have_no_whitespace_boundaries(self) -> None:
        rows = (*training_observations(), *heldout_unseen_compositions())
        self.assertTrue(
            all(
                not any(character.isspace() for character in observation.sentence)
                for observation in rows
            )
        )
        self.assertTrue(
            all(" " not in normalize_continuous(row.sentence) for row in rows)
        )

    def test_boundary_and_collision_controls_remain_non_identifying(self) -> None:
        self.assertGreater(boundary_ablation_optima(), 1)
        self.assertGreater(collision_control_optima(), 1)

    def test_heldout_action_frame_pairs_are_unseen_compositions(self) -> None:
        model, _, _, _ = induce_continuous_japanese(training_observations())
        training_pairs = {
            (factor.action, factor.frame)
            for row in semantic_training_observations()
            for factor, _ in (
                extract_segmented_factor(
                    row,
                    entity_grounding=model.entity_lexicon,
                    action_lexicon=model.action_lexicon,
                ),
            )
        }
        heldout_pairs = {
            (factor.action, factor.frame)
            for row in heldout_unseen_compositions()
            for factor, _ in (
                extract_segmented_factor(
                    row,
                    entity_grounding=model.entity_lexicon,
                    action_lexicon=model.action_lexicon,
                ),
            )
        }
        self.assertTrue(training_pairs.isdisjoint(heldout_pairs))
        self.assertEqual(len(heldout_pairs), 6)
        self.assertEqual(len(heldout_unseen_compositions()), 12)

    def test_unknown_action_and_unknown_frame_abstain(self) -> None:
        model, _, _, _ = induce_continuous_japanese(training_observations())
        before = (1, 2, 3, 4)
        self.assertIsNone(model.predict("アキがボブに交換する。", before))
        self.assertIsNone(model.predict("アキとボブを渡す。", before))


if __name__ == "__main__":
    unittest.main()
