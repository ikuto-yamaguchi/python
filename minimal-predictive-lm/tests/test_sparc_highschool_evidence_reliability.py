import unittest

from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_evidence_reliability import EvidenceReliabilityConsensusLearner
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


def weak(target: str, initial: int, add: int, note: str) -> str:
    return (
        f"{target}に{add}個加える。{note}。{target}には{initial + add}個ある。"
        f"{target}を2倍にする。{target}について不足する状態を根拠付きで説明してください。"
    )


def strong(target: str, initial: int, add: int, note: str) -> str:
    final = (initial + add) * 2
    return (
        f"{target}には{initial}個ある。{target}に{add}個加える。"
        f"{target}を2倍にする。{target}には{final}個ある。{note}。"
        f"{target}について不足する状態を根拠付きで説明してください。"
    )


class EvidenceReliabilityConsensusTest(unittest.TestCase):
    def learner(self, **overrides):
        options = {
            "max_evidence_components": 8,
            "max_hypotheses_per_target": 3,
            "max_lineages": 12,
            "lineage_similarity_threshold": 0.50,
            "max_quality_weight": 3,
            "max_reliability_score": 4,
        }
        options.update(overrides)
        learner = EvidenceReliabilityConsensusLearner(**options)
        learner.learn_independent_documents(_corpus(), min_support=4)
        learner.learn_independent_numeric_documents(_numeric_corpus())
        learner.learn_long_chronological_documents(_long_corpus())
        return learner

    def calibrate(self, learner):
        reliable = "第三者校正研究所の標準器による継続測定"
        unreliable = "旧式集計局の推定装置による継続測定"
        for index in range(3):
            target = f"校正論点{index}A"
            add = index + 2
            truth = index + 8
            learner.ingest_reliability_verified_hypothesis(strong(target, truth + 5, add, unreliable))
            learner.ingest_reliability_verified_hypothesis(strong(target, truth, add, reliable))
            learner.ingest_reliability_verified_hypothesis(strong(target, truth, add, f"独立監査班{index}の再測定"))
            self.assertTrue(learner.consolidate_verified_target(target))
        return reliable, unreliable

    def test_cross_topic_reproducibility_beats_local_anchor_count(self):
        learner = self.learner()
        reliable, unreliable = self.calibrate(learner)
        target = "未知論点A"
        learner.ingest_reliability_verified_hypothesis(weak(target, 11, 3, reliable))
        learner.ingest_reliability_verified_hypothesis(strong(target, 16, 3, unreliable))
        result = learner.answer_from_reliability_graph(f"{target}の現在の結論を説明してください。")
        self.assertTrue(result.accepted)
        self.assertIn((target, "NDR0", 0, 11), result.selected_states)
        self.assertNotIn((target, "NDR0", 0, 16), result.selected_states)
        self.assertEqual("shared-bounded-cross-topic-verified-source-reliability-graph", result.mechanism)

    def test_unopposed_target_cannot_bootstrap_reliability(self):
        learner = self.learner()
        target = "単独論点B"
        learner.ingest_reliability_verified_hypothesis(strong(target, 7, 2, "単独資料の測定"))
        self.assertFalse(learner.consolidate_verified_target(target))
        self.assertEqual({}, learner._reliability)

    def test_tied_local_consensus_does_not_update_reliability(self):
        learner = self.learner()
        target = "同数論点C"
        learner.ingest_reliability_verified_hypothesis(strong(target, 7, 2, "東側測定所の記録"))
        learner.ingest_reliability_verified_hypothesis(strong(target, 12, 2, "西側測定所の記録"))
        self.assertFalse(learner.consolidate_verified_target(target))
        self.assertEqual({}, learner._reliability)

    def test_reliability_graph_is_bounded_and_serializable(self):
        learner = self.learner()
        self.calibrate(learner)
        payload = learner.reliability_graph_bytes()
        self.assertLessEqual(len(payload), 65536)
        self.assertEqual(3, learner.reliability_consolidations)
        self.assertGreater(learner.reliability_writes, 0)

    def test_evicted_lineages_and_targets_do_not_leak_reliability_state(self):
        learner = self.learner(max_evidence_components=2, max_lineages=3)
        target = "境界校正論点A"
        learner.ingest_reliability_verified_hypothesis(strong(target, 12, 2, "北部研究所の独立測定"))
        learner.ingest_reliability_verified_hypothesis(strong(target, 7, 2, "南部研究所の独立測定"))
        learner.ingest_reliability_verified_hypothesis(strong(target, 7, 2, "中央監査所の独立再測定"))
        self.assertTrue(learner.consolidate_verified_target(target))
        scored_lineages = set(learner._reliability)
        self.assertTrue(scored_lineages)

        for index in range(6):
            new_target = f"流入論点{index}Z"
            learner.ingest_reliability_verified_hypothesis(
                strong(new_target, index + 5, 2, f"固有観測施設{index}による独立測定記録")
            )

        learner.reliability_graph_bytes()
        self.assertLessEqual(len(learner._reliability), learner.max_lineages)
        self.assertTrue(set(learner._reliability).issubset(learner._lineages))
        self.assertTrue(learner._reliability_settled_targets.issubset(learner._hypotheses))
        self.assertTrue(scored_lineages.isdisjoint(learner._reliability))

    def test_reset_clears_graph_local_accounting(self):
        learner = self.learner()
        self.calibrate(learner)
        learner.answer_from_reliability_graph("校正論点0Aの現在の結論を説明してください。")
        self.assertGreater(learner.reliability_reads, 0)
        self.assertGreater(learner.reliability_writes, 0)
        self.assertEqual(3, learner.reliability_consolidations)

        learner.reset_reliability_graph()

        self.assertEqual({}, learner._reliability)
        self.assertEqual(set(), learner._reliability_settled_targets)
        self.assertEqual(0, learner.reliability_reads)
        self.assertEqual(0, learner.reliability_writes)
        self.assertEqual(0, learner.reliability_consolidations)


if __name__ == "__main__":
    unittest.main()