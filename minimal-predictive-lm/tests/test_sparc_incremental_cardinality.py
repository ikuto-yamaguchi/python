from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_incremental_cardinality import IncrementalCardinalityLearner
from minimal_predictive_lm.sparc_open_textbook_gate import RELATIONS, base_training, paragraph, train_queries


def trained():
    model = IncrementalCardinalityLearner()
    records, _, chains = base_training()
    model.learn_paragraphs(records)
    evidence = []
    for index in range(8):
        evidence.append((paragraph("produce", f"工程{index}", f"生成物{index}"), f"単値-{index}"))
        for whole in (f"装置甲{index}", f"装置乙{index}"):
            evidence.append((paragraph("part", f"共通部品{index}", whole), f"多値-{index}-{whole}"))
    model.learn_paragraphs(evidence)
    model.induce_rules(min_support=6)
    train_queries(model, chains)
    return model


class IncrementalCardinalityTest(unittest.TestCase):
    def test_local_update_does_not_trigger_full_rebuild(self):
        model = trained()
        before_bootstrap = model.cardinality_bootstrap_reads
        before_parent_reads = model.cardinality_rebuild_reads
        sentence = RELATIONS["produce"][0].format(a="新工程", b="新生成物")
        self.assertTrue(model.read_discourse_sentence(sentence, "新資料")[0])
        self.assertEqual(model.cardinality_bootstrap_reads, before_bootstrap)
        self.assertEqual(model.cardinality_rebuild_reads, before_parent_reads)
        self.assertEqual(model.cardinality_local_updates, 1)
        self.assertEqual(model.cardinality_rebuilds_avoided, 1)

    def test_functional_conflict_and_multivalue_behavior_match(self):
        model = trained()
        first = RELATIONS["produce"][0].format(a="評価工程", b="生成物甲")
        second = RELATIONS["produce"][0].format(a="評価工程", b="生成物乙")
        self.assertTrue(model.read_discourse_sentence(first, "正")[0])
        accepted, reason = model.read_discourse_sentence(second, "誤")
        self.assertFalse(accepted)
        self.assertEqual(reason, "abstain-functional-conflict")

        left = RELATIONS["part"][3].format(a="共通軸", b="装置甲")
        right = RELATIONS["part"][3].format(a="共通軸", b="装置乙")
        self.assertTrue(model.read_discourse_sentence(left, "甲")[0])
        self.assertTrue(model.read_discourse_sentence(right, "乙")[0])

    def test_round_trip_preserves_incremental_counters(self):
        model = trained()
        restored = IncrementalCardinalityLearner.from_bytes(model.to_bytes())
        self.assertEqual(restored.cardinality_subjects, model.cardinality_subjects)
        self.assertEqual(restored.cardinality_multi_subjects, model.cardinality_multi_subjects)
        self.assertEqual(restored.report()["incremental_cardinality_state_slots_added"], 0)


if __name__ == "__main__":
    unittest.main()
