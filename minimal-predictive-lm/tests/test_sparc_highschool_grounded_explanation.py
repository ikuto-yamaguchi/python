import unittest

from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_grounded_explanation import GroundedExplanationLearner
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


class GroundedExplanationTest(unittest.TestCase):
    def _learner(self):
        learner = GroundedExplanationLearner()
        learner.learn_independent_documents(_corpus(), min_support=4)
        learner.learn_independent_numeric_documents(_numeric_corpus())
        learner.learn_long_chronological_documents(_long_corpus())
        return learner

    def test_replays_and_verbalizes_both_worlds(self):
        learner = self._learner()
        text = (
            "説明箱には10個ある。\n"
            "説明箱に3個加える。途中の記録を確認した。説明箱を2倍にする。説明箱には26個ある。\n"
            "別の案として説明箱に5個加える。結果の違いを説明せよ。"
        )
        result = learner.explain_counterfactual_narrative(text)
        self.assertTrue(result.accepted)
        self.assertTrue(result.verified)
        self.assertEqual(result.factual_trace, (10, 13, 26))
        self.assertEqual(result.counterfactual_trace, (10, 15, 30))
        self.assertIn("実際の経路は10→13→26", result.answer)
        self.assertIn("変更した経路は10→15→30", result.answer)
        self.assertIn("検算", result.answer)

    def test_abstains_when_narrative_is_ambiguous(self):
        learner = self._learner()
        result = learner.explain_counterfactual_narrative("箱には10個ある。別の話もある。")
        self.assertFalse(result.accepted)
        self.assertEqual(result.answer, "")


if __name__ == "__main__":
    unittest.main()
