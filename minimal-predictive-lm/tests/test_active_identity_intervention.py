import unittest

from minimal_predictive_lm.active_identity_intervention import (
    ActiveIdentityVersionSpace,
    build_report,
    make_world,
    run_identity_experiment,
)


class ActiveIdentityInterventionTests(unittest.TestCase):
    def test_separating_interventions_identify_unique_mapping(self):
        for object_count in range(2, 8):
            result = run_identity_experiment(object_count, 7, duplicated_signature=False)
            self.assertEqual(result.remaining_versions, 1)

    def test_identical_intervention_signatures_remain_ambiguous(self):
        for object_count in range(2, 8):
            result = run_identity_experiment(object_count, 19, duplicated_signature=True)
            self.assertGreater(result.remaining_versions, 1)

    def test_probe_choice_is_version_space_based(self):
        world = make_world(4, 1, duplicated_signature=False)
        model = ActiveIdentityVersionSpace(world)
        selected = model.choose_intervention()
        self.assertIsNotNone(selected)
        self.assertGreater(model.candidate_reads, 0)

    def test_claim_boundary_remains_false(self):
        report = build_report()
        self.assertEqual(report["integrated_gate_score"], 0.0)
        self.assertFalse(report["highschool_level_passed"])
        self.assertFalse(report["completion"])
        self.assertLess(report["max_model_bytes"], 1_000_000_000)


if __name__ == "__main__":
    unittest.main()
