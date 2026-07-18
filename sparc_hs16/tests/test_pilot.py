from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from sparc_hs16 import GateCase, SparcHS16, UniversityExamGate


class PilotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = SparcHS16()

    def test_unseen_arithmetic(self) -> None:
        rng = random.Random(1616)
        for _ in range(100):
            a, b, c = rng.randint(-50, 50), rng.randint(1, 30), rng.randint(1, 10)
            expected = a + b * c
            result = self.model.solve(f"{a}+{b}×{c}はいくつ？")
            self.assertEqual(result.answer, f"{expected}です。")
            self.assertEqual(result.mechanism, "verified-arithmetic")

    def test_unseen_linear_equations(self) -> None:
        rng = random.Random(1717)
        for _ in range(100):
            a = rng.choice([x for x in range(-9, 10) if x != 0])
            x = rng.randint(-20, 20)
            b = rng.randint(-30, 30)
            rhs = a * x + b
            result = self.model.solve(f"方程式 {a}*x+{b}={rhs} を解いて")
            self.assertEqual(result.answer, f"x={x}です。")

    def test_units(self) -> None:
        cases = {
            "750mはkm？": "0.75kmです。",
            "2.5kgはg？": "2500gです。",
            "180minはh？": "3hです。",
            "40cmはmm？": "400mmです。",
        }
        for prompt, expected in cases.items():
            self.assertEqual(self.model.solve(prompt).answer, expected)

    def test_syllogism(self) -> None:
        prompt = "すべての哺乳類は動物です。すべての犬は哺乳類です。ポチは犬です。ポチは動物ですか？"
        self.assertEqual(self.model.solve(prompt).answer, "はい、導けます。")

    def test_online_fact_and_persistence(self) -> None:
        self.assertEqual(self.model.solve("研究コードは海側と覚えて").answer, "覚えました。")
        self.assertEqual(self.model.solve("研究コードは何？").answer, "海側")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "model.json"
            self.model.save(path)
            restored = SparcHS16.load(path)
            self.assertEqual(restored.solve("研究コードは何？").answer, "海側")

    def test_strict_gate_stays_false_on_narrow_pilot(self) -> None:
        cases = [
            GateCase("mathematics", "12+3×4はいくつ？", "24です。"),
            GateCase("oral_interview", "こんにちは", "こんにちは。今日は何を一緒に考えましょうか？"),
        ]
        report = UniversityExamGate().evaluate(self.model, cases)
        self.assertEqual(report.accuracy, 1.0)
        self.assertFalse(report.all_required_domains_present)
        self.assertFalse(report.university_exam_mastery_passed)
        self.assertTrue(report.mobile_device_gate_passed)
        self.assertFalse(report.highschool_level_passed)


if __name__ == "__main__":
    unittest.main()
