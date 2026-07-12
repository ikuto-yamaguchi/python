from __future__ import annotations

import unittest

from minimal_predictive_lm.induced_proposition_machine import InducedPropositionMachine
from minimal_predictive_lm.phase16d_experiment import build_chain_prompt


class Phase16fInducedClauseCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.machine = InducedPropositionMachine()

    def test_seven_observations_induce_three_role_templates(self) -> None:
        compiler = self.machine.induced_clause_compiler
        self.assertEqual(compiler.training_observations, 7)
        self.assertEqual(len(compiler.templates), 3)
        self.assertEqual(
            {template.kind for template in compiler.templates},
            {"base", "claim", "query"},
        )
        self.assertEqual(compiler.benchmark_task_name_branches, 0)

    def test_public_style_chain_uses_induced_compiler(self) -> None:
        prediction = self.machine.predict(
            "Question: Ada tells the truth. Bea says Ada lies. "
            "Cy says Bea tells the truth. Does Cy tell the truth?"
        )
        self.assertEqual(prediction.output, "No")
        self.assertEqual(prediction.family, "proposition-induced-signed-claim")

    def test_clause_templates_transfer_to_sensor_and_review_domains(self) -> None:
        cases = (
            (
                "Question: SensorA is accurate. SensorB claims SensorA is inaccurate. "
                "SensorC reports SensorB is correct. Does SensorC tell the truth?",
                "No",
            ),
            (
                "Question: PatchA is valid. ReviewerB says PatchA is invalid. "
                "ReviewerC claims ReviewerB is wrong. Does ReviewerC tell the truth?",
                "Yes",
            ),
        )
        for prompt, expected in cases:
            with self.subTest(prompt=prompt):
                self.assertEqual(self.machine.predict(prompt).output, expected)

    def test_reverse_long_chain_preserves_queue_semantics(self) -> None:
        prompt, expected = build_chain_prompt(128, seed=47, order="reverse")
        prediction = self.machine.predict(prompt)
        self.assertEqual(prediction.output, expected)
        self.assertLessEqual(prediction.operations, 4 * 128 + 4)

    def test_unknown_clause_order_truth_phrase_conflict_and_cycle_abstain(self) -> None:
        prompts = (
            (
                "Question: BaseA is reliable. According to BaseA, JudgeB is reliable. "
                "Does JudgeB tell the truth?"
            ),
            (
                "Question: BaseA is trustworthy. JudgeB says BaseA is reliable. "
                "Does JudgeB tell the truth?"
            ),
            (
                "Question: BaseA is reliable. JudgeB says BaseA is reliable. "
                "JudgeB reports BaseA is unreliable. Does JudgeB tell the truth?"
            ),
            (
                "Question: AnchorA is reliable. NodeB says NodeC is reliable. "
                "NodeC claims NodeB is reliable. Does NodeB tell the truth?"
            ),
        )
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertIsNone(self.machine.predict(prompt).output)

    def test_controlled_formal_logic_compiler_is_retained(self) -> None:
        prompt = (
            '"First premise: Every quiet traveler is an awake person. '
            "Second premise: No awake person is an indoor person. "
            "Therefore, no quiet traveler is an indoor person.\"\n"
            "Is the argument, given the explicitly stated premises, "
            "deductively valid or invalid?\nOptions:\n- valid \n- invalid"
        )
        prediction = self.machine.predict(prompt)
        self.assertEqual(prediction.output, "valid")
        self.assertEqual(prediction.family, "proposition-monadic")

    def test_only_formal_surface_compiler_remains_hand_written(self) -> None:
        self.assertEqual(self.machine.human_designed_surface_compilers, 1)
        self.assertEqual(self.machine.induced_surface_compilers, 1)
        self.assertGreater(self.machine.induced_clause_compiler.description_bits, 0)


if __name__ == "__main__":
    unittest.main()
