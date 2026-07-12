from __future__ import annotations

import unittest

from minimal_predictive_lm.generic_state_machine import (
    GenericStateMachine,
    compile_mapping_program,
    compile_navigation_program,
    compile_order_program,
    compile_stack_program,
)
from minimal_predictive_lm.phase15c_experiment import cross_domain_state_examples


class Phase15cGenericStateMachineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.machine = GenericStateMachine()
        cls.examples = {row.example_id: row for row in cross_domain_state_examples()}

    def test_stack_compiler_and_runtime(self) -> None:
        row = self.examples["state_stack_1"]
        program = compile_stack_program(row.prompt)
        self.assertIsNotNone(program)
        prediction = self.machine.predict(row.prompt)
        self.assertEqual(prediction.output, row.target)
        self.assertEqual(prediction.family, "stack")

    def test_absolute_and_relative_navigation_share_vector_state(self) -> None:
        for key in ("state_vector_absolute", "state_vector_relative"):
            row = self.examples[key]
            self.assertIsNotNone(compile_navigation_program(row.prompt))
            prediction = self.machine.predict(row.prompt)
            self.assertEqual(prediction.output, row.target)
            self.assertEqual(prediction.family, "vector")

    def test_mapping_compiler_tracks_dynamic_names_and_values(self) -> None:
        for key in ("state_mapping_api", "state_mapping_services"):
            row = self.examples[key]
            program = compile_mapping_program(row.prompt)
            self.assertIsNotNone(program)
            prediction = self.machine.predict(row.prompt)
            self.assertEqual(prediction.output, row.target)
            self.assertEqual(prediction.family, "mapping")

    def test_order_compiler_resolves_relation_closure(self) -> None:
        for key in ("state_order_queue", "state_order_versions"):
            row = self.examples[key]
            program = compile_order_program(row.prompt)
            self.assertIsNotNone(program)
            prediction = self.machine.predict(row.prompt)
            self.assertEqual(prediction.output, row.target)
            self.assertEqual(prediction.family, "order")

    def test_all_cross_domain_examples_pass_one_runtime(self) -> None:
        for row in self.examples.values():
            with self.subTest(row=row.example_id):
                self.assertEqual(self.machine.predict(row.prompt).output, row.target)

    def test_date_language_remains_unsupported(self) -> None:
        prompt = (
            "Today is 01/02/2020. What is the date tomorrow in MM/DD/YYYY?\n"
            "Options:\n(A) 01/03/2020\n(B) 02/01/2020\n(C) 01/01/2020"
        )
        self.assertIsNone(self.machine.predict(prompt).output)

    def test_compilers_do_not_use_benchmark_task_names(self) -> None:
        self.assertEqual(self.machine.benchmark_task_name_branches, 0)
        self.assertEqual(self.machine.compiler_count, 4)
        self.assertGreater(self.machine.description_bits, 0)


if __name__ == "__main__":
    unittest.main()
