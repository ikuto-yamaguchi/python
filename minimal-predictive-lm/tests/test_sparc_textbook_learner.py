from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_textbook_learner import SparseTextbookLearner


CLASS_PARAGRAPH = (
    "「{a}」は「{b}」の一種である。"
    "分類上、「{a}」は「{b}」に含まれる。"
    "「{a}」が属する分類は「{b}」だ。"
)
LOCATED_PARAGRAPH = (
    "「{a}」は「{b}」に位置する。"
    "「{a}」の所在地は「{b}」である。"
    "地理的に、「{a}」は「{b}」の中にある。"
)
PART_PARAGRAPH = (
    "「{a}」は「{b}」の一部である。"
    "「{b}」を構成する要素の一つが「{a}」だ。"
    "構造上、「{a}」は「{b}」に組み込まれている。"
)


class SparseTextbookLearnerTests(unittest.TestCase):
    def test_paraphrases_form_one_latent_relation_and_keep_roles(self) -> None:
        model = SparseTextbookLearner()
        first_relation = model.learn_fact_paragraph(
            PART_PARAGRAPH.format(a="歯車", b="機械"),
            "S1",
        )
        second_relation = model.learn_fact_paragraph(
            PART_PARAGRAPH.format(a="細胞膜", b="細胞"),
            "S2",
        )
        self.assertEqual(first_relation, second_relation)
        self.assertEqual(len(model.relation_patterns), 1)

        self.assertTrue(model.learn_question("「歯車」は何の一部ですか。", "機械"))
        accepted, relation = model.read_sentence(
            "「惑星系」を構成する要素の一つが「惑星」だ。",
            "S3",
        )
        self.assertTrue(accepted)
        self.assertEqual(relation, first_relation)
        answer = model.ask("本文を踏まえると、「惑星」は何の一部ですか。")
        self.assertEqual(answer.value, "惑星系")
        self.assertEqual(answer.sources, ("S3",))

    def test_rule_induction_returns_two_sources(self) -> None:
        model = SparseTextbookLearner()
        for index in range(6):
            a, b, c = f"A{index}", f"B{index}", f"C{index}"
            model.learn_fact_paragraph(CLASS_PARAGRAPH.format(a=a, b=b), f"T{index}-1")
            model.learn_fact_paragraph(CLASS_PARAGRAPH.format(a=b, b=c), f"T{index}-2")
            model.learn_fact_paragraph(CLASS_PARAGRAPH.format(a=a, b=c), f"T{index}-3")
        model.induce_rules(min_support=5, min_precision=0.95)

        model.read_sentence("別資料では、「試験A」は「試験B」の一種である。", "E1")
        model.read_sentence("別資料では、「試験B」は「試験C」の一種である。", "E2")
        self.assertTrue(
            model.learn_question(
                "「試験A」の最上位分類は何ですか。",
                "試験C",
                mode="closure",
            )
        )
        answer = model.ask("資料を統合すると、「試験A」の最上位分類は何ですか。")
        self.assertEqual(answer.value, "試験C")
        self.assertEqual(set(answer.sources), {"E1", "E2"})
        self.assertEqual(len(answer.proof), 2)

    def test_unknown_relation_abstains_without_mutating_graph(self) -> None:
        model = SparseTextbookLearner()
        model.learn_fact_paragraph(LOCATED_PARAGRAPH.format(a="研究所", b="都市"), "S1")
        before = dict(model.facts)
        accepted, reason = model.read_sentence(
            "「未知A」は「未知B」を祝福する。",
            "UNKNOWN",
        )
        self.assertFalse(accepted)
        self.assertEqual(reason, "abstain-unknown-relation")
        self.assertEqual(model.facts, before)

    def test_save_restore_preserves_question_and_rules(self) -> None:
        model = SparseTextbookLearner()
        model.learn_fact_paragraph(
            CLASS_PARAGRAPH.format(a="哺乳類", b="脊椎動物"),
            "S1",
        )
        self.assertTrue(model.learn_question("「哺乳類」は何の一種ですか。", "脊椎動物"))
        restored = SparseTextbookLearner.from_bytes(model.to_bytes())
        answer = restored.ask("「哺乳類」は何の一種ですか。")
        self.assertEqual(answer.value, "脊椎動物")
        self.assertEqual(answer.sources, ("S1",))


if __name__ == "__main__":
    unittest.main()
