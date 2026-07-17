from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_open_textbook_learner import OpenTextbookLearner


class OpenTextbookLearnerTests(unittest.TestCase):
    def test_induces_entity_boundaries_without_quotes(self) -> None:
        model = OpenTextbookLearner()
        rows = [
            (
                "哺乳類は脊椎動物の一種である。分類上、哺乳類は脊椎動物に含まれる。"
                "脊椎動物に属するものとして哺乳類が知られる。",
                "資料一",
            ),
            (
                "桜は被子植物の一種である。分類上、桜は被子植物に含まれる。"
                "被子植物に属するものとして桜が知られる。",
                "資料二",
            ),
        ]
        model.learn_paragraphs(rows)
        self.assertIn("哺乳類", model.entities)
        self.assertIn("脊椎動物", model.entities)
        self.assertTrue(any(subject == "哺乳類" and obj == "脊椎動物" for subject, _, obj in model.facts))
        self.assertFalse(model.report()["quoted_entity_bootstrap_used"])

    def test_learned_template_captures_unseen_entities(self) -> None:
        model = OpenTextbookLearner()
        model.learn_paragraphs([
            ("研究棟は大学に位置する。研究棟の所在地は大学である。大学の中に研究棟がある。", "学習一"),
            ("実験棟は研究都市に位置する。実験棟の所在地は研究都市である。研究都市の中に実験棟がある。", "学習二"),
        ])
        self.assertTrue(model.learn_question("研究棟の所在地はどこですか。", "大学"))
        accepted, _ = model.read_sentence("観測施設の所在地は臨海地区である。", "評価一")
        self.assertTrue(accepted)
        answer = model.ask("観測施設の所在地はどこですか。")
        self.assertEqual(answer.value, "臨海地区")
        self.assertEqual(answer.sources, ("評価一",))

    def test_induces_rule_and_returns_exact_sources(self) -> None:
        model = OpenTextbookLearner()
        rows = []
        for index in range(6):
            first, middle, last = f"分類始点{index}", f"分類中間{index}", f"分類終点{index}"
            for subject, obj, source in ((first, middle, f"左{index}"), (middle, last, f"右{index}"), (first, last, f"頭{index}")):
                rows.append((f"{subject}は{obj}の一種である。分類上、{subject}は{obj}に含まれる。{obj}に属するものとして{subject}が知られる。", source))
        model.learn_paragraphs(rows)
        model.induce_rules(min_support=5)
        self.assertEqual(len(model.rules), 1)
        self.assertTrue(model.learn_question("分類始点0の最上位分類は何ですか。", "分類終点0", mode="closure"))
        self.assertTrue(model.read_sentence("未知始点は未知中間の一種である。", "新左")[0])
        self.assertTrue(model.read_sentence("未知中間は未知終点の一種である。", "新右")[0])
        result = model.ask("未知始点の最上位分類は何ですか。")
        self.assertEqual(result.value, "未知終点")
        self.assertEqual(result.sources, ("新右", "新左"))
        self.assertEqual(len(result.proof), 2)

    def test_abstention_preserves_graph_and_serialization(self) -> None:
        model = OpenTextbookLearner()
        model.learn_paragraphs([("発電装置には冷却水が必要である。発電装置を成立させるには冷却水を要する。冷却水は発電装置の必要条件である。", "資料一")])
        self.assertTrue(model.learn_question("発電装置に必要なものは何ですか。", "冷却水"))
        before = (len(model.facts), len(model.entities))
        accepted, mechanism = model.read_sentence("未知装置は未知対象を祝福する。", "未知資料")
        self.assertFalse(accepted)
        self.assertEqual(mechanism, "abstain-unknown-surface")
        self.assertEqual(before, (len(model.facts), len(model.entities)))
        restored = OpenTextbookLearner.from_bytes(model.to_bytes())
        self.assertEqual(restored.ask("発電装置に必要なものは何ですか。").value, "冷却水")


if __name__ == "__main__":
    unittest.main()
