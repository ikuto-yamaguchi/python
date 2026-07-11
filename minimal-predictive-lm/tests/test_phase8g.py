from __future__ import annotations

import unittest

from minimal_predictive_lm.adaptive_event_intelligence import (
    Sensor,
    best_change_point,
    exact_bounded_information_policy,
)
from minimal_predictive_lm.phase8g_experiment import run


class Phase8GTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = run()

    def test_oracle_sized_world_matches_global_optimum(self) -> None:
        mixed = self.payload["mixed_domain_induction"]
        self.assertAlmostEqual(mixed["oracle_gap"], 0.0, places=9)
        self.assertTrue(mixed["oracle_partition_exact"])

    def test_shared_event_model_recovers_cross_domain_operations(self) -> None:
        mixed = self.payload["mixed_domain_induction"]
        self.assertTrue(mixed["partition_exact"])
        self.assertEqual(mixed["unified_clusters"], 4)
        self.assertLess(
            mixed["unified_objective"],
            mixed["domain_separated_objective"],
        )

    def test_new_domain_uses_existing_operations(self) -> None:
        transfer = self.payload["new_domain_transfer"]
        self.assertEqual(transfer["assignment_accuracy"], 1.0)
        self.assertLess(
            transfer["pooled_brier"],
            transfer["calibration_only_brier"],
        )

    def test_change_point_is_compact_and_predictive(self) -> None:
        change = self.payload["change_point"]
        self.assertLessEqual(change["absolute_error"], 8)
        self.assertGreater(change["mdl_gain_bits"], 0.0)
        self.assertLess(
            change["adaptive_brier"],
            change["stationary_brier"],
        )
        self.assertLess(
            change["two_segment_summary_bits"],
            change["raw_history_bits"],
        )

    def test_exact_information_policy_dominates_baselines(self) -> None:
        information = self.payload["bounded_information"]
        self.assertTrue(information["exact_dominates_available_baselines"])
        self.assertEqual(information["oracle_gap"], 0.0)
        exact = information["policies"]["exact_bounded"]
        always = information["policies"]["always"]
        self.assertLess(exact["mean_total_cost"], always["mean_total_cost"])
        self.assertLess(exact["mean_probes"], always["mean_probes"])

    def test_change_point_rejects_short_history(self) -> None:
        split, gain = best_change_point(
            [True, False, True],
            min_segment=2,
        )
        self.assertIsNone(split)
        self.assertEqual(gain, 0.0)

    def test_exact_policy_can_decline_all_probes(self) -> None:
        expensive = (
            Sensor("expensive", 0.99, 0.01, 0.0, 100.0),
        )
        value, _ = exact_bounded_information_policy(0.95, expensive)
        self.assertEqual(value.action, "act")
        self.assertEqual(value.expected_probes, 0.0)


if __name__ == "__main__":
    unittest.main()
