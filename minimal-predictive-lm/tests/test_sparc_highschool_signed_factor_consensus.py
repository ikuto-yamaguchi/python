import unittest

from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_evidence_factor_reliability import (
    EvidenceFactorReliabilityConsensusLearner,
)
from minimal_predictive_lm.sparc_highschool_evidence_factor_reliability_gate import _strong, _weak
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


class SignedFactorConsensusTests(unittest.TestCase):
    def _learner(self) -> EvidenceFactorReliabilityConsensusLearner:
        learner = EvidenceFactorReliabilityConsensusLearner(
            max_evidence_components=10,
            max_hypotheses_per_target=3,
            max_lineages=16,
            lineage_similarity_threshold=0.50,
            max_quality_weight=3,
            max_reliability_score=4,
            max_factor_score=4,
            max_factor_entries=2048,
        )
        learner.learn_independent_documents(_corpus(), min_support=4)
        learner.learn_independent_numeric_documents(_numeric_corpus())
        learner.learn_long_chronological_documents(_long_corpus())
        return learner

    def test_verified_contradiction_suppresses_stronger_local_evidence(self):
        learner = self._learner()
        bad_factor = "共通の未校正推定回路による間接算出"
        for index in range(4):
            target = f"符号校正論点{index}"
            truth = 11 + index
            add = 2 + index % 2
            learner.ingest_factor_verified_hypothesis(
                _strong(target, truth + 7, add, f"誤差系列{index}と{bad_factor}")
            )
            learner.ingest_factor_verified_hypothesis(
                _strong(target, truth, add, f"独立光学監査{index}による直接再測定")
            )
            learner.ingest_factor_verified_hypothesis(
                _weak(target, truth, add, f"独立重量監査{index}による別系統確認")
            )
            self.assertTrue(learner.consolidate_verified_target_factors(target))

        target = "未知符号論点"
        truth = 23
        wrong = 31
        add = 3
        learner.ingest_factor_verified_hypothesis(
            _weak(target, truth, add, "新設観測班による単一点の直接確認")
        )
        learner.ingest_factor_verified_hypothesis(
            _strong(target, wrong, add, f"都市集計資料と{bad_factor}")
        )
        result = learner.answer_from_factor_reliability_graph(
            f"{target}の現在の結論を説明してください。"
        )
        selected = {(row[2], row[3]) for row in result.selected_states}
        self.assertTrue(result.accepted)
        self.assertIn((0, truth), selected)
        self.assertNotIn((0, wrong), selected)
        self.assertTrue(any(score < 0 for score in learner._factor_reliability.values()))
        self.assertIn("支持と反証", result.answer)

    def test_signed_graph_remains_bounded_and_serializable(self):
        learner = self._learner()
        learner._factor_reliability.update({index: (-1 if index % 2 else 1) for index in range(2500)})
        payload = learner.factor_reliability_graph_bytes()
        self.assertLessEqual(len(learner._factor_reliability), learner.max_factor_entries)
        self.assertLess(len(payload), 131072)


if __name__ == "__main__":
    unittest.main()
