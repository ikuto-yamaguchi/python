import unittest

from minimal_predictive_lm.risk_bounded_semantic_version_space import (
    Operation,
    Probe,
    RiskBoundedSemanticVersionSpace,
)


class RiskBoundedSemanticVersionSpaceTests(unittest.TestCase):
    def test_identifiable_unknown_is_grounded_by_probes(self):
        operations = (
            Operation("a", ((0,),), 0.1),
            Operation("b", ((1,),), 0.1),
            Operation("danger", ((2,),), 0.9),
        )
        probes = (
            Probe("p0", (0, 1, 1), 0.01),
            Probe("p1", (0, 0, 1), 0.01),
        )
        model = RiskBoundedSemanticVersionSpace(operations, probes)
        utterance = "未知の依頼"
        model.begin(utterance)
        used = frozenset()
        while len(model.version_spaces[utterance]) > 1:
            probe = model.choose_probe(utterance, used)
            self.assertIsNotNone(probe)
            model.observe_probe(utterance, probe, probe.outcomes[1])
            used = used | {probe.name}
        self.assertEqual(model.safe_decision(utterance), ("execute", 1))

    def test_observationally_identical_operations_remain_ambiguous(self):
        operations = (
            Operation("left", ((0,),), 0.1),
            Operation("right", ((1,),), 0.1),
        )
        probes = (Probe("same", (7, 7), 0.01),)
        model = RiskBoundedSemanticVersionSpace(operations, probes)
        model.begin("どちらか不明")
        probe = model.choose_probe("どちらか不明")
        self.assertIsNotNone(probe)
        model.observe_probe("どちらか不明", probe, 7)
        self.assertEqual(model.safe_decision("どちらか不明"), ("probe", None))

    def test_high_risk_operation_requires_confirmation(self):
        operations = (
            Operation("safe", ((0,),), 0.05),
            Operation("danger", ((1,),), 0.95),
        )
        model = RiskBoundedSemanticVersionSpace(
            operations, (Probe("which", (0, 1), 0.01),), risk_budget=0.25
        )
        model.begin("危険かもしれない依頼")
        probe = model.choose_probe("危険かもしれない依頼")
        model.observe_probe("危険かもしれない依頼", probe, 1)
        self.assertEqual(model.safe_decision("危険かもしれない依頼"), ("confirm", 1))


if __name__ == "__main__":
    unittest.main()
