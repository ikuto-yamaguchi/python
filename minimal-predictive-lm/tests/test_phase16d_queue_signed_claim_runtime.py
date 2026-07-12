from __future__ import annotations

import unittest

from minimal_predictive_lm.corrected_proposition_machine import CorrectedPropositionMachine
from minimal_predictive_lm.phase16d_experiment import build_chain_prompt
from minimal_predictive_lm.queue_signed_claim_runtime import QueueSignedClaimRuntime
from minimal_predictive_lm.signed_claim_graph import SignedClaimRuntime


class Phase16dQueueSignedClaimRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.machine = CorrectedPropositionMachine()

    def test_reverse_chain_matches_legacy_with_fewer_operations(self) -> None:
        prompt, expected = build_chain_prompt(128, seed=17, order="reverse")
        program = self.machine.claim_machine.compile(prompt)
        self.assertIsNotNone(program)
        assert program is not None
        legacy = SignedClaimRuntime().execute(program)
        queue = QueueSignedClaimRuntime().execute(program)
        self.assertEqual(legacy.output, expected)
        self.assertEqual(queue.output, expected)
        self.assertLess(queue.operations * 10, legacy.operations)

    def test_shuffled_phrase_and_attribution_chain_is_order_invariant(self) -> None:
        prompt, expected = build_chain_prompt(73, seed=91, order="shuffled")
        prediction = self.machine.predict(prompt)
        self.assertEqual(prediction.output, expected)
        self.assertEqual(prediction.family, "proposition-signed-claim")

    def test_conflict_and_unanchored_cycle_still_abstain(self) -> None:
        conflict = self.machine.predict(
            "Question: BaseA is reliable. JudgeB says BaseA is reliable. "
            "JudgeB reports BaseA is unreliable. Does JudgeB tell the truth?"
        )
        unanchored = self.machine.predict(
            "Question: AnchorA is reliable. NodeB says NodeC is reliable. "
            "NodeC claims NodeB is reliable. Does NodeB tell the truth?"
        )
        self.assertIsNone(conflict.output)
        self.assertIsNone(unanchored.output)

    def test_queue_operation_growth_is_linear(self) -> None:
        rows: list[tuple[int, int]] = []
        for claims in (8, 16, 32, 64, 128):
            prompt, expected = build_chain_prompt(claims, seed=5, order="reverse")
            program = self.machine.claim_machine.compile(prompt)
            self.assertIsNotNone(program)
            assert program is not None
            prediction = QueueSignedClaimRuntime().execute(program)
            self.assertEqual(prediction.output, expected)
            rows.append((claims, prediction.operations))
        for claims, operations in rows:
            self.assertLessEqual(operations, 4 * claims + 4)


if __name__ == "__main__":
    unittest.main()
