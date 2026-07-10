from __future__ import annotations

import unittest

from minimal_predictive_lm.phase8_experiment import run


class SemanticInductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run()

    def test_typed_program_generalizes_compositionally(self) -> None:
        base = self.result["base_evaluation"]

        self.assertEqual(self.result["selected_min_ngram"], 2)
        self.assertEqual(base["exact_compositional_targets"]["accuracy"], 0.0)
        self.assertEqual(base["slot_compositional_targets"]["accuracy"], 1.0)
        self.assertEqual(base["induced_compositional_targets"]["accuracy"], 1.0)
        self.assertGreaterEqual(base["induced_distractors"]["accuracy"], 0.875)

    def test_residuals_transfer_across_symbols_but_not_open_domain(self) -> None:
        residual = self.result["residual_round"]

        self.assertEqual(
            residual["transfer_same_constructions"]["accuracy"],
            1.0,
        )
        self.assertLessEqual(
            residual["second_lexical_shift"]["accuracy"],
            1.0 / 3.0,
        )

    def test_representation_scaling_beats_surface_enumeration(self) -> None:
        ratios = [row["ratio"] for row in self.result["scaling"]]

        self.assertGreater(ratios[0], 50.0)
        self.assertGreater(ratios[1], ratios[0])
        self.assertGreater(ratios[2], 1_000.0)


if __name__ == "__main__":
    unittest.main()
