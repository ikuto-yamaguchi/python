from __future__ import annotations

import random
import unittest

from sparc_hs16.constraints import JapaneseOrderingSolver


class OrderingConstraintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.solver = JapaneseOrderingSolver()

    def test_unique_order(self) -> None:
        text = "対象:葵、蓮、凛、結衣。条件:葵は蓮より前。蓮は凛より前。凛は結衣より前。問:順番は？"
        result = self.solver.solve(text)
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "葵→蓮→凛→結衣です。")
        self.assertEqual(len(result.solutions), 1)

    def test_immediate_adjacent_and_position(self) -> None:
        text = "対象:A、B、C、D。条件:Aは1番目。CはAの直後。BとDは隣り合う。BはDより前。問:順番は？"
        result = self.solver.solve(text)
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "A→C→B→Dです。")

    def test_unsatisfiable(self) -> None:
        text = "対象:A、B。条件:AはBより前。BはAより前。問:順番は？"
        result = self.solver.solve(text)
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "条件を同時に満たす順番はありません。")

    def test_multiple_solutions_reported(self) -> None:
        text = "対象:A、B、C。条件:AはBより前。問:順番は？"
        result = self.solver.solve(text)
        self.assertIsNotNone(result)
        self.assertEqual(len(result.solutions), 3)
        self.assertEqual(result.answer, "一意に定まりません。3通りあります。")

    def test_200_unseen_total_orders(self) -> None:
        rng = random.Random(2424)
        names = ["葵", "蓮", "凛", "結衣", "悠真", "陽菜", "蒼", "紬"]
        for _ in range(200):
            order = rng.sample(names, rng.randint(4, 7))
            constraints = "。".join(
                f"{left}は{right}より前" for left, right in zip(order, order[1:])
            )
            text = f"対象:{'、'.join(order)}。条件:{constraints}。問:順番は？"
            result = self.solver.solve(text)
            self.assertIsNotNone(result)
            self.assertEqual(result.answer, "→".join(order) + "です。")
            self.assertTrue(result.proof)


if __name__ == "__main__":
    unittest.main()
