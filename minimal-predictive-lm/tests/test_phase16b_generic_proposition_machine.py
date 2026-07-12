from __future__ import annotations

import unittest

from minimal_predictive_lm.corrected_proposition_machine import CorrectedPropositionMachine
from minimal_predictive_lm.generic_proposition_machine import (
    GenericPropositionMachine,
    MonadicSentence,
    MonadicTheory,
    ParityConstraintGraph,
    all_of,
    atom,
    implies,
    neg,
)


class Phase16bGenericPropositionMachineTests(unittest.TestCase):
    def test_signed_graph_propagates_and_detects_conflicts(self) -> None:
        graph = ParityConstraintGraph()
        graph.seed("ada", True)
        graph.relate("bea", "ada", inverted=True)
        graph.relate("cy", "bea", inverted=False)
        self.assertFalse(graph.resolve("cy"))

        conflict = ParityConstraintGraph()
        conflict.seed("left", True)
        conflict.seed("right", True)
        conflict.relate("left", "right", inverted=True)
        self.assertIsNone(conflict.resolve("left"))

    def test_monadic_runtime_accepts_contraposition_not_converse(self) -> None:
        p = atom("p")
        q = atom("q")
        premise = MonadicSentence("all", implies(p, q))
        self.assertTrue(
            MonadicTheory((premise,)).entails(
                MonadicSentence("all", implies(neg(q), neg(p)))
            )
        )
        self.assertFalse(
            MonadicTheory((premise,)).entails(
                MonadicSentence("all", implies(q, p))
            )
        )

    def test_monadic_runtime_combines_universal_and_existential_evidence(self) -> None:
        traveler = atom("traveler")
        awake = atom("awake")
        indoors = atom("indoors")
        premises = (
            MonadicSentence("all", implies(traveler, neg(indoors))),
            MonadicSentence("some", all_of(awake, indoors)),
        )
        conclusion = MonadicSentence("some", all_of(awake, neg(traveler)))
        self.assertTrue(MonadicTheory(premises).entails(conclusion))

    def test_independent_truth_chain_uses_shared_parity_runtime(self) -> None:
        prompt = (
            "Question: Ada tells the truth. Bea says Ada lies. "
            "Cy says Bea tells the truth. Does Cy tell the truth?"
        )
        prediction = GenericPropositionMachine().predict(prompt)
        self.assertEqual(prediction.output, "No")
        self.assertEqual(prediction.family, "proposition-parity")

    def test_independent_controlled_argument_uses_model_search(self) -> None:
        valid_prompt = (
            '"First premise: Every quiet traveler is an awake person. '
            "Second premise: No awake person is an indoor person. "
            "Therefore, no quiet traveler is an indoor person.\"\n"
            "Is the argument, given the explicitly stated premises, "
            "deductively valid or invalid?\nOptions:\n- valid \n- invalid"
        )
        invalid_prompt = (
            '"First premise: Every quiet traveler is an awake person. '
            "Therefore, every awake person is a quiet traveler.\"\n"
            "Is the argument, given the explicitly stated premises, "
            "deductively valid or invalid?\nOptions:\n- valid \n- invalid"
        )
        machine = GenericPropositionMachine()
        self.assertEqual(machine.predict(valid_prompt).output, "valid")
        self.assertEqual(machine.predict(invalid_prompt).output, "invalid")

    def test_none_of_disjunction_has_negation_over_full_scope(self) -> None:
        prompt = (
            '"First premise: Everyone who is calm is focused. '
            "Second premise: Whoever is neither noisy nor hurried is calm. "
            "Therefore, whoever is none of this: noisy or hurried, is focused.\"\n"
            "Is the argument, given the explicitly stated premises, "
            "deductively valid or invalid?\nOptions:\n- valid \n- invalid"
        )
        self.assertEqual(CorrectedPropositionMachine().predict(prompt).output, "valid")

    def test_machine_has_no_benchmark_task_name_branch(self) -> None:
        machine = CorrectedPropositionMachine()
        self.assertEqual(machine.benchmark_task_name_branches, 0)
        self.assertEqual(machine.human_designed_surface_compilers, 2)


if __name__ == "__main__":
    unittest.main()
