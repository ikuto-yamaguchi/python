import json
import unittest

from sparc_hs16.generative_interaction_grammar import DialogueExample, GenerativeInteractionGrammar


class GenerativeInteractionGrammarTests(unittest.TestCase):
    def test_generates_without_candidates(self):
        model = GenerativeInteractionGrammar(max_order=5, state_buckets=128)
        model.fit([DialogueExample(("疲れた",), "今日は休もう。")], seed=1)
        self.assertTrue(model.generate(("疲れた",), seed=1))

    def test_roundtrip(self):
        model = GenerativeInteractionGrammar(max_order=4, state_buckets=128)
        example = DialogueExample(("名前は郁斗",), "覚えた。")
        model.fit([example], seed=2)
        restored = GenerativeInteractionGrammar.from_dict(json.loads(json.dumps(model.to_dict(), ensure_ascii=False)))
        self.assertEqual(model.generate(example.context, seed=3), restored.generate(example.context, seed=3))

    def test_bounded_edges(self):
        model = GenerativeInteractionGrammar(max_order=3, state_buckets=64, max_edges=300)
        for i in range(80):
            model.observe(DialogueExample((f"入力{i}",), f"出力{i}です。"))
        self.assertLessEqual(model._edge_count(), 300)

    def test_unseen_prompt_is_not_counted_as_success_by_nonempty_output(self):
        model = GenerativeInteractionGrammar(max_order=4, state_buckets=128)
        model.fit([DialogueExample(("赤",), "赤です。")])
        output = model.generate(("未知の問い",), seed=4)
        self.assertIsInstance(output, str)
        self.assertNotEqual(output, "未知の問い")


if __name__ == "__main__":
    unittest.main()
