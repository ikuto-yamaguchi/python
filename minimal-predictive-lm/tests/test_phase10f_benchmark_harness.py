from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import tempfile
import unittest

from minimal_predictive_lm.benchmark_harness import (
    BenchmarkExample,
    RunPolicy,
    build_manifest,
    compare_reports,
    load_jsonl_manifest,
    model_request,
)
from minimal_predictive_lm.phase10f_experiment import run, smoke_manifest


class BenchmarkHarnessTests(unittest.TestCase):
    def test_model_request_never_contains_targets(self) -> None:
        manifest = smoke_manifest()
        request = model_request(manifest, RunPolicy())
        self.assertTrue(request["examples"])
        self.assertTrue(all("target" not in item for item in request["examples"]))

    def test_checksum_is_stable_and_order_sensitive(self) -> None:
        examples = (
            BenchmarkExample("a", "mathematics", "1+1", "2", "numeric"),
            BenchmarkExample("b", "knowledge", "x", "y", "exact"),
        )
        left = build_manifest(
            name="x",
            split="test",
            source="public://x",
            license_id="test",
            public=True,
            examples=examples,
        )
        right = build_manifest(
            name="x",
            split="test",
            source="public://x",
            license_id="test",
            public=True,
            examples=reversed(examples),
        )
        self.assertNotEqual(left.sha256, right.sha256)

    def test_jsonl_checksum_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bench.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "id": "a",
                        "axis": "mathematics",
                        "prompt": "1+1",
                        "target": "2",
                        "answer_type": "numeric",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_jsonl_manifest(
                    path,
                    name="x",
                    split="test",
                    source="public://x",
                    license_id="test",
                    public=True,
                    expected_sha256="0" * 64,
                )

    def test_phase10f_smoke_and_resource_measurement(self) -> None:
        payload = run()
        score = payload["mpm_smoke"]["score"]
        resources = payload["mpm_smoke"]["resources"]
        self.assertEqual(score["overall_accuracy"], 1.0)
        self.assertEqual(score["coverage"], 1.0)
        self.assertGreater(resources["model_bytes"], 0)
        self.assertGreater(resources["peak_rss_bytes"], 0)
        self.assertGreater(resources["wall_ns"], 0)
        self.assertGreater(resources["operations"], 0)
        self.assertFalse(payload["comparison_readiness"]["first_narrow_comparison_ready"])

    def test_non_public_and_policy_mismatch_block_claims(self) -> None:
        payload = run()
        self.assertIn(
            "benchmark_not_public",
            payload["anti_overclaim"]["non_public_fairness_violations"],
        )
        self.assertFalse(payload["anti_overclaim"]["non_public_parity_allowed"])
        self.assertIn(
            "run_policy_mismatch",
            payload["anti_overclaim"]["policy_mismatch_violations"],
        )
        self.assertFalse(payload["anti_overclaim"]["policy_mismatch_parity_allowed"])


if __name__ == "__main__":
    unittest.main()
