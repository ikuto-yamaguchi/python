from __future__ import annotations

import json
import unittest

from minimal_predictive_lm.benchmark_harness import ABSTAIN_TOKEN, BenchmarkExample, build_manifest
from minimal_predictive_lm.phase15a_experiment import axis_scores, capability_gap_inventory
from minimal_predictive_lm.phase15a_public_benchmarks import PHASE15A_TASKS
from minimal_predictive_lm.public_benchmarks import parse_bbh_task


class Phase15aUnseenPublicBaselineTests(unittest.TestCase):
    def test_suite_has_five_distinct_pinned_capabilities(self) -> None:
        self.assertEqual(len(PHASE15A_TASKS), 5)
        axes = {str(config["axis"]) for config in PHASE15A_TASKS.values()}
        self.assertEqual(len(axes), 5)
        for config in PHASE15A_TASKS.values():
            sha = str(config["blob_sha1"])
            self.assertEqual(len(sha), 40)
            int(sha, 16)

    def test_generic_bbh_parser_preserves_multiple_choice_and_sequence_targets(self) -> None:
        payload = json.dumps(
            {
                "examples": [
                    {"input": "Question\nOptions:\n(A) x\n(B) y", "target": "(B)"},
                    {"input": "Input: [ [", "target": "] ]"},
                ]
            }
        ).encode("utf-8")
        choice = parse_bbh_task(
            payload,
            task_name="unit",
            axis="logical_ordering",
            answer_type="exact",
            limit=1,
        )
        sequence = parse_bbh_task(
            payload,
            task_name="unit",
            axis="stack_completion",
            answer_type="exact",
            limit=2,
        )
        self.assertEqual(choice[0].target, "(B)")
        self.assertEqual(sequence[1].target, "] ]")

    def test_axis_scores_separate_wrong_answers_from_abstention(self) -> None:
        rows = (
            BenchmarkExample("a", "date_understanding", "p", "(A)", "exact"),
            BenchmarkExample("b", "date_understanding", "q", "(B)", "exact"),
            BenchmarkExample("c", "stack_completion", "r", "]", "exact"),
        )
        manifest = build_manifest(
            name="phase15a-unit",
            split="unit",
            source="generated",
            license_id="CC0-1.0",
            public=True,
            examples=rows,
        )
        scores = axis_scores(manifest, {"a": "(A)", "b": "(C)", "c": ABSTAIN_TOKEN})
        self.assertEqual(scores["date_understanding"]["correct"], 1)
        self.assertEqual(scores["date_understanding"]["wrong"], 1)
        self.assertEqual(scores["stack_completion"]["abstained"], 1)

    def test_gap_inventory_is_mechanism_oriented_not_task_solver_names(self) -> None:
        inventory = capability_gap_inventory()
        self.assertEqual(set(inventory), {str(config["axis"]) for config in PHASE15A_TASKS.values()})
        self.assertIn("pushdown stack", inventory["stack_completion"])
        self.assertIn("mutable bijection", inventory["state_permutation_tracking"])


if __name__ == "__main__":
    unittest.main()
