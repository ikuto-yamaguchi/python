from __future__ import annotations

import json
import unittest

from minimal_predictive_lm.sparc_highschool_evidence_factor_interaction import (
    EvidenceFactorInteractionConsensusLearner,
)


class FactorInteractionTest(unittest.TestCase):
    def _learner(self) -> EvidenceFactorInteractionConsensusLearner:
        return EvidenceFactorInteractionConsensusLearner(
            max_evidence_components=4,
            max_hypotheses_per_target=3,
            max_lineages=4,
            lineage_similarity_threshold=0.50,
            max_quality_weight=3,
            max_reliability_score=4,
            max_factor_score=4,
            max_factor_entries=128,
            max_interaction_score=4,
            max_interaction_entries=128,
            max_interaction_features=8,
            max_pairs_per_lineage=16,
        )

    def test_verified_context_overrides_marginal_conflict(self) -> None:
        learner = self._learner()
        learner._lineages["L"] = {"features": (11, 22, 33)}
        learner._lineage_order.append("L")
        learner._factor_reliability.update({11: 2, 22: -2})
        pairs = learner._interaction_pairs("L")
        self.assertTrue(pairs)
        learner._factor_interactions[pairs[0]] = 3

        adjustment, conflicted = learner._factor_signal("L")

        self.assertEqual(adjustment, 3)
        self.assertFalse(conflicted)
        self.assertGreater(learner.interaction_reads, 0)

    def test_materially_conflicting_interactions_remain_unresolved(self) -> None:
        learner = self._learner()
        learner._lineages["L"] = {"features": (11, 22, 33, 44)}
        learner._lineage_order.append("L")
        pairs = learner._interaction_pairs("L")
        self.assertGreaterEqual(len(pairs), 2)
        learner._factor_interactions[pairs[0]] = 2
        learner._factor_interactions[pairs[1]] = -2

        adjustment, conflicted = learner._factor_signal("L")

        self.assertEqual(adjustment, 0)
        self.assertTrue(conflicted)
        self.assertEqual(learner.interaction_conflict_abstentions, 1)

    def test_reset_and_serialization_keep_bounds_explicit(self) -> None:
        learner = self._learner()
        learner._lineages["L"] = {"features": (11, 22, 33)}
        learner._lineage_order.append("L")
        pair = learner._interaction_pairs("L")[0]
        learner._factor_interactions[pair] = 2
        payload = json.loads(learner.factor_interaction_graph_bytes().decode("utf-8"))
        self.assertTrue(payload["conditional_factor_pair_consensus"])
        self.assertEqual(payload["max_interaction_entries"], 128)
        self.assertEqual(len(payload["factor_interactions"]), 1)

        learner.reset_factor_interaction_graph()

        self.assertEqual(learner._factor_interactions, {})
        self.assertEqual(learner.interaction_reads, 0)
        self.assertEqual(learner.interaction_writes, 0)
        self.assertEqual(learner.interaction_consolidations, 0)


if __name__ == "__main__":
    unittest.main()
