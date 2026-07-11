from __future__ import annotations

import unittest

from minimal_predictive_lm.phase8e_experiment import run


class ResidualPartitionSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run()

    def test_matches_exhaustive_oracle_on_small_worlds(self) -> None:
        self.assertTrue(
            self.result["conclusion"]["oracle_gap_zero_for_exhaustive_cases"]
        )
        for case in self.result["cases"][:2]:
            self.assertIsNotNone(case["oracle"])
            self.assertEqual(case["oracle"]["residual_objective_gap"], 0)
            self.assertTrue(case["oracle"]["selected_exact"])

    def test_recovers_hidden_relations_and_transfers(self) -> None:
        self.assertTrue(
            self.result["conclusion"]["all_hidden_partitions_recovered"]
        )
        self.assertTrue(self.result["conclusion"]["all_validation_exact"])
        for case in self.result["cases"]:
            residual = case["residual_search"]
            self.assertEqual(
                residual["selected_clusters"],
                case["hidden_relations"],
            )
            self.assertEqual(residual["selected_train_errors"], 0)
            self.assertEqual(residual["selected_validation_accuracy"], 1.0)

    def test_search_does_not_enumerate_bell_space(self) -> None:
        cases = {case["templates"]: case for case in self.result["cases"]}
        self.assertLess(cases[8]["residual_search"]["evaluated_partitions"], 50)
        self.assertEqual(cases[8]["bell_partitions"], 4_140)
        self.assertLess(cases[12]["residual_search"]["evaluated_partitions"], 100)
        self.assertEqual(cases[12]["bell_partitions"], 4_213_597)
        self.assertLess(cases[32]["residual_search"]["evaluated_partitions"], 200)
        self.assertGreater(cases[32]["bell_partitions"], 10**20)

    def test_search_cost_is_reported_and_amortized_not_hidden(self) -> None:
        for case in self.result["cases"]:
            residual = case["residual_search"]
            self.assertGreater(residual["fit_candidate_checks"], 0)
            amortized = residual["amortized_fit_checks"]
            self.assertGreater(amortized["1"], amortized["100"])
            self.assertGreater(amortized["100"], amortized["10000"])


if __name__ == "__main__":
    unittest.main()
