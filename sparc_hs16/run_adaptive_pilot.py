from __future__ import annotations

import json
import random
from dataclasses import asdict

from sparc_hs16.gate import GateCase, UniversityExamGate
from sparc_hs16.induction import NumericDemonstration
from sparc_hs16.runtime import AdaptiveSparcRuntime


def teach(runtime: AdaptiveSparcRuntime) -> None:
    runtime.teach_numeric_mechanism(
        "distance",
        [
            NumericDemonstration("時速30kmで2時間進む距離は？", "60"),
            NumericDemonstration("時速45kmで3時間進む距離は？", "135"),
            NumericDemonstration("時速12kmで5時間進む距離は？", "60"),
            NumericDemonstration("時速80kmで4時間進む距離は？", "320"),
        ],
    )
    runtime.teach_numeric_mechanism(
        "inventory",
        [
            NumericDemonstration("在庫10個に3箱、各4個を追加すると？", "22"),
            NumericDemonstration("在庫7個に5箱、各2個を追加すると？", "17"),
            NumericDemonstration("在庫20個に2箱、各8個を追加すると？", "36"),
            NumericDemonstration("在庫1個に9箱、各3個を追加すると？", "28"),
        ],
    )


def cases() -> list[GateCase]:
    rng = random.Random(2026)
    rows: list[GateCase] = []
    for _ in range(200):
        a, b, c = rng.randint(-100, 100), rng.randint(1, 50), rng.randint(1, 20)
        rows.append(GateCase("mathematics", f"{a}+{b}×{c}はいくつ？", f"{a + b * c}です。"))
    for _ in range(200):
        a = rng.choice([value for value in range(-12, 13) if value])
        x = rng.randint(-50, 50)
        b = rng.randint(-100, 100)
        rows.append(GateCase("mathematics", f"方程式 {a}*x+{b}={a*x+b} を解いて", f"x={x}です。"))
    for _ in range(100):
        speed, hours = rng.randint(1, 120), rng.randint(1, 12)
        rows.append(GateCase("mathematics", f"時速{speed}kmで{hours}時間進む距離は？", f"{speed * hours}です。"))
    for _ in range(100):
        base, boxes, each = rng.randint(0, 100), rng.randint(1, 20), rng.randint(1, 30)
        rows.append(GateCase("mathematics", f"在庫{base}個に{boxes}箱、各{each}個を追加すると？", f"{base + boxes * each}です。"))
    rows.extend(
        [
            GateCase("mathematics", "750mはkm？", "0.75kmです。"),
            GateCase("mathematics", "2.5kgはg？", "2500gです。"),
            GateCase("oral_interview", "こんにちは", "こんにちは。今日は何を一緒に考えましょうか？"),
            GateCase("long_conversation", "分からない", "大丈夫です。前提、途中式、結論の順に分解して説明します。"),
        ]
    )
    return rows


if __name__ == "__main__":
    runtime = AdaptiveSparcRuntime()
    teach(runtime)
    report = UniversityExamGate(max_p95_ms=100.0).evaluate(runtime, cases())
    payload = asdict(report)
    payload["adaptive_runtime_bytes"] = runtime.serialized_bytes()
    payload["induced_programs"] = [program.expression for program in runtime.numeric_bank.programs]
    print(json.dumps(payload, ensure_ascii=False, indent=2))
