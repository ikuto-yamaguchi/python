from __future__ import annotations

import unittest

from minimal_predictive_lm.phase17e_compositional_template_identifiability import (
    IDENTIFYING_EDGES,
    TEMPLATE_POSITIONS,
    VERBS,
    heldout_unseen_compositions,
    observations_for_edges,
)
from minimal_predictive_lm.phase17f_linear_semantic_induction import (
    InconsistentSemanticsError,
    LabeledSemanticEdge,
    contradiction_detected,
    disconnected_control,
    edges_from_observations,
    induce_linear_factorization,
    run,
    semantic_accuracy,
    synthetic_spanning_tree,
    verify_synthetic_model,
)


class Phase17fLinearSemanticInductionTests(unittest.TestCase):
    def test_small_factorization_preserves_unseen_compositions(self) -> None:
        training = observations_for_edges(IDENTIFYING_EDGES)
        model = induce_linear_factorization(
            edges_from_observations(training),
            verbs=VERBS,
            template_positions=TEMPLATE_POSITIONS,
        )
        accuracy, coverage = semantic_accuracy(model, heldout_unseen_compositions())
        self.assertTrue(model.identifiable)
        self.assertEqual(accuracy, 1.0)
        self.assertEqual(coverage, 1.0)

    def test_disconnected_graph_abstains_cross_component(self) -> None:
        model, abstains = disconnected_control()
        self.assertFalse(model.identifiable)
        self.assertTrue(abstains)

    def test_contradiction_is_rejected(self) -> None:
        self.assertTrue(contradiction_detected())
        with self.assertRaises(InconsistentSemanticsError):
            induce_linear_factorization(
                (
                    LabeledSemanticEdge("v0", 0, True),
                    LabeledSemanticEdge("v0", 0, False),
                ),
                verbs=("v0",),
                template_positions=(0,),
            )

    def test_large_connected_graph_is_linear_and_verified(self) -> None:
        verbs, templates, edges = synthetic_spanning_tree(256, 256)
        model = induce_linear_factorization(
            edges,
            verbs=verbs,
            template_positions=templates,
        )
        self.assertTrue(verify_synthetic_model(model, edges, verbs=verbs, templates=templates))
        self.assertLessEqual(model.operations, 3 * len(edges) + len(verbs) + len(templates))

    def test_all_theorem_checks_pass(self) -> None:
        payload = run()
        self.assertTrue(payload["all_theorem_checks_pass"])
        self.assertEqual(payload["scaling"][-1]["nodes"], 2048)
        self.assertTrue(payload["scaling"][-1]["verified"])


if __name__ == "__main__":
    unittest.main()
