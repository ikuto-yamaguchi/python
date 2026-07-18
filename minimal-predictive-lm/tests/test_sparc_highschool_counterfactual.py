import unittest

from minimal_predictive_lm.sparc_highschool_counterfactual import CounterfactualNarrativeLearner
from minimal_predictive_lm.sparc_highschool_general import World
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


class CounterfactualNarrativeLearnerTests(unittest.TestCase):
    def make_learner(self):
        learner = CounterfactualNarrativeLearner()
        learner.learn_independent_numeric_documents(_numeric_corpus())
        learner.learn_long_chronological_documents(_long_corpus())
        return learner

    def test_intervention_reuses_one_program_bank_and_shared_prefix(self):
        learner = self.make_learner()
        start = learner.observe_world(["箱Zには1個ある"]).world
        result = learner.compare_intervention(
            start,
            ["箱Zに3個加える", "箱Zを2倍にする", "箱Zに3個加える"],
            intervention_at=1,
            replacement_actions=["箱Zに3個加える"],
        )
        self.assertTrue(result.accepted)
        values = result.changed_numbers[0]
        self.assertEqual(values[2:], (11, 10))
        self.assertEqual(result.shared_prefix, ("箱Zに3個加える",))
        self.assertFalse(learner.report()["branch_specific_program_bank"])

    def test_counterfactual_branch_does_not_mutate_factual_world(self):
        learner = self.make_learner()
        start = learner.observe_world(["箱Qには2個ある"]).world
        result = learner.compare_intervention(
            start,
            ["箱Qに3個加える", "箱Qを2倍にする"],
            intervention_at=0,
            replacement_actions=["箱Qを2倍にする"],
        )
        self.assertTrue(result.accepted)
        self.assertNotEqual(result.factual.world, result.counterfactual.world)
        self.assertEqual(start, learner.observe_world(["箱Qには2個ある"]).world)

    def test_unknown_replacement_abstains_without_partial_branch(self):
        learner = self.make_learner()
        start = learner.observe_world(["箱Rには4個ある"]).world
        result = learner.compare_intervention(
            start,
            ["箱Rに3個加える", "箱Rを2倍にする"],
            intervention_at=0,
            replacement_actions=["箱Rを未知の規則で変える"],
        )
        self.assertFalse(result.accepted)
        self.assertFalse(result.counterfactual.accepted)
        self.assertEqual(result.counterfactual.world, start)

    def test_branching_survives_serialization(self):
        learner = self.make_learner()
        restored = CounterfactualNarrativeLearner.from_bytes(learner.to_bytes())
        start = restored.observe_world(["試料Zの温度は10度である"]).world
        result = restored.compare_intervention(
            start,
            ["試料Zの温度を5度上げる", "試料Zの温度を5度上げる"],
            intervention_at=1,
            replacement_actions=[],
        )
        self.assertTrue(result.accepted)
        self.assertEqual(result.changed_numbers[0][2:], (20, 15))


if __name__ == "__main__":
    unittest.main()
