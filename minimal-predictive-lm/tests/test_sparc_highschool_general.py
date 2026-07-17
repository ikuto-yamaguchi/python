import unittest

from minimal_predictive_lm.sparc_highschool_general import SparseGeneralLearner, World


def w(*facts, numbers=None):
    return World.from_parts(facts, numbers or {})


class SparseHighSchoolGeneralTests(unittest.TestCase):
    def test_composes_unseen_surface_fragments(self):
        learner = SparseGeneralLearner()
        learner.teach("水は物質である", w(), w(("水", "kind", "物質")))
        learner.teach("鉄というものは金属に分類される", w(), w(("鉄", "kind", "金属")))
        result = learner.apply("酸素は気体に分類される", w())
        self.assertTrue(result.accepted)
        self.assertEqual(result.mechanism, "composed-surface-schema")
        self.assertIn(("酸素", "kind", "気体"), result.world.facts)

    def test_verbalizes_with_learned_inverse_schema(self):
        learner = SparseGeneralLearner()
        learner.teach("水は物質である", w(), w(("水", "kind", "物質")))
        self.assertEqual(learner.explain(w(("酸素", "kind", "気体"))), "酸素は気体である。")

    def test_numeric_and_abstention_are_preserved(self):
        learner = SparseGeneralLearner()
        learner.teach("箱Aに3個加える", w(numbers={("箱A", "count"): 2}), w(numbers={("箱A", "count"): 5}))
        result = learner.apply("箱Zに3個加える", w(numbers={("箱Z", "count"): 7}))
        self.assertEqual(result.world.number_map()[("箱Z", "count")], 10)
        unknown = learner.apply("今日は雨である", w(("保持", "R", "知識")))
        self.assertFalse(unknown.accepted)

    def test_serialization_keeps_bidirectional_schema(self):
        learner = SparseGeneralLearner()
        learner.teach("水は物質である", w(), w(("水", "kind", "物質")))
        restored = SparseGeneralLearner.from_bytes(learner.to_bytes())
        self.assertEqual(restored.explain(w(("銅", "kind", "金属"))), "銅は金属である。")


if __name__ == "__main__":
    unittest.main()
