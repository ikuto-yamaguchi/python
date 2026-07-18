from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_intervention_lattice import InterventionLatticeLearner
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


class InterventionLatticeLearnerTest(unittest.TestCase):
    def learner(self) -> InterventionLatticeLearner:
        learner = InterventionLatticeLearner()
        learner.learn_independent_documents(_corpus(), min_support=4)
        learner.learn_independent_numeric_documents(_numeric_corpus())
        learner.learn_long_chronological_documents(_long_corpus())
        return learner

    def test_decomposes_shared_operations_and_their_interaction(self):
        learner = self.learner()
        text = (
            "分析箱には6個ある。\n"
            "分析箱に2個加える。途中の観測を記録した。分析箱を2倍にする。"
            "分析箱に3個加える。分析箱には19個ある。\n"
            "別の進め方では分析箱を3倍にする。"
            "どの操作が結果へ寄与し、互いにどう作用したか説明せよ。"
        )
        result = learner.explain_interaction_narrative(text)
        self.assertTrue(result.accepted)
        self.assertTrue(result.verified)
        self.assertEqual((4, 8, 3), result.contributions)
        self.assertIn((0, 1, 2), result.pairwise_interactions)
        self.assertIn("増幅相互作用", result.answer)
        self.assertIn("検算", result.answer)

    def test_abstains_without_verified_shared_world_alignment(self):
        learner = self.learner()
        result = learner.explain_interaction_narrative("複数の原因について説明してください。")
        self.assertFalse(result.accepted)
        self.assertEqual("abstain-unverified-causal-provenance", result.mechanism)

    def test_round_trip_preserves_intervention_lattice(self):
        learner = self.learner()
        restored = InterventionLatticeLearner.from_bytes(learner.to_bytes())
        text = (
            "保存対象には7個ある。保存対象に2個加える。保存対象を2倍にする。"
            "保存対象に3個加える。保存対象には21個ある。"
            "別案では保存対象を3倍にする。寄与の組合せを説明せよ。"
        )
        result = restored.explain_interaction_narrative(text)
        self.assertTrue(result.accepted)
        self.assertEqual((4, 9, 3), result.contributions)
        self.assertIn((0, 1, 2), result.pairwise_interactions)


if __name__ == "__main__":
    unittest.main()
