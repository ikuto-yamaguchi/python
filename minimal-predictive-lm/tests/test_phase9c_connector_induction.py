from __future__ import annotations

import unittest

from minimal_predictive_lm.connector_induction import (
    ConnectorObservation,
    induce_connector_lexicon,
)
from minimal_predictive_lm.phase9c_experiment import run


class Phase9cConnectorInductionTests(unittest.TestCase):
    def test_true_condition_is_induced_from_execution_effect(self) -> None:
        result = induce_connector_lexicon(
            [
                ConnectorObservation("opaque-a", True, True, False, False, False, False),
                ConnectorObservation("opaque-a", False, False, False, False, False, False),
            ]
        )
        self.assertEqual(result.lexicon.role("opaque-a"), "CONDITION_TRUE")

    def test_false_condition_is_induced(self) -> None:
        result = induce_connector_lexicon(
            [
                ConnectorObservation("opaque-b", True, False, False, False, False, False),
                ConnectorObservation("opaque-b", False, True, False, False, False, False),
            ]
        )
        self.assertEqual(result.lexicon.role("opaque-b"), "CONDITION_FALSE")

    def test_shifted_connector_roles_and_graphs(self) -> None:
        payload = run()
        self.assertEqual(payload["base_induction"]["mapping_accuracy"], 1.0)
        self.assertEqual(payload["shifted_induction"]["exact_surface_accuracy"], 0.0)
        self.assertEqual(payload["shifted_induction"]["interaction_induced_accuracy"], 1.0)
        self.assertEqual(payload["graph_transfer"]["event_recall"], 1.0)
        self.assertEqual(payload["graph_transfer"]["edge_recall"], 1.0)
        self.assertEqual(payload["graph_transfer"]["unresolved"], 0)


if __name__ == "__main__":
    unittest.main()
