from __future__ import annotations

import json
import random
from dataclasses import asdict

from sparc_hs16 import GateCase, SparcHS16, UniversityExamGate


def build_pilot() -> list[GateCase]:
    rng = random.Random(1616)
    cases: list[GateCase] = []
    for _ in range(200):
        a, b, c = rng.randint(-100, 100), rng.randint(1, 50), rng.randint(1, 20)
        cases.append(GateCase("mathematics", f"{a}+{b}×{c}はいくつ？", f"{a + b * c}です。"))
    for _ in range(200):
        a = rng.choice([x for x in range(-12, 13) if x != 0])
        x = rng.randint(-50, 50)
        b = rng.randint(-100, 100)
        cases.append(GateCase("mathematics", f"方程式 {a}*x+{b}={a*x+b} を解いて", f"x={x}です。"))
    cases += [
        GateCase("mathematics", "750mはkm？", "0.75kmです。"),
        GateCase("mathematics", "2.5kgはg？", "2500gです。"),
        GateCase("oral_interview", "こんにちは", "こんにちは。今日は何を一緒に考えましょうか？"),
        GateCase("long_conversation", "分からない", "大丈夫です。前提、途中式、結論の順に分解して説明します。"),
    ]
    return cases


if __name__ == "__main__":
    model = SparcHS16()
    report = UniversityExamGate(max_p95_ms=100.0).evaluate(model, build_pilot())
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
