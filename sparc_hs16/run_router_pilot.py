from __future__ import annotations

import json
import random
import time

from sparc_hs16.router import SparseMechanismRouter, build_bootstrap_router


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int((len(ordered) - 1) * 0.95)]


def main() -> None:
    router = build_bootstrap_router()
    rng = random.Random(2626)
    names = ["葵", "蓮", "凛", "結衣", "悠真", "陽菜", "蒼", "紬"]
    places = ["駅", "公園", "図書館", "研究室", "体育館"]
    cases: list[tuple[str, str]] = []

    for _ in range(100):
        a, b = rng.randint(1, 99), rng.randint(1, 20)
        cases.append((f"{a}+{b}×3を計算して", "base"))
    for _ in range(100):
        speed, hours = rng.randint(10, 120), rng.randint(1, 12)
        cases.append((f"時速{speed}kmで{hours}時間進む距離は", "numeric"))
    for _ in range(100):
        person, place = rng.choice(names), rng.choice(places)
        cases.append((f"本文:{person}は{place}へ行った。問:{person}はどこへ行った", "reading"))
    for _ in range(100):
        order = rng.sample(names, 3)
        cases.append((f"対象:{'、'.join(order)}。条件:{order[0]}は{order[1]}より前。問:順番は", "constraints"))
    for _ in range(100):
        person = rng.choice(names)
        cases.append((f"私の名前は{person}です。覚えて", "conversation"))

    correct = 0
    latencies: list[float] = []
    predictions: list[str] = []
    for text, expected in cases:
        started = time.perf_counter()
        predicted, _ = router.predict(text)
        latencies.append((time.perf_counter() - started) * 1000)
        predictions.append(predicted)
        correct += int(predicted == expected)

    restored = SparseMechanismRouter.from_dict(router.to_dict())
    persistence_ok = all(
        restored.predict(text)[0] == predicted
        for (text, _), predicted in zip(cases, predictions)
    )
    report = {
        "capability_id": "SPARC-HS16-LEARNED-SPARSE-ROUTING",
        "unseen_cases": len(cases),
        "correct": correct,
        "accuracy": correct / len(cases),
        "p95_latency_ms": p95(latencies),
        "router_bytes": router.serialized_bytes(),
        "persistence_ok": persistence_ok,
        "buckets": router.buckets,
        "labels": list(router.labels),
        "transformer_used": False,
        "gradient_backpropagation_used": False,
        "university_exam_mastery_passed": False,
        "claim_boundary": "This pilot learns sparse routing among existing mechanisms; it does not itself supply subject knowledge or unrestricted language understanding.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
