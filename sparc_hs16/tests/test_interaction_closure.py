import json
import unittest

from sparc_hs16.interaction_closure import (
    PreferencePair,
    SparsePairwiseRanker,
    shuffled_context_pairs,
)


class InteractionClosureTests(unittest.TestCase):
    def test_pairwise_learning_uses_raw_text(self):
        pairs = [
            PreferencePair(
                ("今日は仕事で失敗して落ち込んでる",),
                "それはつらかったね。何が一番苦しかった？",
                "富士山は高いです。",
            ),
            PreferencePair(
                ("友達と喧嘩してしまった",),
                "関係を戻したいなら、まず相手の話を聞くのがよさそう。",
                "猫はかわいいですね。",
            ),
            PreferencePair(
                ("走ると後半に脚が重い。どうすればいい？",),
                "前半のペースを少し落として変化を比べよう。",
                "宇宙は広いです。",
            ),
        ]
        model = SparsePairwiseRanker(dimensions=4096)
        model.fit(pairs, epochs=8, seed=3)
        self.assertEqual(model.accuracy(pairs), 1.0)
        self.assertGreater(model.updates, 0)

    def test_serialization_roundtrip(self):
        pair = PreferencePair(("困っている",), "状況を整理しよう。", "関係ない答え")
        model = SparsePairwiseRanker(dimensions=2048)
        model.fit([pair], epochs=2)
        restored = SparsePairwiseRanker.from_dict(json.loads(json.dumps(model.to_dict())))
        self.assertEqual(
            model.prefer(pair.context, pair.chosen, pair.rejected),
            restored.prefer(pair.context, pair.chosen, pair.rejected),
        )

    def test_context_shuffle_preserves_responses(self):
        pairs = [
            PreferencePair(("a",), "x", "y"),
            PreferencePair(("b",), "u", "v"),
            PreferencePair(("c",), "m", "n"),
        ]
        shuffled = shuffled_context_pairs(pairs, 4)
        self.assertEqual([p.chosen for p in shuffled], [p.chosen for p in pairs])
        self.assertEqual(
            sorted(p.context for p in shuffled),
            sorted(p.context for p in pairs),
        )

    def test_arbitrary_candidates_can_be_ranked_without_strategy_labels(self):
        pair = PreferencePair(
            ("どちらから直すべき？",),
            "失敗時の影響が大きい方から確認しよう。",
            "何も考えず両方やろう。",
        )
        model = SparsePairwiseRanker(dimensions=2048)
        model.fit([pair], epochs=4)
        order = model.rank(pair.context, (pair.rejected, pair.chosen))
        self.assertEqual(order[0], 1)


if __name__ == "__main__":
    unittest.main()
