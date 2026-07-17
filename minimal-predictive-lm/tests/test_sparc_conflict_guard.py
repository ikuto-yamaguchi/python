from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_conflict_guard import ConflictGuardLearner
from minimal_predictive_lm.sparc_open_textbook_gate import QUERIES, RELATIONS, base_training, train_queries


def trained():
    model = ConflictGuardLearner()
    records, _, chains = base_training()
    model.learn_paragraphs(records)
    model.induce_rules(min_support=6)
    train_queries(model, chains)
    return model


class ConflictGuardLearnerTest(unittest.TestCase):
    def test_rejects_conflicting_fact_without_mutation(self):
        model = trained()
        self.assertTrue(model.read_discourse_sentence("光合成の分類先は生物活動である。", "資料一")[0])
        before = (set(model.facts), set(model.entities))
        accepted, reason = model.read_discourse_sentence("光合成の分類先は化学反応である。", "誤資料")
        self.assertFalse(accepted)
        self.assertEqual(reason, "abstain-conflicting-fact")
        self.assertEqual(before, (set(model.facts), set(model.entities)))
        self.assertEqual(model.ask(QUERIES["tax"]["direct"][0].format(a="光合成")).value, "生物活動")

    def test_accepts_nonconflicting_new_fact(self):
        model = trained()
        accepted, _ = model.read_discourse_sentence("蒸発の分類先は物理現象である。", "資料")
        self.assertTrue(accepted)
        self.assertEqual(model.ask(QUERIES["tax"]["direct"][0].format(a="蒸発")).value, "物理現象")

    def test_duplicate_support_is_accepted(self):
        model = trained()
        self.assertTrue(model.read_discourse_sentence("凝縮の分類先は物理現象である。", "資料一")[0])
        self.assertTrue(model.read_discourse_sentence("凝縮の分類先は物理現象である。", "資料二")[0])

    def test_round_trip_preserves_guard(self):
        model = trained()
        restored = ConflictGuardLearner.from_bytes(model.to_bytes())
        self.assertIsInstance(restored, ConflictGuardLearner)
        self.assertEqual(restored.report()["conflict_state_slots_added"], 0)


if __name__ == "__main__":
    unittest.main()
