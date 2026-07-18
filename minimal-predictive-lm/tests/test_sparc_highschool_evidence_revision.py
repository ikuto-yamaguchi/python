from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_evidence_revision import EvidenceRevisionWorkspaceLearner
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


class EvidenceRevisionWorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.learner = EvidenceRevisionWorkspaceLearner(max_evidence_components=4)
        self.learner.learn_independent_documents(_corpus(), min_support=4)
        self.learner.learn_independent_numeric_documents(_numeric_corpus())
        self.learner.learn_long_chronological_documents(_long_corpus())

    @staticmethod
    def narrative(target: str, initial: int, add: int) -> str:
        observed = initial + add
        return (
            f"{target}に{add}個加える。資料を確認した。{target}には{observed}個ある。"
            f"{target}を2倍にする。{target}について不足する状態を説明してください。"
        )

    def test_keeps_multiple_verified_components(self):
        first = self.learner.ingest_verified_evidence(self.narrative("論点A", 7, 3))
        second = self.learner.ingest_verified_evidence(self.narrative("論点B", 5, 4))
        recalled = self.learner.answer_from_evidence_ledger("論点Aの根拠を説明してください。")
        self.assertTrue(first.accepted)
        self.assertTrue(second.accepted)
        self.assertTrue(recalled.accepted)
        self.assertEqual("論点A", recalled.target)
        self.assertIn(("論点A", recalled.selected_states[0][1], 0, 7), recalled.selected_states)

    def test_verified_revision_replaces_only_one_component(self):
        self.learner.ingest_verified_evidence(self.narrative("論点A", 7, 3))
        self.learner.ingest_verified_evidence(self.narrative("論点B", 5, 4))
        revised = self.learner.ingest_verified_evidence(self.narrative("論点A", 11, 3))
        first = self.learner.answer_from_evidence_ledger("論点Aを説明してください。")
        second = self.learner.answer_from_evidence_ledger("論点Bを説明してください。")
        self.assertTrue(revised.revised)
        self.assertEqual(2, revised.version)
        self.assertTrue(any(row[0] == "論点A" and row[2] == 0 and row[3] == 11 for row in first.selected_states))
        self.assertTrue(any(row[0] == "論点B" and row[2] == 0 and row[3] == 5 for row in second.selected_states))

    def test_unverified_update_does_not_destroy_previous_evidence(self):
        self.learner.ingest_verified_evidence(self.narrative("論点A", 7, 3))
        rejected = self.learner.ingest_verified_evidence(
            "論点Aに3個加える。論点Aには10個ある。論点Aには12個ある。論点Aを説明してください。"
        )
        recalled = self.learner.answer_from_evidence_ledger("論点Aを説明してください。")
        self.assertFalse(rejected.accepted)
        self.assertTrue(recalled.accepted)
        self.assertTrue(any(row[2] == 0 and row[3] == 7 for row in recalled.selected_states))

    def test_bounded_ledger_persists_and_restores(self):
        self.learner.ingest_verified_evidence(self.narrative("論点A", 7, 3))
        self.learner.ingest_verified_evidence(self.narrative("論点B", 5, 4))
        payload = self.learner.evidence_ledger_bytes()
        restored = EvidenceRevisionWorkspaceLearner(max_evidence_components=4)
        restored.load_evidence_ledger_bytes(payload)
        result = restored.answer_from_evidence_ledger("論点Bを説明してください。")
        self.assertTrue(result.accepted)
        self.assertEqual("論点B", result.target)
        self.assertLessEqual(len(payload), 4096)


if __name__ == "__main__":
    unittest.main()
