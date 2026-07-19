from __future__ import annotations

import random
import unittest

from sparc_hs16.router import RouteExample, SparseMechanismRouter, build_bootstrap_router


class SparseRouterTests(unittest.TestCase):
    def test_bootstrap_training_examples(self) -> None:
        router = build_bootstrap_router()
        cases = {
            "本文:蓮は公園へ向かった。質問:蓮はどこへ向かった": "reading",
            "対象:葵、凛、蒼。条件:葵は凛より前。質問:並び順は": "constraints",
            "私の名前を覚えている？": "conversation",
            "時速72kmで5時間なら距離はいくつ": "numeric",
            "18÷3+7を計算して": "base",
        }
        for text, expected in cases.items():
            label, _ = router.predict(text)
            self.assertEqual(label, expected)
        self.assertLess(router.serialized_bytes(), 200_000)

    def test_learns_new_route_without_code_change(self) -> None:
        router = SparseMechanismRouter(labels=("alpha", "beta"))
        router.fit(
            [
                RouteExample("赤い果物について", "alpha"),
                RouteExample("赤色のりんご", "alpha"),
                RouteExample("青い海について", "beta"),
                RouteExample("青色の空", "beta"),
            ],
            epochs=50,
        )
        self.assertEqual(router.predict("赤いりんご")[0], "alpha")
        self.assertEqual(router.predict("青い空")[0], "beta")

    def test_serialization_round_trip(self) -> None:
        router = build_bootstrap_router()
        restored = SparseMechanismRouter.from_dict(router.to_dict())
        prompts = [
            "文章を読んで原因を説明して",
            "すべての条件を満たす順序は",
            "私の目標を覚えているか",
            "例題から獲得した式で計算して",
            "方程式を解いて",
        ]
        for prompt in prompts:
            self.assertEqual(restored.predict(prompt), router.predict(prompt))


if __name__ == "__main__":
    unittest.main()
