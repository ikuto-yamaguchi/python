from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_hypothesis_consensus import HypothesisConsensusWorkspaceLearner
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


class HypothesisConsensusWorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.learner = HypothesisConsensusWorkspaceLearner(
            max_evidence_components=4,
            max_hypotheses_per_target=3,
        )
        self.learner.learn_independent_documents(_corpus(), min_support=4)
        self.learner.learn_independent_numeric_documents(_numeric_corpus())
        self.learner.learn_long_chronological_documents(_long_corpus())

    @staticmethod
    def narrative(target: str, initial: int, add: int, note: str) -> str:
        observed = initial + add
        return (
            f"{target}に{add}個加える。{note}。{target}には{observed}個ある。"
            f"{target}を2倍にする。{target}について不足する状態を説明してください。"
        )

    def test_conflicting_verified_hypotheses_abstain_until_one_has_more_support(self):
        self.learner.ingest_verified_hypothesis(self.narrative("論点A", 7, 3, "第一資料を確認した"))
        self.learner.ingest_verified_hypothesis(self.narrative("論点A", 12, 3, "第二資料を確認した"))
        tied = self.learner.answer_from_hypothesis_graph("論点Aの結論を説明してください。")
        self.assertFalse(tied.accepted)
        self.assertEqual("abstain-unresolved-verified-hypothesis-conflict", tied.mechanism)

        self.learner.ingest_verified_hypothesis(self.narrative("論点A", 12, 3, "独立資料を再確認した"))
        resolved = self.learner.answer_from_hypothesis_graph("論点Aの結論を説明してください。")
        self.assertTrue(resolved.accepted)
        self.assertEqual(2, resolved.support)
        self.assertEqual(2, resolved.competing_hypotheses)
        self.assertTrue(any(row[2] == 0 and row[3] == 12 for row in resolved.selected_states))
        self.assertTrue(all(not (row[2] == 0 and row[3] == 7) for row in resolved.selected_states))

    def test_exact_duplicate_evidence_does_not_manufacture_consensus(self):
        first = self.narrative("論点A", 7, 3, "同じ資料を確認した")
        self.learner.ingest_verified_hypothesis(first)
        self.learner.ingest_verified_hypothesis(self.narrative("論点A", 12, 3, "別資料を確認した"))
        self.learner.ingest_verified_hypothesis(first)
        result = self.learner.answer_from_hypothesis_graph("論点Aを説明してください。")
        self.assertFalse(result.accepted)
        self.assertEqual(1, self.learner.hypothesis_duplicate_evidence)

    def test_resolving_one_target_does_not_destroy_another(self):
        self.learner.ingest_verified_hypothesis(self.narrative("論点A", 7, 3, "資料A1"))
        self.learner.ingest_verified_hypothesis(self.narrative("論点A", 12, 3, "資料A2"))
        self.learner.ingest_verified_hypothesis(self.narrative("論点A", 12, 3, "資料A3"))
        self.learner.ingest_verified_hypothesis(self.narrative("論点B", 5, 4, "資料B1"))
        second = self.learner.answer_from_hypothesis_graph("論点Bを説明してください。")
        self.assertTrue(second.accepted)
        self.assertEqual(1, second.support)
        self.assertTrue(any(row[2] == 0 and row[3] == 5 for row in second.selected_states))

    def test_bounded_graph_persists_and_restores(self):
        self.learner.ingest_verified_hypothesis(self.narrative("論点A", 7, 3, "資料1"))
        self.learner.ingest_verified_hypothesis(self.narrative("論点A", 7, 3, "資料2"))
        payload = self.learner.hypothesis_graph_bytes()
        restored = HypothesisConsensusWorkspaceLearner(
            max_evidence_components=4,
            max_hypotheses_per_target=3,
        )
        restored.load_hypothesis_graph_bytes(payload)
        result = restored.answer_from_hypothesis_graph("論点Aを説明してください。")
        self.assertTrue(result.accepted)
        self.assertEqual(2, result.support)
        self.assertLessEqual(len(payload), 8192)


if __name__ == "__main__":
    unittest.main()
