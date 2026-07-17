from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_discourse_focus import DiscourseFocusLearner
from minimal_predictive_lm.sparc_open_textbook_gate import RELATIONS, QUERIES, base_training, train_queries


class DiscourseFocusLearnerTest(unittest.TestCase):
    def trained(self):
        model = DiscourseFocusLearner()
        records, _, chains = base_training()
        model.learn_paragraphs(records)
        model.induce_rules(min_support=6)
        train_queries(model, chains)
        return model

    def test_subject_anaphora_updates_original_subject(self):
        model = self.trained()
        first = "光合成"
        middle = "生物活動"
        last = "酸素"
        passage = RELATIONS["tax"][3].format(a=first, b=middle) + "これは" + last + "を引き起こす。"
        result = model.read_passage(passage, "資料")
        self.assertEqual([True, True], [accepted for accepted, _ in result])
        answer = model.ask(QUERIES["cause"]["direct"][0].format(a=first))
        self.assertEqual(last, answer.value)
        self.assertEqual(("資料:2",), answer.sources)

    def test_object_anaphora_uses_previous_object(self):
        model = self.trained()
        first = "葉緑体"
        middle = "細胞小器官"
        last = "細胞内"
        passage = RELATIONS["part"][3].format(a=first, b=middle) + "その対象は" + last + "に位置する。"
        model.read_passage(passage, "資料")
        answer = model.ask(QUERIES["loc"]["direct"][0].format(a=middle))
        self.assertEqual(last, answer.value)

    def test_unbound_anaphora_abstains_without_mutation(self):
        model = self.trained()
        before = (len(model.facts), len(model.entities))
        accepted, mechanism = model.read_discourse_sentence("これは酸素を引き起こす。", "未知")
        self.assertFalse(accepted)
        self.assertEqual("abstain-unbound-subject-anaphora", mechanism)
        self.assertEqual(before, (len(model.facts), len(model.entities)))

    def test_round_trip_preserves_focus_extension(self):
        model = self.trained()
        restored = DiscourseFocusLearner.from_bytes(model.to_bytes())
        self.assertIsInstance(restored, DiscourseFocusLearner)
        self.assertEqual(2, restored.report()["discourse_state_slots"])


if __name__ == "__main__":
    unittest.main()
