from __future__ import annotations

import unittest

from minimal_predictive_lm.residual_lm import (
    CompiledResidualLM,
    SparseResidualTrainer,
    make_micro_corpus,
)


class ResidualLMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.training = make_micro_corpus(line_count=500, seed=1)
        cls.test = make_micro_corpus(line_count=100, seed=2)
        split = int(len(cls.training) * 0.8)
        trainer = SparseResidualTrainer(
            maximum_order=5,
            minimum_fit_count=3,
            minimum_selection_count=2,
        )
        trainer.fit(cls.training[:split], cls.training[split:])
        trainer.refit(cls.training)
        cls.rule_count = len(trainer.rules)
        cls.model = trainer.compile(cls.training, shortcut_budget=64)

    def test_model_is_sparse_and_compact(self) -> None:
        blob = self.model.to_bytes()
        self.assertGreater(self.rule_count, 1)
        self.assertLess(len(blob), 8_192)
        self.assertLessEqual(self.model.runtime_state_bits, 16)

    def test_binary_round_trip_preserves_prediction(self) -> None:
        before = self.model.evaluate(self.test)
        restored = CompiledResidualLM.from_bytes(self.model.to_bytes())
        after = restored.evaluate(self.test)
        self.assertAlmostEqual(before["bpb"], after["bpb"], places=12)
        self.assertAlmostEqual(
            before["average_transition_checks"],
            after["average_transition_checks"],
            places=12,
        )
        self.assertLess(before["average_transition_checks"], 2.0)

    def test_generation_is_valid_utf8(self) -> None:
        prompt = "ユーザー: "
        generated = self.model.generate(prompt, byte_count=100, seed=4, enforce_utf8=True)
        self.assertTrue(generated.startswith(prompt))
        self.assertEqual(generated, generated.encode("utf-8").decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
