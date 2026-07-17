import random
import unittest

from minimal_predictive_lm.sparc_highschool_temporal_stream import TemporalNarrativeLearner


def numeric_corpus():
    rows = []
    for subject, value in [("青箱", 2), ("赤容器", 4), ("大型倉庫", 7), ("小型ケース", 9)]:
        rows += [f"{subject}には{value}個ある", f"{value}個入っている対象は{subject}だ", f"{subject}の個数は{value}である"]
    for subject, value in [("試料甲", 10), ("検体乙", 20), ("素材丙", 15), ("サンプル丁", 25)]:
        rows += [f"{subject}の温度は{value}度である", f"{value}度を示す対象は{subject}だ", f"{subject}は温度{value}度の状態にある"]
    records = [(text, f"N{index}") for index, text in enumerate(rows)]
    random.Random(23).shuffle(records)
    return records


def temporal_corpus():
    return [
        ("箱Aには2個ある。箱Aに3個加える。箱Aには5個ある。", "T1"),
        ("箱Bには4個ある。箱Bに3個加える。箱Bには7個ある。", "T2"),
        ("箱Aには3個ある。箱Aを2倍にする。箱Aには6個ある。", "T3"),
        ("箱Bには5個ある。箱Bを2倍にする。箱Bには10個ある。", "T4"),
        ("試料Aの温度は10度である。試料Aの温度を5度上げる。試料Aの温度は15度である。", "T5"),
        ("試料Bの温度は20度である。試料Bの温度を5度上げる。試料Bの温度は25度である。", "T6"),
    ]


class TemporalNarrativeLearnerTests(unittest.TestCase):
    def make_learner(self):
        learner = TemporalNarrativeLearner()
        learner.learn_independent_numeric_documents(numeric_corpus())
        return learner

    def test_discovers_event_sentences_between_observations(self):
        learner = self.make_learner()
        result = learner.learn_chronological_documents(temporal_corpus())
        self.assertEqual(result.transitions_found, 6)
        self.assertEqual(len(learner.programs), 3)
        report = learner.report()
        self.assertFalse(report["before_after_worlds_supplied"])
        self.assertFalse(report["event_sentence_labels_supplied"])

    def test_transfers_program_from_unlabeled_narratives(self):
        learner = self.make_learner()
        learner.learn_chronological_documents(temporal_corpus())
        before = learner.observe_world(["箱Zには9個ある"]).world
        result = learner.apply("箱Zに3個加える", before)
        self.assertTrue(result.accepted)
        self.assertIn(12, result.world.number_map().values())

    def test_abstains_on_passage_without_observation_event_observation(self):
        learner = self.make_learner()
        result = learner.learn_chronological_document("今日は雨が降る。空は暗い。風も強い。", "D")
        self.assertEqual(result.transitions_found, 0)
        self.assertEqual(result.abstained_documents, 1)

    def test_serialization_preserves_temporal_programs(self):
        learner = self.make_learner()
        learner.learn_chronological_documents(temporal_corpus())
        restored = TemporalNarrativeLearner.from_bytes(learner.to_bytes())
        before = restored.observe_world(["試料Zの温度は30度である"]).world
        result = restored.apply("試料Zの温度を5度上げる", before)
        self.assertTrue(result.accepted)
        self.assertIn(35, result.world.number_map().values())


if __name__ == "__main__":
    unittest.main()
