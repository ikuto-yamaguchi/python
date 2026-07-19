from __future__ import annotations

import unittest

from sparc_hs16.dialogue_cognition import ConversationalCognitiveEngine


class DialogueCognitionTests(unittest.TestCase):
    def test_memory_and_correction(self):
        engine = ConversationalCognitiveEngine()
        engine.respond("私の名前は郁斗です。")
        self.assertIn("郁斗", engine.respond("名前を覚えてる？").text)
        engine.respond("彼女と旅行に行く予定なんだ。")
        corrected = engine.respond("彼女じゃなくて妹だよ。")
        self.assertIn("妹", corrected.text)
        self.assertNotEqual(engine.state.current_topic, "彼女")

    def test_empathy_and_question(self):
        engine = ConversationalCognitiveEngine()
        reply = engine.respond("今日は仕事で疲れたよ。")
        self.assertIn("疲れる", reply.text)
        self.assertTrue(reply.text.endswith("？"))

    def test_ambiguous_reference_abstains(self):
        engine = ConversationalCognitiveEngine()
        reply = engine.respond("それはどうすればいい？")
        self.assertTrue("一言" in reply.text or "曖昧" in reply.text or "特定" in reply.text)

    def test_topic_switch_and_return(self):
        engine = ConversationalCognitiveEngine()
        engine.respond("ランニングを再開した。")
        engine.respond("AIモデルの研究もしている。")
        reply = engine.respond("さっきのランニングの話に戻ろう。")
        self.assertIn("ランニング", reply.text)

    def test_session_boundary_retains_profile_not_referent(self):
        engine = ConversationalCognitiveEngine()
        engine.respond("私の名前は郁斗です。")
        engine.respond("ランニングについて話そう。")
        engine.start_new_session()
        self.assertEqual(engine.state.facts["名前"], "郁斗")
        self.assertIsNone(engine.state.current_topic)
        self.assertIn("特定", engine.respond("それをどうすればいい？").text)

    def test_round_trip_persistence(self):
        engine = ConversationalCognitiveEngine()
        engine.respond("私の名前は郁斗です。")
        restored = ConversationalCognitiveEngine.from_dict(engine.to_dict())
        self.assertIn("郁斗", restored.respond("名前を覚えてる？").text)


if __name__ == "__main__":
    unittest.main()
