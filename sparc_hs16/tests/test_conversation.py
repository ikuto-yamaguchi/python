from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sparc_hs16.conversation import ConsistentConversationEngine
from sparc_hs16.runtime import AdaptiveSparcRuntime


class ConversationEngineTests(unittest.TestCase):
    def test_fact_preference_goal_and_correction(self) -> None:
        engine = ConsistentConversationEngine()
        self.assertEqual(engine.respond("私の名前は郁斗です").answer, "名前は郁斗ですね。覚えました。")
        self.assertEqual(engine.respond("私はラーメンが好きです").answer, "ラーメンが好きなのですね。覚えました。")
        self.assertEqual(engine.respond("目標はフルマラソンを完走することです").answer, "目標はフルマラソンを完走することですね。覚えました。")
        self.assertEqual(engine.respond("私の名前は？").answer, "郁斗です。")
        self.assertEqual(engine.respond("違う、郁斗ではなく海斗").answer, "訂正しました。海斗として覚えます。")
        self.assertEqual(engine.respond("私の名前は？").answer, "海斗です。")
        self.assertEqual(engine.respond("私が好きなのは？").answer, "ラーメンです。")
        self.assertEqual(engine.respond("私の目標は？").answer, "フルマラソンを完走することです。")

    def test_preference_contradiction_is_removed(self) -> None:
        engine = ConsistentConversationEngine()
        engine.respond("私は納豆が好きです")
        engine.respond("私は納豆が嫌いです")
        self.assertEqual(engine.respond("私が好きなのは？").answer, "好きなものはまだ聞いていません。")
        self.assertEqual(engine.respond("私が嫌いなのは？").answer, "納豆です。")

    def test_bounded_history(self) -> None:
        engine = ConsistentConversationEngine()
        engine.state.max_history = 20
        for index in range(100):
            engine.respond(f"私の仕事は仕事{index}です")
        self.assertLessEqual(len(engine.state.history), 20)
        self.assertEqual(engine.respond("私の仕事は？").answer, "仕事99です。")

    def test_runtime_persistence(self) -> None:
        runtime = AdaptiveSparcRuntime()
        runtime.chat("私の名前は郁斗です")
        runtime.chat("私はラーメンが好きです")
        runtime.chat("目標は24時間走で120kmです")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "runtime.json"
            runtime.save(path)
            restored = AdaptiveSparcRuntime.load(path)
            self.assertEqual(restored.chat("私の名前は？").answer, "郁斗です。")
            self.assertEqual(restored.chat("私が好きなのは？").answer, "ラーメンです。")
            self.assertEqual(restored.chat("私の目標は？").answer, "24時間走で120kmです。")
            self.assertLess(path.stat().st_size, 20_000)


if __name__ == "__main__":
    unittest.main()
