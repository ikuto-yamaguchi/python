from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_implicit_world import ImplicitWorldLearner
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


class ImplicitWorldLearnerTest(unittest.TestCase):
    def learner(self) -> ImplicitWorldLearner:
        learner = ImplicitWorldLearner()
        learner.learn_independent_documents(_corpus(), min_support=4)
        learner.learn_independent_numeric_documents(_numeric_corpus())
        learner.learn_long_chronological_documents(_long_corpus())
        return learner

    @staticmethod
    def values(result):
        return {(subject, value) for subject, _relation, value in result.inferred_values}

    def test_recovers_two_omitted_initial_states_with_one_shared_mechanism(self):
        learner = self.learner()
        text = (
            "主系列に3個加える。途中の記録を整理した。主系列を2倍にする。"
            "副系列に4個加える。副系列を3倍にする。"
            "主系列には26個ある。副系列には27個ある。"
        )
        result = learner.infer_implicit_world(text)
        self.assertTrue(result.accepted)
        self.assertTrue(result.verified)
        self.assertEqual({("主系列", 10), ("副系列", 5)}, self.values(result))
        self.assertIn("逆向き", result.answer)
        self.assertIn("検算", result.answer)
        self.assertEqual("shared-reversible-affine-world-constraint", result.mechanism)

    def test_abstains_when_reverse_constraint_is_not_integral(self):
        learner = self.learner()
        result = learner.infer_implicit_world("箱に3個加える。箱を2倍にする。箱には25個ある。")
        self.assertFalse(result.accepted)
        self.assertEqual("abstain-nonintegral-or-singular-constraint", result.mechanism)

    def test_round_trip_preserves_shared_reverse_programs(self):
        learner = self.learner()
        restored = ImplicitWorldLearner.from_bytes(learner.to_bytes())
        result = restored.infer_implicit_world("保存系列に2個加える。保存系列を3倍にする。保存系列には27個ある。")
        self.assertTrue(result.accepted)
        self.assertEqual({("保存系列", 7)}, self.values(result))


if __name__ == "__main__":
    unittest.main()
