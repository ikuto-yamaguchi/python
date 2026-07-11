from __future__ import annotations

import unittest

from minimal_predictive_lm.grounded_knowledge import (
    Claim,
    SourceObservation,
    build_knowledge_index,
    learn_source_trust,
)
from minimal_predictive_lm.phase10d_experiment import run


class GroundedKnowledgeTests(unittest.TestCase):
    def test_learns_source_reliability(self) -> None:
        trust = learn_source_trust(
            [
                SourceObservation("good", True),
                SourceObservation("good", True),
                SourceObservation("good", False),
                SourceObservation("weak", True),
                SourceObservation("weak", False),
                SourceObservation("weak", False),
            ]
        )
        self.assertGreater(
            trust["good"].reliability,
            trust["weak"].reliability,
        )

    def test_abstains_without_evidence(self) -> None:
        trust = learn_source_trust(
            [SourceObservation("source", True)]
        )
        index = build_knowledge_index([], trust)
        answer = index.answer("unknown", "color")
        self.assertTrue(answer.abstained)
        self.assertIsNone(answer.value)
        self.assertEqual(answer.claims_read, 0)

    def test_retains_conflicting_provenance(self) -> None:
        trust = learn_source_trust(
            [SourceObservation("a", True)] * 9
            + [SourceObservation("a", False)]
            + [SourceObservation("b", True)] * 6
            + [SourceObservation("b", False)] * 4
        )
        index = build_knowledge_index(
            [
                Claim("item", "color", "red", "a", "doc://a"),
                Claim("item", "color", "blue", "b", "doc://b"),
            ],
            trust,
        )
        answer = index.answer(
            "item",
            "color",
            confidence_threshold=0.5,
            adaptive=False,
        )
        self.assertTrue(answer.conflict)
        self.assertEqual(
            set(answer.provenance),
            {"doc://a", "doc://b"},
        )

    def test_adaptive_policy_matches_exhaustive_selection(self) -> None:
        payload = run()
        adaptive = payload["policies"]["adaptive_confidence"]
        exhaustive = payload["policies"]["indexed_exhaustive"]
        self.assertEqual(
            adaptive["selective_accuracy"],
            exhaustive["selective_accuracy"],
        )
        self.assertEqual(adaptive["coverage"], exhaustive["coverage"])
        self.assertLess(
            adaptive["claim_reads"],
            exhaustive["claim_reads"],
        )

    def test_reproducible_phase10d_results(self) -> None:
        payload = run()
        adaptive = payload["policies"]["adaptive_confidence"]
        self.assertEqual(adaptive["selective_accuracy"], 1.0)
        self.assertEqual(adaptive["claim_reads"], 2120)
        self.assertEqual(
            payload["knowledge_corpus"]["conflicting_subjects"],
            700,
        )
        self.assertEqual(
            payload["stage_c"]["readiness_points_after"],
            8,
        )
        self.assertFalse(payload["stage_c"]["stage_c_ready"])


if __name__ == "__main__":
    unittest.main()
