from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_open_textbook_gate import QUERIES, RELATIONS, base_training, train_queries
from minimal_predictive_lm.sparc_zero_subject import ZeroSubjectLearner
from minimal_predictive_lm.sparc_zero_subject_index import IndexedZeroSubjectLearner


def trained(cls):
    model = cls()
    records, _, chains = base_training()
    model.learn_paragraphs(records)
    model.induce_rules(min_support=6)
    train_queries(model, chains)
    return model


class IndexedZeroSubjectLearnerTest(unittest.TestCase):
    def test_recovers_omitted_subject(self):
        model = trained(IndexedZeroSubjectLearner)
        passage = RELATIONS["tax"][3].format(a="光合成", b="生物活動") + "酸素を引き起こす。"
        accepted = model.read_passage(passage, "資料")
        answer = model.ask(QUERIES["cause"]["direct"][0].format(a="光合成"))
        self.assertTrue(all(ok for ok, _ in accepted))
        self.assertEqual(answer.value, "酸素")
        self.assertGreater(model.report()["zero_subject_suffix_index_entries"], 0)

    def test_index_reads_fewer_template_features_than_scan(self):
        indexed = trained(IndexedZeroSubjectLearner)
        scanned = trained(ZeroSubjectLearner)
        indexed.zero_subject_template_reads = 0
        scanned.zero_subject_template_reads = 0
        passage = RELATIONS["tax"][3].format(a="蒸発", b="物理現象") + "水蒸気を引き起こす。"
        indexed.read_passage(passage, "索引")
        scanned.read_passage(passage, "走査")
        self.assertLess(indexed.zero_subject_template_reads, scanned.zero_subject_template_reads)

    def test_unbound_fragment_abstains_without_mutation(self):
        model = trained(IndexedZeroSubjectLearner)
        model.reset_discourse()
        before = (len(model.facts), len(model.entities))
        accepted, _ = model.read_discourse_sentence("酸素を引き起こす。", "未知")
        self.assertFalse(accepted)
        self.assertEqual(before, (len(model.facts), len(model.entities)))

    def test_round_trip_preserves_index(self):
        model = trained(IndexedZeroSubjectLearner)
        restored = IndexedZeroSubjectLearner.from_bytes(model.to_bytes())
        self.assertEqual(model.zero_subject_suffix_index, restored.zero_subject_suffix_index)


if __name__ == "__main__":
    unittest.main()
