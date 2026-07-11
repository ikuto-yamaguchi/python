from __future__ import annotations

import unittest

from minimal_predictive_lm.phase8d_experiment import run


class LatentRelationPartitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run()

    def test_true_effect_remains_in_candidate_set(self) -> None:
        self.assertEqual(self.result["effect_candidate_recall"], 1.0)
        self.assertEqual(self.result["ambiguous_traces"], 1)
        self.assertTrue(self.result["ambiguous_trace_resolved"])

    def test_hidden_relation_partition_and_lags_are_recovered(self) -> None:
        search = self.result["partition_search"]
        self.assertEqual(search["evaluated_partitions"], 15)
        self.assertEqual(search["selected_cluster_count"], 2)
        self.assertTrue(search["selected_partition_exact"])
        self.assertEqual(search["selected_train_errors"], 0)
        self.assertEqual(
            sorted(item["lag"] for item in search["selected_relations"]),
            [1, 2],
        )

    def test_shared_relation_transfers_to_new_entities(self) -> None:
        search = self.result["partition_search"]
        self.assertEqual(search["new_entity_validation_accuracy"], 1.0)
        hypotheses = self.result["representative_hypotheses"]
        selected = hypotheses["selected_two_relation"]
        self.assertLess(
            selected["objective"],
            hypotheses["merged_one_relation"]["objective"],
        )
        self.assertLess(
            selected["objective"],
            hypotheses["flat_four_relation"]["objective"],
        )

    def test_exhaustive_search_is_explicitly_non_scalable(self) -> None:
        rows = self.result["partition_search_scaling"]
        self.assertEqual(rows[0], {"templates": 4, "set_partitions": 15})
        self.assertGreater(rows[-1]["set_partitions"], 4_000_000)


if __name__ == "__main__":
    unittest.main()
