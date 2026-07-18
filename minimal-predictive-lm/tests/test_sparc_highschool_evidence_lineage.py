from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_evidence_lineage import EvidenceLineageConsensusLearner
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


def narrative(target: str, initial: int, note: str) -> str:
    observed = initial + 3
    return (
        f"{target}に3個加える。{note}。{target}には{observed}個ある。"
        f"{target}を2倍にする。{target}について不足する状態を根拠付きで説明してください。"
    )


class EvidenceLineageConsensusTest(unittest.TestCase):
    def learner(self) -> EvidenceLineageConsensusLearner:
        learner = EvidenceLineageConsensusLearner(
            max_evidence_components=4,
            max_hypotheses_per_target=3,
            max_lineages=8,
            lineage_similarity_threshold=0.50,
        )
        learner.learn_independent_documents(_corpus(), min_support=4)
        learner.learn_independent_numeric_documents(_numeric_corpus())
        learner.learn_long_chronological_documents(_long_corpus())
        return learner

    def test_reposts_do_not_create_independent_majority(self):
        learner = self.learner()
        target = "由来論点A"
        learner.ingest_lineage_verified_hypothesis(
            narrative(target, 7, "共同記録班の一次資料をそのまま転記した")
        )
        learner.ingest_lineage_verified_hypothesis(
            narrative(target, 7, "共同記録班の一次資料を一部整形して転記した")
        )
        learner.ingest_lineage_verified_hypothesis(
            narrative(target, 12, "別施設の担当者が独自に観測した")
        )
        tied = learner.answer_from_lineage_graph(f"{target}の結論を説明してください。")
        self.assertFalse(tied.accepted)
        self.assertEqual("abstain-unresolved-independent-lineage-conflict", tied.mechanism)
        self.assertGreaterEqual(learner.lineage_reuses, 1)
        self.assertGreaterEqual(learner.lineage_dependent_duplicates, 1)

        learner.ingest_lineage_verified_hypothesis(
            narrative(target, 12, "第三者の測定器で最初から再計測した")
        )
        resolved = learner.answer_from_lineage_graph(f"{target}の結論を説明してください。")
        self.assertTrue(resolved.accepted)
        self.assertEqual(2, resolved.support)
        self.assertIn((target, resolved.selected_states[0][1], 0, 12), resolved.selected_states)

    def test_one_lineage_cannot_support_incompatible_states(self):
        learner = self.learner()
        target = "由来論点B"
        learner.ingest_lineage_verified_hypothesis(
            narrative(target, 8, "同じ観測班の共有記録をそのまま掲載した")
        )
        learner.ingest_lineage_verified_hypothesis(
            narrative(target, 13, "同じ観測班の共有記録を少し整えて掲載した")
        )
        result = learner.answer_from_lineage_graph(f"{target}の結論を説明してください。")
        self.assertFalse(result.accepted)
        self.assertGreaterEqual(learner.lineage_conflicts, 1)

    def test_round_trip_preserves_lineages(self):
        learner = self.learner()
        target = "由来論点C"
        learner.ingest_lineage_verified_hypothesis(
            narrative(target, 9, "第一施設が独自に測定した")
        )
        learner.ingest_lineage_verified_hypothesis(
            narrative(target, 9, "第二施設が別の装置で測定した")
        )
        payload = learner.lineage_graph_bytes()
        restored = self.learner()
        restored.load_lineage_graph_bytes(payload)
        result = restored.answer_from_lineage_graph(f"{target}の結論を説明してください。")
        self.assertTrue(result.accepted)
        self.assertEqual(2, result.support)
        self.assertEqual(payload, restored.lineage_graph_bytes())

    def test_graph_is_bounded(self):
        learner = self.learner()
        for index in range(12):
            target = f"上限論点{index % 4}"
            learner.ingest_lineage_verified_hypothesis(
                narrative(target, 5 + index, f"独立測定施設{index}の記録を確認した")
            )
        self.assertLessEqual(len(learner._lineage_order), learner.max_lineages)
        self.assertLessEqual(len(learner._hypothesis_order), learner.max_evidence_components)
        self.assertLessEqual(len(learner.lineage_graph_bytes()), 16384)


if __name__ == "__main__":
    unittest.main()
