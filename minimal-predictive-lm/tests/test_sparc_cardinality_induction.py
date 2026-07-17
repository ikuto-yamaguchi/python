from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_cardinality_induction import CardinalityInductionLearner
from minimal_predictive_lm.sparc_open_textbook_gate import RELATIONS, base_training, paragraph, train_queries


def trained():
    model = CardinalityInductionLearner()
    records, _, chains = base_training()
    model.learn_paragraphs(records)
    cardinality = []
    for index in range(8):
        cardinality.append(
            (paragraph("produce", f"工程{index}", f"生成物{index}"), f"単値-{index}")
        )
        for whole in (f"装置甲{index}", f"装置乙{index}"):
            cardinality.append(
                (paragraph("part", f"共通部品{index}", whole), f"多値-{index}-{whole}")
            )
    model.learn_paragraphs(cardinality)
    model.induce_rules(min_support=6)
    train_queries(model, chains)
    return model


class CardinalityInductionTest(unittest.TestCase):
    def test_functional_relation_rejects_conflict(self):
        model = trained()
        first = RELATIONS["produce"][0].format(a="光合成工程", b="酸素")
        second = RELATIONS["produce"][0].format(a="光合成工程", b="窒素")
        relation = model._match_sentence(first)[0][1]
        self.assertIn(relation, model.functional_relations)
        self.assertTrue(model.read_discourse_sentence(first, "正")[0])
        accepted, reason = model.read_discourse_sentence(second, "誤")
        self.assertFalse(accepted)
        self.assertEqual(reason, "abstain-functional-conflict")
        self.assertEqual(model.out_index["光合成工程"][relation], {"酸素"})

    def test_induced_multivalued_relation_accepts_two_objects(self):
        model = trained()
        first = RELATIONS["part"][3].format(a="共通軸", b="装置甲")
        second = RELATIONS["part"][3].format(a="共通軸", b="装置乙")
        relation = model._match_sentence(first)[0][1]
        self.assertIn(relation, model.nonfunctional_relations)
        self.assertTrue(model.read_discourse_sentence(first, "甲")[0])
        self.assertTrue(model.read_discourse_sentence(second, "乙")[0])
        self.assertEqual(model.out_index["共通軸"][relation], {"装置甲", "装置乙"})

    def test_round_trip_and_no_supplied_cardinality(self):
        model = trained()
        restored = CardinalityInductionLearner.from_bytes(model.to_bytes())
        self.assertEqual(restored.functional_relations, model.functional_relations)
        self.assertEqual(restored.nonfunctional_relations, model.nonfunctional_relations)
        self.assertFalse(restored.report()["relation_cardinalities_supplied"])
        self.assertEqual(restored.report()["cardinality_state_slots_added"], 0)


if __name__ == "__main__":
    unittest.main()
