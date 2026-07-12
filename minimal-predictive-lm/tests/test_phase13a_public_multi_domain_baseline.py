from __future__ import annotations

import json
import unittest

from minimal_predictive_lm.benchmark_harness import ABSTAIN_TOKEN, BenchmarkExample, build_manifest
from minimal_predictive_lm.mixed_task_learner import induce_mixed_task_model
from minimal_predictive_lm.phase12a_experiment import calibration_interactions
from minimal_predictive_lm.phase13a_experiment import failure_summary, model_fingerprint
from minimal_predictive_lm.public_benchmarks import parse_bbh_task


class Phase13aPublicMultiDomainBaselineTests(unittest.TestCase):
    def test_bbh_parser_preserves_raw_prompt_and_answer_type(self) -> None:
        payload = json.dumps(
            {
                "canary": "do not train",
                "examples": [
                    {"input": "not True is", "target": "False"},
                    {"input": "True or False is", "target": "True"},
                ],
            }
        ).encode("utf-8")
        rows = parse_bbh_task(
            payload,
            task_name="boolean_expressions",
            axis="boolean_expressions",
            answer_type="exact",
            limit=2,
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].prompt, "not True is")
        self.assertEqual(rows[0].target, "False")
        self.assertEqual(rows[0].axis, "boolean_expressions")
        self.assertEqual(rows[0].answer_type, "exact")

    def test_bbh_parser_rejects_short_source(self) -> None:
        payload = json.dumps(
            {"examples": [{"input": "x", "target": "y"}]}
        ).encode("utf-8")
        with self.assertRaises(ValueError):
            parse_bbh_task(
                payload,
                task_name="word_sorting",
                axis="word_sorting",
                answer_type="exact",
                limit=2,
            )

    def test_phase12_model_fingerprint_is_deterministic_and_domain_neutral(self) -> None:
        left = induce_mixed_task_model(calibration_interactions())
        right = induce_mixed_task_model(calibration_interactions())
        self.assertEqual(model_fingerprint(left), model_fingerprint(right))
        self.assertEqual(left.domain_specific_handlers, 0)
        self.assertEqual(right.domain_specific_handlers, 0)

    def test_failure_summary_separates_abstention_from_wrong_answer(self) -> None:
        examples = (
            BenchmarkExample("a", "axis", "p1", "1", "numeric"),
            BenchmarkExample("b", "axis", "p2", "true", "exact"),
            BenchmarkExample("c", "axis", "p3", "sorted", "exact"),
        )
        manifest = build_manifest(
            name="phase13a-unit",
            split="unit",
            source="generated",
            license_id="CC0-1.0",
            public=True,
            examples=examples,
        )
        counts = failure_summary(
            manifest,
            {"a": "1", "b": "false", "c": ABSTAIN_TOKEN},
        )
        self.assertEqual(counts, {"correct": 1, "wrong": 1, "abstained": 1})


if __name__ == "__main__":
    unittest.main()
