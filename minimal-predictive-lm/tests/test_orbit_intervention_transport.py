from __future__ import annotations

import random
import unittest

from minimal_predictive_lm.orbit_intervention_transport import (
    MECHANISMS,
    OrbitLearner,
    TransitionEpisode,
    build_training,
    evaluate_scale,
    transition,
)


class OrbitInterventionTransportTests(unittest.TestCase):
    def test_discovers_constant_mechanism_orbits(self) -> None:
        small = evaluate_scale(4, 5004)
        large = evaluate_scale(64, 5064)
        self.assertEqual(small.orbit_count, len(MECHANISMS))
        self.assertEqual(large.orbit_count, len(MECHANISMS))
        self.assertEqual(small.orbit_count, large.orbit_count)
        self.assertGreater(large.reuse_ratio, 0.99)

    def test_role_reversal_merges_transfer_surfaces(self) -> None:
        learner = OrbitLearner(minimum_support=2, minimum_fraction=0.75)
        rows = [
            row
            for row in build_training(12, 7000)
            if "移す" in row.text or "受け取る" in row.text
        ]
        learner.fit(rows)
        self.assertEqual(len(learner.orbits), 1)
        self.assertEqual(len(next(iter(learner.orbits.values())).surfaces), 2)

    def test_one_shot_grounding_transports_to_new_world(self) -> None:
        learner = OrbitLearner(minimum_support=3, minimum_fraction=0.75)
        learner.fit(build_training(16, 8000))
        rng = random.Random(8001)
        template = str(MECHANISMS["mirror"]["heldout"])
        demo = transition("mirror", template, rng, 1, noise_entities=5)
        self.assertIsNotNone(learner.ground_surface_once(demo))
        test = transition("mirror", template, rng, 2, noise_entities=11)
        prediction = learner.predict(test.text, test.before)
        self.assertEqual(prediction.after, dict(test.after))
        for key in test.before:
            if key.startswith("雑音"):
                self.assertEqual(prediction.after[key], test.before[key])

    def test_accidental_alias_abstains_then_resolves(self) -> None:
        learner = OrbitLearner(minimum_support=2, minimum_fraction=0.75)
        learner.fit(build_training(24, 9000))
        entity = "曖昧対象"
        first = TransitionEpisode(
            f"{entity} へ 5 を新語処理する",
            {entity: 0},
            {entity: 5},
        )
        self.assertIsNone(learner.ground_surface_once(first))
        second = TransitionEpisode(
            f"{entity} へ 3 を新語処理する",
            {entity: 7},
            {entity: 10},
        )
        self.assertIsNotNone(learner.ground_surface_once(second))
        result = learner.predict(f"{entity} へ 11 を新語処理する", {entity: 20})
        self.assertEqual(result.after, {entity: 31})

    def test_noise_and_depth_sixteen(self) -> None:
        result = evaluate_scale(64, 10064, noise_rate=0.08)
        self.assertEqual(result.orbit_count, len(MECHANISMS))
        self.assertGreaterEqual(result.heldout_accuracy, 0.95)
        self.assertGreaterEqual(result.depth16_accuracy, 0.95)
        self.assertGreater(result.residual_rate, 0.04)
        self.assertLess(result.residual_rate, 0.12)

    def test_serialization_remains_small(self) -> None:
        learner = OrbitLearner(minimum_support=3, minimum_fraction=0.75)
        learner.fit(build_training(64, 11000))
        payload = learner.to_bytes()
        self.assertLess(len(payload), 10_000)
        self.assertIn(b"orbit:", payload)


if __name__ == "__main__":
    unittest.main()
