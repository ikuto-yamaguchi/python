import unittest

from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_evidence_factor_reliability_gate import _strong, _weak
from minimal_predictive_lm.sparc_highschool_interaction_support import (
    EvidenceFactorInteractionSupportLearner,
)
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus


class InteractionSupportTest(unittest.TestCase):
    def _learner(self):
        learner = EvidenceFactorInteractionSupportLearner(
            max_evidence_components=10,
            max_hypotheses_per_target=3,
            max_lineages=16,
            lineage_similarity_threshold=0.50,
            max_quality_weight=3,
            max_reliability_score=4,
            max_factor_score=4,
            max_factor_entries=2048,
            max_interaction_score=4,
            max_interaction_entries=4096,
            max_interaction_features=64,
            max_pairs_per_lineage=512,
            min_interaction_targets=2,
        )
        learner.learn_independent_documents(_corpus(), min_support=4)
        learner.learn_independent_numeric_documents(_numeric_corpus())
        learner.learn_long_chronological_documents(_long_corpus())
        return learner

    @staticmethod
    def _note(tag):
        return f"{tag}方式{tag}回路{tag}環境{tag}条件{tag}記録"

    def _resolve(self, learner, target, truth, wrong, tag):
        learner.ingest_interaction_verified_hypothesis(
            _strong(target, wrong, 3, self._note(tag))
        )
        learner.ingest_interaction_verified_hypothesis(
            _strong(target, truth, 3, self._note(tag))
        )
        learner.ingest_interaction_verified_hypothesis(
            _weak(target, truth, 3, f"独立再測定{target}")
        )
        self.assertTrue(learner.consolidate_verified_target_interactions(target))

    def test_single_resolved_target_cannot_activate_interaction_transfer(self):
        learner = self._learner()
        self._resolve(learner, "単発校正論点", 20, 28, "紫")
        lineage = next(
            lineage_id
            for lineage_id, row in learner._lineages.items()
            if any(learner._interaction_support.get(pair, 0) == 1 for pair in learner._interaction_pairs(lineage_id))
        )
        adjustment, conflict, active = learner._interaction_signal(lineage)
        self.assertEqual((adjustment, conflict, active), (0, False, 0))
        self.assertGreater(learner.low_support_interactions_ignored, 0)

    def test_repeated_resolved_targets_activate_same_interaction(self):
        learner = self._learner()
        self._resolve(learner, "反復校正論点A", 20, 28, "緑")
        self._resolve(learner, "反復校正論点B", 21, 29, "緑")
        supports = list(learner._interaction_support.values())
        self.assertTrue(any(value >= 2 for value in supports))
        self.assertLessEqual(max(supports), learner.max_interaction_support)
        payload = learner.factor_interaction_support_graph_bytes()
        self.assertLessEqual(len(payload), 262144)

    def test_reset_and_pruning_keep_support_graph_bounded(self):
        learner = self._learner()
        self._resolve(learner, "境界校正論点A", 20, 28, "橙")
        learner.factor_interaction_support_graph_bytes()
        self.assertLessEqual(len(learner._interaction_support), learner.max_interaction_entries)
        self.assertTrue(set(learner._interaction_support).issubset(learner._factor_interactions))
        learner.reset_factor_interaction_graph()
        self.assertEqual(learner._interaction_support, {})
        self.assertEqual(learner.interaction_support_reads, 0)
        self.assertEqual(learner.interaction_support_writes, 0)


if __name__ == "__main__":
    unittest.main()
