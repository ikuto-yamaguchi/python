from __future__ import annotations

import unittest

from minimal_predictive_lm.phase8c_experiment import run


class MultiRelationSemanticInductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run()

    def test_partial_and_delayed_effects_are_recovered(self) -> None:
        recovery = self.result["raw_operation_inference"]["recovery_by_kind"]
        self.assertEqual(
            recovery["set_partial"],
            {"correct": 3, "total": 3},
        )
        self.assertEqual(
            recovery["set_delayed"],
            {"correct": 3, "total": 3},
        )
        self.assertEqual(
            self.result["raw_operation_inference"]["recall"],
            1.0,
        )

    def test_robust_schema_wins_lifetime_objective(self) -> None:
        self.assertEqual(
            self.result["selected_hypothesis"],
            "robust_multi_relation_schema",
        )
        hypotheses = self.result["hypotheses"]
        robust = hypotheses["robust_multi_relation_schema"]
        self.assertEqual(robust["relation_count"], 3)
        self.assertEqual(robust["validation"]["accuracy"], 1.0)
        self.assertLess(
            robust["lifetime_objective"],
            hypotheses["support_1_schema"]["lifetime_objective"],
        )
        self.assertLess(
            robust["lifetime_objective"],
            hypotheses["exact_surface"]["lifetime_objective"],
        )

    def test_unsupported_noise_is_not_compiled(self) -> None:
        filtering = self.result["noise_filtering"]
        self.assertTrue(filtering["support_1_retains_accidental_rule"])
        self.assertTrue(filtering["robust_rejects_accidental_rule"])

    def test_cue_index_avoids_full_rule_scan(self) -> None:
        routing = self.result["routing_efficiency"]
        self.assertLess(
            routing["indexed_average_rule_checks"],
            routing["linear_scan_rule_checks_per_input"],
        )

    def test_new_relation_needs_consistent_evidence_then_recombines(self) -> None:
        bootstrap = self.result["new_relation_bootstrap"]
        self.assertEqual(bootstrap["relation_count_before"], 3)
        self.assertEqual(bootstrap["relation_count_after"], 4)
        self.assertEqual(bootstrap["rules_added"], 1)
        self.assertEqual(
            bootstrap["heldout_cross_combination"]["accuracy"],
            1.0,
        )


if __name__ == "__main__":
    unittest.main()
