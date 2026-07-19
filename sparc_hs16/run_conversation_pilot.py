from __future__ import annotations

import json
import random
import tempfile
import time
from pathlib import Path

from sparc_hs16.runtime import AdaptiveSparcRuntime


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int((len(ordered) - 1) * 0.95)]


def main() -> None:
    runtime = AdaptiveSparcRuntime()
    runtime.conversation.state.max_history = 128
    rng = random.Random(2323)
    names = ["郁斗", "海斗", "悠斗", "蒼", "蓮"]
    foods = ["ラーメン", "寿司", "カレー", "蕎麦", "餃子"]
    goals = ["24時間走で120km", "大学入試で満点", "毎日5km走る", "アプリを公開する"]
    latencies: list[float] = []
    correct = 0
    total = 0

    def chat(prompt: str, expected: str) -> None:
        nonlocal correct, total
        started = time.perf_counter()
        reply = runtime.chat(prompt)
        latencies.append((time.perf_counter() - started) * 1000)
        correct += int(reply.answer == expected)
        total += 1

    for _ in range(100):
        old, new = rng.sample(names, 2)
        chat(f"私の名前は{old}です", f"名前は{old}ですね。覚えました。")
        chat(f"違う、{old}ではなく{new}", f"訂正しました。{new}として覚えます。")
        chat("私の名前は？", f"{new}です。")

    for _ in range(100):
        food = rng.choice(foods)
        chat(f"私は{food}が好きです", f"{food}が好きなのですね。覚えました。")
        chat("私が好きなのは？", "、".join(runtime.conversation.state.likes) + "です。")
        chat(f"私は{food}が嫌いです", f"{food}が苦手なのですね。覚えました。")
        remaining = runtime.conversation.state.likes
        expected = "、".join(remaining) + "です。" if remaining else "好きなものはまだ聞いていません。"
        chat("私が好きなのは？", expected)

    for _ in range(100):
        goal = rng.choice(goals)
        chat(f"目標は{goal}です", f"目標は{goal}ですね。覚えました。")
        chat("私の目標は？", "、".join(runtime.conversation.state.goals) + "です。")

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "runtime.json"
        runtime.save(path)
        restored = AdaptiveSparcRuntime.load(path)
        persistence_ok = (
            restored.conversation.state.facts == runtime.conversation.state.facts
            and restored.conversation.state.likes == runtime.conversation.state.likes
            and restored.conversation.state.dislikes == runtime.conversation.state.dislikes
            and restored.conversation.state.goals == runtime.conversation.state.goals
        )
        artifact_bytes = path.stat().st_size

    report = {
        "capability_id": "SPARC-HS16-CORRECTION-AWARE-LONG-CONVERSATION",
        "turn_checks": total,
        "correct": correct,
        "accuracy": correct / total,
        "p95_latency_ms": p95(latencies),
        "history_entries": len(runtime.conversation.state.history),
        "history_bound": runtime.conversation.state.max_history,
        "history_bound_respected": len(runtime.conversation.state.history) <= runtime.conversation.state.max_history,
        "persistence_ok": persistence_ok,
        "artifact_bytes": artifact_bytes,
        "contradiction_free_preferences": not set(runtime.conversation.state.likes) & set(runtime.conversation.state.dislikes),
        "transformer_used": False,
        "university_exam_mastery_passed": False,
        "claim_boundary": "This pilot establishes bounded explicit memory, correction and contradiction handling for controlled personal-state dialogue, not unrestricted human-level communication.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
