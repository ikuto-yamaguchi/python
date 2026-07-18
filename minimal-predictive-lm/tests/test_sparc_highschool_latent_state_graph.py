from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_latent_state_graph import LatentStateGraphLearner
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


class LatentStateGraphLearnerTest(unittest.TestCase):
    def learner(self) -> LatentStateGraphLearner:
        learner = LatentStateGraphLearner()
        learner.learn_independent_documents(_corpus(), min_support=4)
        learner.learn_independent_numeric_documents(_numeric_corpus())
        learner.learn_long_chronological_documents(_long_corpus())
        return learner

    @staticmethod
    def subject_value(world, subject: str) -> int | None:
        rows = [value for (row_subject, _relation), value in world.number_map().items() if row_subject == subject]
        return rows[0] if len(rows) == 1 else None

    def test_recovers_omitted_initial_and_intermediate_states(self):
        learner = self.learner()
        text = (
            "系列Aに3個加える。系列Aには13個ある。系列Aを2倍にする。"
            "系列Aに4個加える。系列Aには30個ある。"
            "系列Bを3倍にする。系列Bには21個ある。系列Bに2個加える。"
        )
        result = learner.infer_latent_state_graph(text)
        self.assertTrue(result.accepted)
        self.assertTrue(result.verified)
        recovered = {(subject, node, value) for subject, _relation, node, value in result.recovered_states}
        self.assertIn(("系列A", 0, 10), recovered)
        self.assertIn(("系列A", 2, 26), recovered)
        self.assertIn(("系列B", 0, 7), recovered)
        self.assertIn(("系列B", 2, 23), recovered)
        self.assertEqual("shared-bidirectional-latent-state-graph", result.mechanism)
        self.assertIn("検算", result.answer)

    def test_unanchored_transition_component_does_not_poison_solved_chain(self):
        learner = self.learner()
        result = learner.infer_latent_state_graph(
            "無関係に5個加える。系列に3個加える。系列には13個ある。"
            "系列を2倍にする。系列には26個ある。"
        )
        self.assertTrue(result.accepted)
        recovered = {(subject, node, value) for subject, _relation, node, value in result.recovered_states}
        self.assertIn(("系列", 0, 10), recovered)
        self.assertIsNone(self.subject_value(result.initial_world, "無関係"))
        self.assertGreaterEqual(learner.latent_unanchored_components_skipped, 1)

    def test_observation_only_component_is_preserved_as_fixed_context(self):
        learner = self.learner()
        result = learner.infer_latent_state_graph(
            "資料Cには99個ある。系列に3個加える。系列には13個ある。"
            "系列を2倍にする。系列には26個ある。"
        )
        self.assertTrue(result.accepted)
        self.assertEqual(99, self.subject_value(result.initial_world, "資料C"))
        self.assertEqual(99, self.subject_value(result.final_world, "資料C"))
        self.assertGreaterEqual(learner.latent_fixed_observation_components, 1)

    def test_abstains_on_inconsistent_middle_observation(self):
        learner = self.learner()
        result = learner.infer_latent_state_graph(
            "系列に3個加える。系列には14個ある。系列を2倍にする。系列には26個ある。"
        )
        self.assertFalse(result.accepted)
        self.assertIn("inconsistent", result.mechanism)

    def test_round_trip_preserves_latent_graph_solver(self):
        learner = self.learner()
        restored = LatentStateGraphLearner.from_bytes(learner.to_bytes())
        result = restored.infer_latent_state_graph(
            "保存系列に2個加える。保存系列には9個ある。保存系列を3倍にする。"
        )
        self.assertTrue(result.accepted)
        recovered = {(subject, node, value) for subject, _relation, node, value in result.recovered_states}
        self.assertIn(("保存系列", 0, 7), recovered)
        self.assertIn(("保存系列", 2, 27), recovered)


if __name__ == "__main__":
    unittest.main()
