from __future__ import annotations

import unittest

from minimal_predictive_lm.generic_causal_machine import (
    CausalEvent,
    CausalScenario,
    IntentEvidence,
    NormAwareCausalMachine,
    OutcomeRule,
)


class Phase16eGenericCausalMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.machine = NormAwareCausalMachine()

    def test_abnormal_conjunct_is_selected_over_normal_cofactor(self) -> None:
        events = (
            CausalEvent("allowed_wire", True, True),
            CausalEvent("forbidden_wire", True, False),
        )
        rule = OutcomeRule.all_of("allowed_wire", "forbidden_wire")
        normal = self.machine.judge_cause(CausalScenario(events, rule, "allowed_wire"))
        abnormal = self.machine.judge_cause(CausalScenario(events, rule, "forbidden_wire"))
        self.assertFalse(normal.output)
        self.assertEqual(normal.classification, "normal-conjunct-suppressed")
        self.assertTrue(abnormal.output)
        self.assertEqual(abnormal.classification, "but-for")

    def test_redundant_abnormal_disjunct_is_not_selected(self) -> None:
        events = (
            CausalEvent("unexpected_order", True, False),
            CausalEvent("usual_order", True, True),
        )
        prediction = self.machine.judge_cause(
            CausalScenario(events, OutcomeRule.any_of("unexpected_order", "usual_order"), "unexpected_order")
        )
        self.assertFalse(prediction.output)
        self.assertEqual(prediction.classification, "redundant-under-normal-contingencies")

    def test_normality_improving_contingency_can_reveal_a_cause(self) -> None:
        events = (
            CausalEvent("retained_power", True, True),
            CausalEvent("abnormal_backup", True, False),
        )
        prediction = self.machine.judge_cause(
            CausalScenario(events, OutcomeRule.any_of("retained_power", "abnormal_backup"), "retained_power")
        )
        self.assertTrue(prediction.output)
        self.assertEqual(prediction.classification, "normality-contingency")
        self.assertEqual(prediction.contingency, ("abnormal_backup",))

    def test_threshold_event_is_directly_pivotal(self) -> None:
        events = (
            CausalEvent("first", True, True),
            CausalEvent("second", True, True),
            CausalEvent("third", True, False),
        )
        prediction = self.machine.judge_cause(
            CausalScenario(events, OutcomeRule(("first", "second", "third"), 3), "third")
        )
        self.assertTrue(prediction.output)
        self.assertEqual(prediction.classification, "but-for")

    def test_intent_distinguishes_foreseen_side_effect_from_lucky_accident(self) -> None:
        side_effect = self.machine.judge_intent(
            IntentEvidence(True, controlled_action=True, expected_path=True, foresaw_side_effect=True)
        )
        accident = self.machine.judge_intent(
            IntentEvidence(True, controlled_action=True, expected_path=False, goal=True)
        )
        self.assertTrue(side_effect.output)
        self.assertFalse(accident.output)
        self.assertEqual(accident.classification, "accidental-realization")


if __name__ == "__main__":
    unittest.main()
