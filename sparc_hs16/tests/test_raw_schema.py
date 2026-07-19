from __future__ import annotations

import unittest

from sparc_hs16.raw_schema import (
    RawCausalSchemaModel,
    hidden_examples,
    role_calibration_texts,
    training_examples,
)


class RawCausalSchemaTests(unittest.TestCase):
    def build_model(self, worlds: int = 64) -> RawCausalSchemaModel:
        model = RawCausalSchemaModel(budget_mb=16)
        model.fit_roles(role_calibration_texts())
        model.fit_context_gates(list(training_examples(64)))
        for text, target in training_examples(worlds):
            model.learn(text, target)
        return model

    def test_distributional_paraphrase_roles_are_shared(self) -> None:
        model = RawCausalSchemaModel(budget_mb=16)
        model.fit_roles(role_calibration_texts())
        roles = model.roles.anchor_to_role
        self.assertEqual(roles["基準"], roles["判断基準"])
        self.assertEqual(roles["噂"], roles["参考"])

    def test_context_gate_discovers_conditional_relevance(self) -> None:
        model = RawCausalSchemaModel(budget_mb=16)
        model.fit_roles(role_calibration_texts())
        model.fit_context_gates(list(training_examples(64)))
        self.assertEqual(len(model.gate.schemas), 2)
        schemas = list(model.gate.schemas.values())
        self.assertTrue(all(purity == 1.0 for _, _, purity, _ in schemas))

    def test_unseen_order_and_held_combination(self) -> None:
        model = self.build_model()
        rows = list(hidden_examples(64, start=0, count=64))
        correct = sum(model.predict(text) == target for text, target in rows)
        self.assertEqual(correct, len(rows))

    def test_managed_storage_matches_budget(self) -> None:
        model = RawCausalSchemaModel(budget_mb=16)
        self.assertEqual(model.managed_storage_bytes, 16 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
