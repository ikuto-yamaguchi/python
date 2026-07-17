from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_zero_subject import ZeroSubjectLearner
from minimal_predictive_lm.sparc_discourse_focus import DiscourseFocusLearner
from minimal_predictive_lm.sparc_open_textbook_gate import RELATIONS, QUERIES, base_training, train_queries


def trained(cls):
    model = cls()
    records, _, chains = base_training()
    model.learn_paragraphs(records)
    model.induce_rules(min_support=6)
    train_queries(model, chains)
    return model


class ZeroSubjectLearnerTest(unittest.TestCase):
    def test_omitted_subject_uses_previous_subject(self):
        model = trained(ZeroSubjectLearner)
        passage = RELATIONS["tax"][3].format(a="光合成", b="生物活動") + "酸素を引き起こす。"
        accepted = model.read_passage(passage, "資料")
        answer = model.ask(QUERIES["cause"]["direct"][0].format(a="光合成"))
        self.assertTrue(all(ok for ok, _ in accepted))
        self.assertEqual(answer.value, "酸素")
        self.assertEqual(answer.sources, ("資料:2",))

    def test_unextended_focus_model_cannot_recover(self):
        model = trained(DiscourseFocusLearner)
        passage = RELATIONS["tax"][3].format(a="光合成", b="生物活動") + "酸素を引き起こす。"
        accepted = model.read_passage(passage, "資料")
        self.assertFalse(accepted[1][0])

    def test_unknown_fragment_does_not_mutate_graph(self):
        model = trained(ZeroSubjectLearner)
        model.read_discourse_sentence(RELATIONS["tax"][3].format(a="光合成", b="生物活動"), "資料:1")
        before = (len(model.facts), len(model.entities))
        accepted, mechanism = model.read_discourse_sentence("まったく未知の記述である。", "資料:2")
        self.assertFalse(accepted)
        self.assertEqual(mechanism, "abstain-unknown-surface")
        self.assertEqual(before, (len(model.facts), len(model.entities)))

    def test_no_additional_state_slots(self):
        model = trained(ZeroSubjectLearner)
        self.assertEqual(model.report()["zero_subject_state_slots_added"], 0)


if __name__ == "__main__":
    unittest.main()
