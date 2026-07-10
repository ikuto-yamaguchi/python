from __future__ import annotations

import unittest

from minimal_predictive_lm.phase8b_experiment import run


class LatentSemanticInductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run()

    def test_operations_and_roles_are_inferred_without_labels(self) -> None:
        inferred = self.result["operation_inference"]
        roles = self.result["discovered_roles"]

        self.assertEqual(inferred["accuracy_against_hidden_trace_generator"], 1.0)
        self.assertEqual(inferred["operation_set"], ["get", "set"])
        self.assertEqual(roles["purity"]["key_role"], 1.0)
        self.assertEqual(roles["purity"]["value_role"], 1.0)

    def test_two_role_hypothesis_wins_global_objective(self) -> None:
        self.assertEqual(self.result["selected_hypothesis"], "two_latent_roles")
        hypotheses = self.result["hypotheses"]
        self.assertEqual(hypotheses["two_latent_roles"]["validation"]["accuracy"], 1.0)
        self.assertLess(
            hypotheses["two_latent_roles"]["lifetime_objective"],
            hypotheses["untyped_symbols"]["lifetime_objective"],
        )
        self.assertLess(
            hypotheses["two_latent_roles"]["lifetime_objective"],
            hypotheses["exact_surface"]["lifetime_objective"],
        )

    def test_new_symbols_reuse_rules_without_rule_growth(self) -> None:
        bootstrap = self.result["new_symbol_bootstrap"]
        self.assertEqual(bootstrap["rule_bits_added"], 0)
        self.assertEqual(bootstrap["evaluation"]["accuracy"], 1.0)

    def test_state_operations_remove_unnecessary_surface_distinctions(self) -> None:
        factor = self.result["operation_factorization"]
        self.assertLess(
            factor["state_operation_program_bits"],
            factor["surface_intent_program_bits"],
        )
        self.assertEqual(factor["state_operation_validation"]["accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
