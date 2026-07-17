import unittest

from minimal_predictive_lm.sparc_highschool_general import World
from minimal_predictive_lm.sparc_highschool_text_observation import TextObservationLearner


class TextObservationLearnerTests(unittest.TestCase):
    def make_learner(self):
        learner = TextObservationLearner()
        learner.learn_fact_observation_group([
            "水は物質である",
            "物質に分類されるものの一つが水だ",
            "水という対象は物質の仲間に入る",
        ])
        learner.learn_numeric_observation_group([
            "箱Aには2個ある",
            "2個入っている箱は箱Aだ",
            "箱Aの個数は2である",
        ])
        return learner

    def test_induces_opaque_fact_relation_from_raw_paraphrases(self):
        learner = self.make_learner()
        result = learner.apply("酸素は気体である", World())
        self.assertTrue(result.accepted)
        self.assertEqual(len(result.world.facts), 1)
        subject, relation, obj = next(iter(result.world.facts))
        self.assertEqual((subject, obj), ("酸素", "気体"))
        self.assertTrue(relation.startswith("TR"))

    def test_clusters_separate_raw_groups_into_one_relation(self):
        learner = self.make_learner()
        first = next(iter(learner.programs[pid].edits)).relation if False else None
        relation = learner.learn_fact_observation_group([
            "鉄というものは金属に分類される",
            "金属の一つとして鉄が知られる",
            "鉄を分類すると金属に入る",
        ])
        base_relation = learner.programs[next(iter(learner.fact_program_ids))].edits[0].relation
        self.assertEqual(relation, base_relation)
        self.assertEqual(learner.fact_relation_merges, 1)
        result = learner.apply("酸素は気体に分類される", World())
        self.assertTrue(result.accepted)
        self.assertIn(("酸素", base_relation, "気体"), result.world.facts)

    def test_builds_numeric_world_without_relation_id(self):
        learner = self.make_learner()
        observed = learner.observe_world(["箱Zには9個ある"])
        self.assertEqual(observed.accepted, 1)
        self.assertEqual(observed.abstained, 0)
        ((subject, relation), value), = observed.world.number_map().items()
        self.assertEqual((subject, value), ("箱Z", 9))
        self.assertTrue(relation.startswith("NR"))

    def test_teaches_event_from_japanese_observations_only(self):
        learner = self.make_learner()
        learner.teach_event_from_text("箱Aに3個加える", ["箱Aには2個ある"], ["箱Aには5個ある"])
        learner.teach_event_from_text("箱Bに3個加える", ["箱Bには4個ある"], ["箱Bには7個ある"])
        before = learner.observe_world(["箱Zには9個ある"]).world
        result = learner.apply("箱Zに3個加える", before)
        self.assertTrue(result.accepted)
        ((subject, _relation), value), = result.world.number_map().items()
        self.assertEqual((subject, value), ("箱Z", 12))

    def test_serialization_preserves_text_observation_layer(self):
        learner = self.make_learner()
        restored = TextObservationLearner.from_bytes(learner.to_bytes())
        observed = restored.observe_world(["箱Qの個数は11である"])
        self.assertEqual(observed.accepted, 1)
        self.assertIn(11, observed.world.number_map().values())
        report = restored.report()
        self.assertFalse(report["relation_ids_supplied_by_caller"])
        self.assertFalse(report["grounded_worlds_supplied_by_caller"])


if __name__ == "__main__":
    unittest.main()
