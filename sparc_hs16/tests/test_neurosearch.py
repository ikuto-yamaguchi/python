from __future__ import annotations

import unittest

from sparc_hs16.neurosearch import (
    BrainPrototype,
    PROTOTYPE_CONFIGS,
    evaluate_prototype,
)


class NeurosearchTests(unittest.TestCase):
    def config(self, name: str):
        return next(config for config in PROTOTYPE_CONFIGS if config.name == name)

    def test_real_fixed_memory_budget(self) -> None:
        model = BrainPrototype(self.config("planning_hybrid"), 1)
        self.assertEqual(model.budget_bytes, 1024 * 1024)
        self.assertEqual(model.allocated_cortex_bytes, int(1024 * 1024 * 0.75))
        self.assertLess(model.allocated_cortex_bytes, model.budget_bytes)

    def test_hippocampus_supports_one_shot_exception(self) -> None:
        result = evaluate_prototype(self.config("hippocampal_one_shot"), 1, epochs=2)
        self.assertEqual(result.one_shot_accuracy, 1.0)

    def test_planning_replay_propagates_delayed_reward(self) -> None:
        result = evaluate_prototype(self.config("planning_hybrid"), 1, epochs=2)
        self.assertEqual(result.delayed_planning_accuracy, 1.0)

    def test_hybrid_beats_atomic_ablation(self) -> None:
        atomic = evaluate_prototype(self.config("atomic_cortex"), 1, epochs=2)
        hybrid = evaluate_prototype(self.config("planning_hybrid"), 1, epochs=2)
        self.assertGreaterEqual(hybrid.composite_score - atomic.composite_score, 0.25)
        self.assertGreater(hybrid.compositional_accuracy, atomic.compositional_accuracy)


if __name__ == "__main__":
    unittest.main()
