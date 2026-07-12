from __future__ import annotations

import unittest

from minimal_predictive_lm.phase17d_semantic_identifiability import (
    VERBS,
    all_hypotheses,
    behavior_classes,
    exact_memorizer_coverage,
    heldout_role_reversal_pairs,
    identifying_interventions,
    non_identifying_observations,
    representation_accuracy_upper_bound,
    role_intervention_consistency,
    run,
    semantic_accuracy,
    version_space,
)


class Phase17dSemanticIdentifiabilityTests(unittest.TestCase):
    def test_symmetric_observations_are_non_identifying(self) -> None:
        prior = all_hypotheses()
        surviving = version_space(non_identifying_observations(), prior)
        self.assertGreater(len(behavior_classes(surviving)), 1)

    def test_interventions_identify_semantics_modulo_gauge(self) -> None:
        prior = all_hypotheses()
        surviving = version_space(identifying_interventions(), prior)
        self.assertEqual(len(surviving), 2)
        self.assertEqual(len(behavior_classes(surviving)), 1)

    def test_surface_bound_and_semantic_generalization(self) -> None:
        training = identifying_interventions()
        heldout = heldout_role_reversal_pairs()
        surviving = version_space(training)
        learned = surviving[0]

        self.assertEqual(representation_accuracy_upper_bound(heldout), 0.5)
        self.assertEqual(exact_memorizer_coverage(training, heldout), 0.0)
        self.assertEqual(semantic_accuracy(learned, heldout), 1.0)
        self.assertEqual(role_intervention_consistency(learned, heldout), 1.0)

    def test_information_lower_bound_matches_informative_interventions(self) -> None:
        payload = run()
        self.assertEqual(
            payload["theory"]["information_lower_bound_bits"],
            len(VERBS),
        )
        self.assertEqual(
            payload["theory"]["minimum_informative_interventions"],
            len(VERBS),
        )
        self.assertTrue(payload["all_theorem_checks_pass"])


if __name__ == "__main__":
    unittest.main()
