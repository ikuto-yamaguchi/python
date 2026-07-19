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
    rng = random.Random(2222)
    names = ["葵", "蓮", "凛", "結衣", "悠真", "陽菜", "蒼", "紬", "湊", "咲良", "樹", "杏"]
    places = ["図書館", "公園", "研究室", "駅", "体育館", "美術館", "校庭", "講堂"]
    objects = ["鍵", "本", "地図", "時計", "手紙", "ノート", "封筒", "写真"]
    causes = [
        ("雨が強く降った", "試合は中止になった"),
        ("電車が遅れた", "会議の開始が遅くなった"),
        ("気温が急に下がった", "池の表面が凍った"),
        ("材料が不足した", "製作は翌日に延期された"),
        ("道が工事中だった", "バスは迂回した"),
    ]

    correct = 0
    total = 0
    latencies: list[float] = []
    mechanisms: dict[str, int] = {}

    def check(prompt: str, expected: str) -> None:
        nonlocal correct, total
        result = runtime.solve(prompt)
        total += 1
        correct += int(result.answer == expected)
        latencies.append(result.elapsed_ms)
        family = result.mechanism.split(":", 1)[0]
        mechanisms[family] = mechanisms.get(family, 0) + 1

    for _ in range(150):
        person = rng.choice(names)
        place = rng.choice(places)
        check(f"本文:{person}は{place}へ行った。\n問:{person}はどこへ行った？", f"{place}です。")

    for _ in range(150):
        giver, receiver = rng.sample(names, 2)
        obj = rng.choice(objects)
        check(f"本文:{giver}は{receiver}に{obj}を渡した。\n問:誰が{obj}を渡した？", f"{giver}です。")

    for _ in range(100):
        first, middle, last = rng.sample(names, 3)
        passage = f"{first}は{middle}より先に到着した。{middle}は{last}より先に到着した。"
        check(f"本文:{passage}\n問:{first}と{last}ではどちらが先？", f"{first}です。")

    for _ in range(100):
        cause, effect = rng.choice(causes)
        check(f"本文:{cause}ので、{effect}。\n問:なぜ{effect}？", f"{cause}からです。")

    abstention = runtime.solve("本文:葵は図書館へ行った。\n問:葵は何を食べた？")
    report = {
        "capability_id": "SPARC-HS16-PROOF-JAPANESE-READING",
        "unseen_cases": total,
        "correct": correct,
        "accuracy": correct / total,
        "p95_latency_ms": p95(latencies),
        "adaptive_runtime_bytes": runtime.serialized_bytes(),
        "mechanisms": mechanisms,
        "unsupported_question_abstained": abstention.mechanism == "calibrated-abstention",
        "proof_attached": all(key == "proof-japanese-reading" for key in mechanisms),
        "transformer_used": False,
        "university_exam_mastery_passed": False,
        "claim_boundary": "The runtime proves answers for a controlled but unseen relation-and-cause subset of Japanese reading. This pilot alone does not establish unrestricted modern Japanese comprehension.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
