from __future__ import annotations

import unittest

from minimal_predictive_lm.phase17d_semantic_identifiability import (
    exact_memorizer_coverage,
    representation_accuracy_upper_bound,
)
from minimal_predictive_lm.phase17e_compositional_template_identifiability import (
    IDENTIFYING_EDGES,
    NON_IDENTIFYING_EDGES,
    all_hypotheses,
    behavior_classes,
    heldout_unseen_compositions,
    observation_graph_components,
    observations_for_edges,
    role_intervention_consistency,
    run,
    semantic_accuracy,
    version_space,
)


class Phase17eCompositionalTemplateIdentifiabilityTests(unittest.TestCase):
    def test_disconnected_graph_is_non_identifying(self) -> None:
        observations = observations_for_edges(NON_IDENTIFYING_EDGES)
        surviving = version_space(observations, all_hypotheses())
        components = observation_graph_components(NON_IDENTIFYING_EDGES)
        self.assertGreater(len(components), 1)
        self.assertEqual(
            len(behavior_classes(surviving)),
            2 ** (len(components) - 1),
        )

    def test_connected_spanning_tree_identifies_modulo_gauge(self) -> None:
        observations = observations_for_edges(IDENTIFYING_EDGES)
        surviving = version_space(observations, all_hypotheses())
        self.assertEqual(len(observation_graph_components(IDENTIFYING_EDGES)), 1)
        self.assertEqual(len(surviving), 2)
        self.assertEqual(len(behavior_classes(surviving)), 1)

    def test_unseen_verb_template_compositions_generalize(self) -> None:
        training = observations_for_edges(IDENTIFYING_EDGES)
        heldout = heldout_unseen_compositions()
        learned = version_space(training)[0]

        self.assertEqual(semantic_accuracy(learned, heldout), 1.0)
        self.assertEqual(representation_accuracy_upper_bound(heldout), 0.5)
        self.assertEqual(exact_memorizer_coverage(training, heldout), 0.0)
        self.assertEqual(role_intervention_consistency(learned, heldout), 1.0)

    def test_all_theorem_checks_pass(self) -> None:
        payload = run()
        self.assertTrue(payload["all_theorem_checks_pass"])
        self.assertEqual(
            payload["theory"]["minimum_connected_observation_edges"],
            len(IDENTIFYING_EDGES),
        )


if __name__ == "__main__":
    unittest.main()
