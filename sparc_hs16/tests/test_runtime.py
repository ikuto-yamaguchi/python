from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sparc_hs16.gate import GateCase, UniversityExamGate
from sparc_hs16.induction import NumericDemonstration
from sparc_hs16.runtime import AdaptiveSparcRuntime


class AdaptiveRuntimeTests(unittest.TestCase):
    def build_runtime(self) -> AdaptiveSparcRuntime:
        runtime = AdaptiveSparcRuntime()
        runtime.teach_numeric_mechanism(
            "distance",
            [
                NumericDemonstration("時速30kmで2時間進む距離は？", "60"),
                NumericDemonstration("時速45kmで3時間進む距離は？", "135"),
                NumericDemonstration("時速12kmで5時間進む距離は？", "60"),
            ],
        )
        return runtime

    def test_routes_learned_and_base_mechanisms(self) -> None:
        runtime = self.build_runtime()
        induced = runtime.solve("時速73kmで6時間進む距離は？")
        arithmetic = runtime.solve("12+3×4はいくつ？")
        dialogue = runtime.solve("こんにちは")
        self.assertEqual(induced.answer, "438です。")
        self.assertTrue(induced.mechanism.startswith("induced-program:"))
        self.assertEqual(arithmetic.answer, "24です。")
        self.assertEqual(dialogue.answer, "こんにちは。今日は何を一緒に考えましょうか？")

    def test_single_artifact_round_trip(self) -> None:
        runtime = self.build_runtime()
        runtime.base.solve("研究コードは海側と覚えて")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "adaptive.json"
            runtime.save(path)
            restored = AdaptiveSparcRuntime.load(path)
            self.assertEqual(restored.solve("時速73kmで6時間進む距離は？").answer, "438です。")
            self.assertEqual(restored.solve("研究コードは何？").answer, "海側")
            self.assertLess(path.stat().st_size, 10_000)

    def test_strict_gate_accepts_runtime_but_remains_fail_closed(self) -> None:
        runtime = self.build_runtime()
        report = UniversityExamGate().evaluate(
            runtime,
            [
                GateCase("mathematics", "時速73kmで6時間進む距離は？", "438です。"),
                GateCase("oral_interview", "こんにちは", "こんにちは。今日は何を一緒に考えましょうか？"),
            ],
        )
        self.assertEqual(report.accuracy, 1.0)
        self.assertTrue(report.mobile_device_gate_passed)
        self.assertFalse(report.all_required_domains_present)
        self.assertFalse(report.university_exam_mastery_passed)
        self.assertFalse(report.highschool_level_passed)


if __name__ == "__main__":
    unittest.main()
