from __future__ import annotations

import unittest

from minimal_predictive_lm.intelligence_route_discovery import (
    FamilyVerdict,
    RouteMetrics,
    SCALES,
    _prefix_targets,
    family_verdict,
)


class IntelligenceRouteDiscoveryTests(unittest.TestCase):
    def test_scale_resource_plans_strictly_grow(self) -> None:
        recurrent_bytes = [scale.recurrent.persistent_bytes() for scale in SCALES]
        mobile_bytes = [scale.mobile.package_bytes() for scale in SCALES]
        self.assertEqual(recurrent_bytes, sorted(recurrent_bytes))
        self.assertEqual(mobile_bytes, sorted(mobile_bytes))
        self.assertEqual(len(set(recurrent_bytes)), len(recurrent_bytes))
        self.assertEqual(len(set(mobile_bytes)), len(mobile_bytes))

    def test_prefix_targets_preserve_single_ascii_answer(self) -> None:
        examples = _prefix_targets(["規則甲|入力2|答え3"])
        self.assertEqual(examples, [("規則甲|入力2|答え", ord("3"))])

    def test_verdict_rejects_flat_toy_success(self) -> None:
        rows = [
            RouteMetrics(
                family="candidate",
                scale=name,
                model_bytes=model_bytes,
                active_macs_per_byte=100,
                training_seconds=0.1,
                train_nll_before=5.0,
                train_nll_after=1.0,
                train_nll_gain=0.8,
                compositional_transfer_accuracy=0.25,
                long_dependency_accuracy=0.25,
                continual_retention=1.0,
                one_shot_exact_accuracy=1.0,
                one_shot_paraphrase_accuracy=1.0,
            )
            for name, model_bytes in (("tiny", 1000), ("small", 2000), ("medium", 4000))
        ]
        verdict = family_verdict(rows)
        self.assertIsInstance(verdict, FamilyVerdict)
        self.assertFalse(verdict.route_go)
        self.assertIn("positive_compositional_scaling", verdict.failed_requirements)
        self.assertIn("largest_compositional_transfer", verdict.failed_requirements)

    def test_verdict_requires_multiple_scales(self) -> None:
        row = RouteMetrics(
            family="candidate",
            scale="tiny",
            model_bytes=1000,
            active_macs_per_byte=100,
            training_seconds=0.1,
            train_nll_before=5.0,
            train_nll_after=1.0,
            train_nll_gain=0.8,
            compositional_transfer_accuracy=1.0,
            long_dependency_accuracy=1.0,
            continual_retention=1.0,
            one_shot_exact_accuracy=1.0,
            one_shot_paraphrase_accuracy=1.0,
        )
        with self.assertRaises(ValueError):
            family_verdict([row])


if __name__ == "__main__":
    unittest.main()
