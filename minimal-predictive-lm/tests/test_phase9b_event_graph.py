from __future__ import annotations

import unittest

from minimal_predictive_lm.hierarchical_event_graph import (
    execute_graph_workflow,
    parse_event_graph,
)
from minimal_predictive_lm.phase9a_experiment import TRAINING_SPECIFICATION, _traces
from minimal_predictive_lm.phase9b_experiment import BENCHMARK, run
from minimal_predictive_lm.raw_event_program import induce_raw_grounder


class Phase9bHierarchicalEventGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.grounder = induce_raw_grounder(_traces(TRAINING_SPECIFICATION))

    def test_conditional_repair_builds_hierarchical_graph(self) -> None:
        graph = parse_event_graph(BENCHMARK[0]["raw"], self.grounder)
        self.assertEqual(
            graph.operations(),
            ("SET", "VERIFY", "RETRACT", "SET", "VERIFY", "EMIT"),
        )
        relations = {edge.relation for edge in graph.edges}
        self.assertIn("CONDITION_TRUE", relations)
        self.assertIn("REFERS_TO", relations)
        self.assertIn("CONTENT", relations)
        self.assertFalse(graph.unresolved)

    def test_mixed_report_has_emit_with_embedded_proposition(self) -> None:
        graph = parse_event_graph(BENCHMARK[1]["raw"], self.grounder)
        self.assertEqual(graph.operations(), ("EMIT",))
        propositions = graph.proposition_nodes()
        self.assertEqual(len(propositions), 1)
        self.assertEqual(propositions[0].label, "TEST_STATUS")
        self.assertEqual(propositions[0].arguments, ("PASS",))
        self.assertTrue(any(edge.relation == "CONTENT" for edge in graph.edges))

    def test_negative_action_is_represented_without_deleting_the_event(self) -> None:
        graph = parse_event_graph(BENCHMARK[2]["raw"], self.grounder)
        retract = next(node for node in graph.event_nodes() if node.label == "RETRACT")
        self.assertFalse(retract.polarity)
        self.assertTrue(any(edge.relation == "CONDITION_FALSE" for edge in graph.edges))

    def test_reference_edge_points_to_prior_change(self) -> None:
        graph = parse_event_graph(BENCHMARK[4]["raw"], self.grounder)
        reference_edges = [edge for edge in graph.edges if edge.relation == "REFERS_TO"]
        self.assertEqual(len(reference_edges), 1)
        source = graph.nodes[reference_edges[0].source]
        target = graph.nodes[reference_edges[0].target]
        self.assertEqual(source.label, "RETRACT")
        self.assertEqual(target.label, "SET")

    def test_graph_executes_failure_rollback_repair(self) -> None:
        graph = parse_event_graph(BENCHMARK[0]["raw"], self.grounder)
        result = execute_graph_workflow(graph)
        self.assertEqual(
            result.executed,
            ("SET", "VERIFY", "RETRACT", "SET", "VERIFY", "EMIT"),
        )
        self.assertEqual(result.state.expression, "x * x + 1")
        self.assertEqual(result.state.last_test, "PASS")
        self.assertEqual(result.rollbacks, 1)
        self.assertEqual(result.tests, 2)

    def test_graph_outperforms_single_label_without_flat_handoffs(self) -> None:
        payload = run()
        benchmark = payload["benchmark"]
        memory = payload["memory"]
        self.assertEqual(benchmark["graph_event_recall"], 1.0)
        self.assertEqual(benchmark["graph_edge_recall"], 1.0)
        self.assertLess(
            benchmark["single_label_event_recall"],
            benchmark["graph_event_recall"],
        )
        self.assertLess(
            memory["graph_plus_provenance_bits"],
            memory["flat_json_handoff_bits"],
        )

    def test_representation_invention_is_cost_gated(self) -> None:
        invention = run()["representation_invention"]
        self.assertIsNotNone(invention["break_even_reuses"])
        self.assertGreater(invention["additional_representation_bits"], 0)
        self.assertLessEqual(invention["break_even_reuses"], 16)


if __name__ == "__main__":
    unittest.main()
