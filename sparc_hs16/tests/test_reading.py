from __future__ import annotations

import random
import unittest

from sparc_hs16.reading import JapaneseReadingReasoner


class JapaneseReadingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reasoner = JapaneseReadingReasoner()

    def ask(self, passage: str, question: str) -> str:
        result = self.reasoner.solve(f"本文:{passage}\n問:{question}")
        self.assertIsNotNone(result)
        self.assertTrue(result.proof)
        return result.answer

    def test_location_and_placement(self) -> None:
        self.assertEqual(self.ask("葵は図書館へ行った。", "葵はどこへ行った？"), "図書館です。")
        self.assertEqual(self.ask("蓮は鍵を引き出しに置いた。", "鍵はどこに置かれた？"), "引き出しです。")

    def test_transfer(self) -> None:
        passage = "美咲は健に地図を渡した。健は凛に鉛筆を貸した。"
        self.assertEqual(self.ask(passage, "誰が地図を渡した？"), "美咲です。")
        self.assertEqual(self.ask(passage, "健は誰に鉛筆を貸した？"), "凛です。")

    def test_order_transitive_closure(self) -> None:
        passage = "青木は石井より先に到着した。石井は上田より先に到着した。"
        self.assertEqual(self.ask(passage, "青木と上田ではどちらが先？"), "青木です。")
        self.assertEqual(self.ask(passage, "誰が最初だった？"), "青木です。")

    def test_cause(self) -> None:
        passage = "雨が強く降ったので、試合は中止になった。"
        self.assertEqual(self.ask(passage, "なぜ試合は中止になった？"), "雨が強く降ったからです。")

    def test_unseen_names_and_values(self) -> None:
        rng = random.Random(2121)
        names = ["葵", "蓮", "凛", "結衣", "悠真", "陽菜", "蒼", "紬"]
        places = ["図書館", "公園", "研究室", "駅", "体育館", "美術館"]
        objects = ["鍵", "本", "地図", "時計", "手紙", "ノート"]
        for _ in range(100):
            person = rng.choice(names)
            place = rng.choice(places)
            self.assertEqual(self.ask(f"{person}は{place}へ行った。", f"{person}はどこへ行った？"), f"{place}です。")
        for _ in range(100):
            giver, receiver = rng.sample(names, 2)
            obj = rng.choice(objects)
            self.assertEqual(self.ask(f"{giver}は{receiver}に{obj}を渡した。", f"誰が{obj}を渡した？"), f"{giver}です。")
        for _ in range(100):
            first, second, third = rng.sample(names, 3)
            passage = f"{first}は{second}より先に到着した。{second}は{third}より先に到着した。"
            self.assertEqual(self.ask(passage, f"{first}と{third}ではどちらが先？"), f"{first}です。")

    def test_abstains_without_proof(self) -> None:
        self.assertIsNone(self.reasoner.solve("本文:葵は図書館へ行った。\n問:葵は何を食べた？"))


if __name__ == "__main__":
    unittest.main()
