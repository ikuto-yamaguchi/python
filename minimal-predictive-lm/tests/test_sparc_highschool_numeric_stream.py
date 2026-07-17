import random
import unittest

from minimal_predictive_lm.sparc_highschool_numeric_stream import IndependentNumericDocumentLearner


def numeric_corpus():
    rows = []
    count_values = [("箱A", 2), ("箱B", 4), ("箱C", 7), ("箱D", 9)]
    temperature_values = [("試料A", 10), ("試料B", 20), ("試料C", 15), ("試料D", 25)]
    for subject, value in count_values:
        rows.extend([
            f"{subject}には{value}個ある",
            f"{value}個入っている箱は{subject}だ",
            f"{subject}の個数は{value}である",
        ])
    for subject, value in temperature_values:
        rows.extend([
            f"{subject}の温度は{value}度である",
            f"{value}度を示すのは{subject}だ",
            f"{subject}は温度{value}度の状態にある",
        ])
    rows.extend(["今日は雨が降る", "春は暖かい"])
    records = [(text, f"N{index:03d}") for index, text in enumerate(rows)]
    random.Random(23).shuffle(records)
    return records


class IndependentNumericDocumentLearnerTests(unittest.TestCase):
    def test_discovers_two_numeric_relations_without_groups(self):
        learner = IndependentNumericDocumentLearner()
        result = learner.learn_independent_numeric_documents(numeric_corpus())
        self.assertEqual(result.relation_clusters, 2)
        world = learner.learned_numeric_world().number_map()
        self.assertEqual(len(world), 8)
        count_relations = {relation for (subject, relation), value in world.items() if subject.startswith("箱")}
        temperature_relations = {relation for (subject, relation), value in world.items() if subject.startswith("試料")}
        self.assertEqual(len(count_relations), 1)
        self.assertEqual(len(temperature_relations), 1)
        self.assertNotEqual(count_relations, temperature_relations)

    def test_reads_unseen_numeric_observations(self):
        learner = IndependentNumericDocumentLearner()
        learner.learn_independent_numeric_documents(numeric_corpus())
        observed = learner.observe_world(["箱Zの個数は11である", "試料Zの温度は31度である"])
        self.assertEqual(observed.accepted, 2)
        self.assertEqual({value for value in observed.world.number_map().values()}, {11, 31})

    def test_teaches_numeric_event_without_grouped_observation_bootstrap(self):
        learner = IndependentNumericDocumentLearner()
        learner.learn_independent_numeric_documents(numeric_corpus())
        learner.teach_event_from_text("箱Aに3個加える", ["箱Aには2個ある"], ["箱Aには5個ある"])
        learner.teach_event_from_text("箱Bに3個加える", ["箱Bには4個ある"], ["箱Bには7個ある"])
        before = learner.observe_world(["箱Zには9個ある"]).world
        result = learner.apply("箱Zに3個加える", before)
        self.assertTrue(result.accepted)
        self.assertIn(12, result.world.number_map().values())

    def test_serialization_preserves_numeric_stream(self):
        learner = IndependentNumericDocumentLearner()
        learner.learn_independent_numeric_documents(numeric_corpus())
        restored = IndependentNumericDocumentLearner.from_bytes(learner.to_bytes())
        observed = restored.observe_world(["33度を示すのは試料Qだ"])
        self.assertEqual(observed.accepted, 1)
        self.assertIn(33, observed.world.number_map().values())
        self.assertFalse(restored.report()["numeric_paraphrase_group_labels_supplied"])


if __name__ == "__main__":
    unittest.main()
