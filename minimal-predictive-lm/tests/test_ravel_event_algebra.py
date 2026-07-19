from __future__ import annotations

import unittest

from minimal_predictive_lm.ravel_event_algebra import (
    EventProgramBank,
    RecursiveMacroCompiler,
    explanatory_work,
)


class RavelEventAlgebraTests(unittest.TestCase):
    def test_entity_names_do_not_change_program_identity(self) -> None:
        bank = EventProgramBank()
        first = bank.observe_transition(
            {"alice": {"x": 2, "energy": 5}},
            {"alice": {"x": 5, "energy": 4}},
            source_id="episode-a",
        )
        second = bank.observe_transition(
            {"robot-77": {"x": 10, "energy": 9}},
            {"robot-77": {"x": 13, "energy": 8}},
            source_id="episode-b",
        )
        self.assertEqual(first.program_id, second.program_id)
        self.assertFalse(first.reused_existing_program)
        self.assertTrue(second.reused_existing_program)
        self.assertEqual(bank.get(first.program_id).support, 2)
        self.assertEqual(bank.get(first.program_id).provenance, {"episode-a", "episode-b"})

    def test_program_runs_forward_and_inverse_on_unseen_entity(self) -> None:
        bank = EventProgramBank()
        observation = bank.observe_transition(
            {"sample": {"temperature": 20, "phase": "solid"}},
            {"sample": {"temperature": 25, "phase": "liquid"}},
        )
        program = bank.get(observation.program_id)
        unseen = {"unknown": {"temperature": 7, "phase": "solid"}}
        result = program.forward(unseen, ("unknown",))
        self.assertEqual(result, {"unknown": {"temperature": 12, "phase": "liquid"}})
        restored = program.inverse(result, ("unknown",))
        self.assertEqual(restored, unseen)

    def test_create_and_delete_are_reversible(self) -> None:
        bank = EventProgramBank()
        observation = bank.observe_transition(
            {"box": {"closed": True, "label": "A"}},
            {"box": {"closed": True, "content": "key"}},
        )
        program = bank.get(observation.program_id)
        forward = program.forward(
            {"other-box": {"closed": True, "label": "A"}},
            ("other-box",),
        )
        self.assertEqual(forward, {"other-box": {"closed": True, "content": "key"}})
        self.assertEqual(
            program.inverse(forward, ("other-box",)),
            {"other-box": {"closed": True, "label": "A"}},
        )

    def test_repeated_chain_compiles_to_one_active_macro_step(self) -> None:
        bank = EventProgramBank()
        move = bank.observe_transition(
            {"a": {"x": 0}}, {"a": {"x": 1}}
        ).program_id
        charge = bank.observe_transition(
            {"a": {"energy": 2}}, {"a": {"energy": 5}}
        ).program_id
        cool = bank.observe_transition(
            {"a": {"temperature": 9}}, {"a": {"temperature": 7}}
        ).program_id
        chain = (move, charge, cool)
        compiler = RecursiveMacroCompiler(bank, min_support=3, max_length=4)
        self.assertEqual(compiler.observe_sequence(chain), ())
        self.assertEqual(compiler.observe_sequence(chain), ())
        created = compiler.observe_sequence(chain)
        macro = next(row for row in created if row.program_ids == chain)
        self.assertEqual(macro.primitive_steps, 3)
        self.assertEqual(macro.active_steps, 1)
        self.assertEqual(compiler.longest_macro_prefix(chain), macro)

        initial = {"z": {"x": 4, "energy": 1, "temperature": 20}}
        result = compiler.execute_forward(
            macro,
            initial,
            (("z",), ("z",), ("z",)),
        )
        self.assertEqual(
            result,
            {"z": {"x": 5, "energy": 4, "temperature": 18}},
        )
        self.assertEqual(
            compiler.execute_inverse(
                macro,
                result,
                (("z",), ("z",), ("z",)),
            ),
            initial,
        )

    def test_explanatory_work_prefers_reuse_with_lower_cost(self) -> None:
        expensive = explanatory_work(
            eliminated_residual_bits=10_000,
            stored_program_bytes=2_000,
            active_execution_cost=1_000,
        )
        reusable = explanatory_work(
            eliminated_residual_bits=10_000,
            stored_program_bytes=250,
            active_execution_cost=250,
        )
        self.assertGreater(reusable, expensive)

    def test_no_change_is_not_an_event(self) -> None:
        bank = EventProgramBank()
        with self.assertRaises(ValueError):
            bank.observe_transition({"a": {"x": 1}}, {"a": {"x": 1}})


if __name__ == "__main__":
    unittest.main()
