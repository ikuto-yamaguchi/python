from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus
from minimal_predictive_lm.sparc_highschool_question_grounding import QuestionGroundedWorldLearner


class QuestionGroundedWorldLearnerTest(unittest.TestCase):
    def learner(self):
        learner = QuestionGroundedWorldLearner()
        learner.learn_independent_documents(_corpus(), min_support=4)
        learner.learn_independent_numeric_documents(_numeric_corpus())
        learner.learn_long_chronological_documents(_long_corpus())
        return learner

    def test_selects_only_asked_world_component(self):
        learner = self.learner()
        result = learner.answer_question_grounded_world(
            "甲系列に3個加える。甲系列には13個ある。甲系列を2倍にする。"
            "乙系列を3倍にする。乙系列には21個ある。乙系列に2個加える。"
            "文章の情報から甲系列の分からない状態だけを説明してください。"
        )
        self.assertTrue(result.accepted)
        self.assertEqual(("甲系列",), result.targets)
        self.assertTrue(result.selected_states)
        self.assertTrue(all(row[0] == "甲系列" for row in result.selected_states))
        self.assertIn("検算", result.answer)

    def test_uses_maximal_entity_span_for_overlapping_names(self):
        learner = self.learner()
        result = learner.answer_question_grounded_world(
            "系列1に3個加える。系列1には13個ある。系列1を2倍にする。"
            "系列10を3倍にする。系列10には21個ある。系列10に2個加える。"
            "系列10について不足する状態を説明してください。"
        )
        self.assertTrue(result.accepted)
        self.assertEqual(("系列10",), result.targets)
        self.assertTrue(result.selected_states)
        self.assertTrue(all(row[0] == "系列10" for row in result.selected_states))
        self.assertNotIn("系列1について", result.answer)

    def test_abstains_when_question_mentions_two_supported_targets(self):
        learner = self.learner()
        result = learner.answer_question_grounded_world(
            "甲系列に3個加える。甲系列には13個ある。乙系列を3倍にする。乙系列には21個ある。"
            "甲系列と乙系列の状態を答えてください。"
        )
        self.assertFalse(result.accepted)
        self.assertEqual("abstain-ambiguous-question-target", result.mechanism)

    def test_round_trip_preserves_question_grounding(self):
        learner = self.learner()
        restored = QuestionGroundedWorldLearner.from_bytes(learner.to_bytes())
        result = restored.answer_question_grounded_world(
            "保存系列に2個加える。保存系列には9個ある。保存系列を3倍にする。"
            "保存系列について不足する状態を説明してください。"
        )
        self.assertTrue(result.accepted)
        self.assertEqual(("保存系列",), result.targets)


if __name__ == "__main__":
    unittest.main()
