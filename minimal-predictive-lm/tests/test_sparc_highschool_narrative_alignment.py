from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_narrative_alignment import NarrativeAlignedLearner
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


class NarrativeAlignmentTests(unittest.TestCase):
    def learner(self) -> NarrativeAlignedLearner:
        learner = NarrativeAlignedLearner()
        learner.learn_independent_documents(_corpus(), min_support=4)
        learner.learn_independent_numeric_documents(_numeric_corpus())
        learner.learn_long_chronological_documents(_long_corpus())
        return learner

    def test_infers_observations_factual_path_and_replacement_without_task_label(self):
        learner = self.learner()
        result = learner.infer_counterfactual_narrative(
            "青箱には10個ある。\n青箱に3個加える。途中で担当者は記録を確認した。青箱を2倍にする。青箱には26個ある。\n別案を検討する。青箱に5個加える。結果を説明せよ。"
        )
        self.assertTrue(result.accepted)
        self.assertEqual(0, result.intervention_at)
        self.assertEqual(26, next(iter(result.comparison.factual.world.number_map().values())))
        self.assertEqual(30, next(iter(result.comparison.counterfactual.world.number_map().values())))

    def test_embedded_replacement_is_selected_by_world_consistency(self):
        learner = self.learner()
        result = learner.infer_counterfactual_narrative(
            "青箱には10個ある。青箱に3個加える。青箱を2倍にする。青箱には26個ある。別の案として青箱に5個加える。"
        )
        self.assertTrue(result.accepted)
        self.assertEqual(("青箱に5個加える",), result.replacement_actions)
        self.assertEqual(30, next(iter(result.comparison.counterfactual.world.number_map().values())))

    def test_abstains_when_two_replacements_are_equally_supported(self):
        learner = self.learner()
        result = learner.infer_counterfactual_narrative(
            "青箱には10個ある。青箱に3個加える。青箱を2倍にする。青箱には26個ある。青箱に5個加える。青箱に7個加える。"
        )
        self.assertFalse(result.accepted)
        self.assertEqual("abstain-ambiguous-narrative", result.mechanism)

    def test_roundtrip_preserves_alignment(self):
        learner = self.learner()
        restored = learner.from_bytes(learner.to_bytes())
        result = restored.infer_counterfactual_narrative(
            "試料甲の温度は10度である。試料甲の温度を5度上げる。観測者は窓を閉めた。試料甲の温度を5度上げる。試料甲の温度は20度である。試料甲の温度を3度上げる。"
        )
        self.assertFalse(result.accepted)


if __name__ == "__main__":
    unittest.main()
