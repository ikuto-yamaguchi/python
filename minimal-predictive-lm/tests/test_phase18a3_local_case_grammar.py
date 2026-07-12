from __future__ import annotations

import unittest

from minimal_predictive_lm.phase18a3_local_case_grammar_v2 import (
    TRAINING_SPECS,
    contradictory_cycle_is_rejected,
    disconnected_graph_is_rejected,
    evaluate_model,
    heldout_specs,
    heldout_unseen_local_compositions,
    induce_local_case_grammar,
    run,
    same_polarity_pair_abstains,
    semantic_training_observations,
    tied_majority_is_rejected,
    training_observations,
    unknown_particle_abstains,
)


class Phase18a3LocalCaseGrammarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.training = training_observations()
        cls.semantic_training = semantic_training_observations()
        cls.heldout = heldout_unseen_local_compositions()
        cls.model, cls.template_model, cls.fit = induce_local_case_grammar(
            cls.training
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

    def test_heldout_whole_forms_are_unseen_in_each_joint_key(self) -> None:
        seen_action_particle = {
            (action, first)
            for action, first, _, _ in TRAINING_SPECS
        }
        seen_particle_pair = {
            (first, second)
            for _, first, second, _ in TRAINING_SPECS
        }
        seen_particle_order = {
            (first, order)
            for _, first, _, order in TRAINING_SPECS
        }
        for action, first, second, order in heldout_specs():
            self.assertNotIn((action, first), seen_action_particle)
            self.assertNotIn((first, second), seen_particle_pair)
            self.assertNotIn((first, order), seen_particle_order)

    def test_local_grammar_transfers_but_template_model_abstains(self) -> None:
        accuracy, coverage = evaluate_model(self.model, self.heldout)
        self.assertEqual((accuracy, coverage), (1.0, 1.0))
        template_answers = [
            self.template_model.predict(row.sentence, row.before)
            for row in self.heldout
        ]
        self.assertTrue(all(answer is None for answer in template_answers))

    def test_final_model_has_atoms_not_literal_frame_index(self) -> None:
        self.assertEqual(len(self.model.particle_index), 6)
        self.assertEqual(len(self.model.order_patterns), 3)
        self.assertFalse(hasattr(self.model, "frame_index"))

    def test_non_identifiable_or_invalid_grammars_are_rejected(self) -> None:
        self.assertTrue(tied_majority_is_rejected())
        self.assertTrue(disconnected_graph_is_rejected())
        self.assertTrue(contradictory_cycle_is_rejected())

    def test_unknown_or_same_role_markers_abstain(self) -> None:
        self.assertTrue(same_polarity_pair_abstains(self.model))
        self.assertTrue(unknown_particle_abstains(self.model))


if __name__ == "__main__":
    unittest.main()
