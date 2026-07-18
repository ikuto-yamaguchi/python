from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_highschool_discourse_workspace import DiscourseEvidenceWorkspaceLearner
from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


class DiscourseEvidenceWorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.learner = DiscourseEvidenceWorkspaceLearner()
        self.learner.learn_independent_documents(_corpus(), min_support=4)
        self.learner.learn_independent_numeric_documents(_numeric_corpus())
        self.learner.learn_long_chronological_documents(_long_corpus())
        self.body = (
            "系列Aに3個加える。系列Aには13個ある。系列Aを2倍にする。"
            "系列Bを3倍にする。系列Bには21個ある。系列Bに2個加える。"
        )

    def test_reuses_only_verified_focus_for_followup(self):
        first = self.learner.answer_discourse_grounded_world(
            self.body + "系列Aについて不足する状態を説明してください。"
        )
        follow = self.learner.answer_discourse_grounded_world(
            self.body + "続けて、この計算の根拠を検算結果とともに説明してください。"
        )
        self.assertTrue(first.accepted)
        self.assertTrue(follow.accepted)
        self.assertEqual(("系列A",), follow.targets)
        self.assertTrue(follow.focus_reused)
        self.assertNotIn("系列Bの", follow.answer)

    def test_explicit_supported_component_switches_focus(self):
        self.learner.answer_discourse_grounded_world(
            self.body + "系列Aについて不足する状態を説明してください。"
        )
        switched = self.learner.answer_discourse_grounded_world(
            self.body + "次は系列Bについて同じ根拠を説明してください。"
        )
        follow = self.learner.answer_discourse_grounded_world(
            self.body + "その結果も再実行して確かめてください。"
        )
        self.assertTrue(switched.accepted)
        self.assertEqual(("系列B",), switched.targets)
        self.assertTrue(follow.accepted)
        self.assertEqual(("系列B",), follow.targets)
        self.assertEqual(1, self.learner.discourse_focus_switches)

    def test_ambiguity_clears_workspace_and_prevents_stale_reuse(self):
        self.learner.answer_discourse_grounded_world(
            self.body + "系列Aについて不足する状態を説明してください。"
        )
        ambiguous = self.learner.answer_discourse_grounded_world(
            self.body + "系列Aと系列Bについて説明してください。"
        )
        stale = self.learner.answer_discourse_grounded_world(
            self.body + "続けて根拠を説明してください。"
        )
        self.assertFalse(ambiguous.accepted)
        self.assertFalse(stale.accepted)
        self.assertEqual((), self.learner._discourse_focus)


if __name__ == "__main__":
    unittest.main()
