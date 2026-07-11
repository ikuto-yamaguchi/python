from __future__ import annotations

import unittest

from minimal_predictive_lm.phase10a_experiment import run
from minimal_predictive_lm.stage_c_readiness import (
    CapabilityEvidence,
    build_scorecard,
    choose_next_axis,
)


class Phase10aStageCReadinessTests(unittest.TestCase):
    def test_stage_c_requires_all_six_matched_public_axes(self) -> None:
        evidence = tuple(
            CapabilityEvidence(axis, 4, 1.0, 1, "matched", True, True)
            for axis in (
                "conversation",
                "knowledge",
                "mathematics",
                "code",
                "long_context",
                "creative_writing",
            )
        )
        scorecard = build_scorecard(evidence)
        self.assertTrue(scorecard.stage_c_ready)
        self.assertTrue(scorecard.pareto_claim_allowed)

    def test_synthetic_success_cannot_authorize_parity_claim(self) -> None:
        payload = run()
        self.assertFalse(payload["scorecard"]["stage_c_ready"])
        self.assertFalse(payload["scorecard"]["pareto_claim_allowed"])
        self.assertLess(payload["scorecard"]["normalized_level"], 0.5)

    def test_next_axis_uses_value_per_upgrade_cost(self) -> None:
        scorecard = build_scorecard(
            (
                CapabilityEvidence("conversation", 3, 0.8, 1, "x"),
                CapabilityEvidence("knowledge", 3, 0.8, 1, "x"),
                CapabilityEvidence("mathematics", 0, 0.0, 0, "x"),
                CapabilityEvidence("code", 3, 0.8, 1, "x"),
                CapabilityEvidence("long_context", 3, 0.8, 1, "x"),
                CapabilityEvidence("creative_writing", 0, 0.0, 0, "x"),
            )
        )
        selected = choose_next_axis(
            scorecard,
            {
                "conversation": 10,
                "knowledge": 10,
                "mathematics": 1,
                "code": 10,
                "long_context": 10,
                "creative_writing": 2,
            },
        )
        self.assertEqual(selected, "mathematics")


if __name__ == "__main__":
    unittest.main()
