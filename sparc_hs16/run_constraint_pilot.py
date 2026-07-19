from __future__ import annotations

import json
import random
import time

from sparc_hs16.runtime import AdaptiveSparcRuntime


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int((len(ordered) - 1) * 0.95)]


def main() -> None:
    runtime = AdaptiveSparcRuntime()
    rng = random.Random(2525)
    names = ["葵", "蓮", "凛", "結衣", "悠真", "陽菜", "蒼", "紬"]
    correct = 0
    total = 0
    latencies: list[float] = []

    for _ in range(300):
        order = rng.sample(names, rng.randint(4, 7))
        constraints = "。".join(
            f"{left}は{right}より前" for left, right in zip(order, order[1:])
        )
        prompt = f"対象:{'、'.join(order)}。条件:{constraints}。問:順番は？"
        result = runtime.solve(prompt)
        total += 1
        correct += int(result.answer == "→".join(order) + "です。")
        latencies.append(result.elapsed_ms)

    contradictory = runtime.solve("対象:A、B。条件:AはBより前。BはAより前。問:順番は？")
    ambiguous = runtime.solve("対象:A、B、C。条件:AはBより前。問:順番は？")
    report = {
        "capability_id": "SPARC-HS16-EXACT-JAPANESE-CONSTRAINT-SOLVING",
        "unseen_cases": total,
        "correct": correct,
        "accuracy": correct / total,
        "p95_latency_ms": p95(latencies),
        "adaptive_runtime_bytes": runtime.serialized_bytes(),
        "contradiction_detected": contradictory.answer == "条件を同時に満たす順番はありません。",
        "ambiguity_detected": ambiguous.answer == "一意に定まりません。3通りあります。",
        "proof_attached": all(
            runtime.solve(
                f"対象:{'、'.join(order)}。条件:"
                + "。".join(f"{a}は{b}より前" for a, b in zip(order, order[1:]))
                + "。問:順番は？"
            ).mechanism.startswith("exact-ordering-constraints:")
            for order in [rng.sample(names, 4) for _ in range(10)]
        ),
        "transformer_used": False,
        "university_exam_mastery_passed": False,
        "claim_boundary": "This establishes exact bounded ordering-constraint solving with ambiguity and contradiction detection, not unrestricted entrance-exam logic coverage.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
