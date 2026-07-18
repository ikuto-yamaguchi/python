from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_highschool_causal_provenance import CausalProvenanceLearner
from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


class CausalProvenanceLearnerTest(unittest.TestCase):
    def learner(self) -> CausalProvenanceLearner:
        learner = CausalProvenanceLearner()
        learner.learn_independent_documents(_corpus(), min_support=4)
        learner.learn_independent_numeric_documents(_numeric_corpus())
        learner.learn_long_chronological_documents(_long_corpus())
        return learner

    def test_attributes_and_propagates_difference(self):
        learner = self.learner()
        text = (
            "試験箱には10個ある。\n"
            "試験箱に3個加える。途中経過を記録した。試験箱を2倍にする。試験箱には26個ある。\n"
            "別の進め方では試験箱に5個加える。なぜ結果が違うのか説明せよ。"
        )
        result = learner.explain_causal_narrative(text)
        self.assertTrue(result.accepted)
        self.assertTrue(result.verified)
        self.assertEqual((0, 2, 4), result.gap_trace)
        self.assertEqual(1, result.first_divergence)
        self.assertIn("2倍", result.answer)
        self.assertIn("検算", result.answer)

    def test_abstains_when_no_verified_alignment_exists(self):
        learner = self.learner()
        result = learner.explain_causal_narrative("結果が違う理由だけを説明してください。")
        self.assertFalse(result.accepted)
        self.assertEqual("abstain-unverified-grounded-explanation", result.mechanism)

    def test_round_trip_preserves_shared_mechanism(self):
        learner = self.learner()
        restored = CausalProvenanceLearner.from_bytes(learner.to_bytes())
        text = (
            "保存箱には12個ある。保存箱に2個加える。保存箱を2倍にする。保存箱には28個ある。\n"
            "別案では保存箱に4個加える。途中の差を説明せよ。"
        )
        result = restored.explain_causal_narrative(text)
        self.assertTrue(result.accepted)
        self.assertEqual((0, 2, 4), result.gap_trace)


if __name__ == "__main__":
    unittest.main()
