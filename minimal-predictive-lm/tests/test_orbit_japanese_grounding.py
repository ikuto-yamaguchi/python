from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from minimal_predictive_lm.orbit_japanese_grounding import (
    DiscourseOrbit,
    FOLLOWUPS,
    GroundedOrbit,
    accuracy,
    dialogue_accuracy,
    make_dialogue,
    make_episode,
    run,
)


class GroundedOrbitTest(unittest.TestCase):
    def test_unseen_surface_and_negation_execute(self) -> None:
        rng = random.Random(7)
        model = GroundedOrbit()
        training = [make_episode(rng, train=True) for _ in range(120)]
        training += [make_episode(rng, train=True, noop=True) for _ in range(40)]
        model.fit(training)
        self.assertFalse(model.failures)
        self.assertEqual(1.0, accuracy(model, [make_episode(rng, train=False, recombined=True) for _ in range(80)]))
        self.assertEqual(
            1.0,
            accuracy(
                model,
                [make_episode(rng, train=False, noop=True, recombined=True) for _ in range(80)],
            ),
        )

    def test_dialogue_binding_algebra(self) -> None:
        rng = random.Random(11)
        model = DiscourseOrbit()
        training = []
        for operator in FOLLOWUPS:
            training.extend(make_dialogue(rng, operator, train=True) for _ in range(24))
        model.fit(training)
        self.assertFalse(model.failures)
        for operator in FOLLOWUPS:
            heldout = [make_dialogue(rng, operator, train=False) for _ in range(80)]
            self.assertEqual(1.0, dialogue_accuracy(model, heldout), operator)

    def test_report_refuses_completion_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = run(Path(directory), seed=13)
        self.assertFalse(report["highschool_level_passed"])
        self.assertTrue(all(report["checks"].values()))


if __name__ == "__main__":
    unittest.main()
