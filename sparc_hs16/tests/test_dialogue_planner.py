from __future__ import annotations

import unittest

from sparc_hs16.dialogue_planner import PlannedConversationalEngine


class DialoguePlannerTests(unittest.TestCase):
    def test_generates_and_scores_multiple_candidates(self) -> None:
        engine = PlannedConversationalEngine()
        reply = engine.respond("今日は仕事でかなり疲れたよ。")
        self.assertGreaterEqual(len(engine.last_candidates), 3)
        selected = next(candidate for candidate in engine.last_candidates if candidate.text == reply.text)
        self.assertEqual(selected.score, max(candidate.score for candidate in engine.last_candidates))
        self.assertTrue(any(reason.startswith("strategy=") for reason in reply.evidence))

    def test_advice_is_actionable_and_uses_active_topic(self) -> None:
        engine = PlannedConversationalEngine()
        engine.respond("上司に帰る直前で急な仕事を頼まれた。")
        engine.respond("断ったら機嫌が悪くなりそうで、結局引き受けた。")
        reply = engine.respond("こういうとき、どうすればいいと思う？")
        self.assertTrue(any(term in reply.text for term in ("上司", "事実・制約・希望", "相手", "選択肢")))
        self.assertTrue(any(term in reply.text for term in ("まず", "分け", "確認", "決め", "選ぶ")))

    def test_topic_dimensions_support_causal_followup(self) -> None:
        engine = PlannedConversationalEngine()
        engine.respond("最近ランニングを再開したんだ。")
        engine.respond("10キロ走ると後半に脚が重くなる。")
        reply = engine.respond("原因は何だと思う？")
        self.assertTrue(any(term in reply.text for term in ("ペース", "呼吸", "脚", "補給")))

    def test_repetition_penalty_changes_repeated_response(self) -> None:
        engine = PlannedConversationalEngine()
        first = engine.respond("ゲームの操作が分かりづらいと言われた。").text
        second = engine.respond("ゲームの操作が分かりづらいと言われた。").text
        self.assertNotEqual(first, second)

    def test_profile_survives_new_session_but_topic_does_not(self) -> None:
        engine = PlannedConversationalEngine()
        engine.respond("私の名前は郁斗です。")
        engine.respond("最近ランニングを再開したんだ。")
        engine.start_new_session()
        self.assertEqual(engine.state.facts.get("名前"), "郁斗")
        self.assertIsNone(engine.state.current_topic)
        self.assertIn("郁斗", engine.respond("名前を覚えてる？").text)


if __name__ == "__main__":
    unittest.main()
