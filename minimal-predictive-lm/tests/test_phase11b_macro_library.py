from __future__ import annotations

import unittest

from minimal_predictive_lm.phase11b_experiment import run
from minimal_predictive_lm.universal_macro_library import (
    induce_macro_library,
    synthesize_expression_with_library,
)
from minimal_predictive_lm.universal_program_induction import (
    Expr,
    InducedProgram,
    TransitionTrace,
)


class MacroLibraryTests(unittest.TestCase):
    @staticmethod
    def _remaining_program(a: int, b: int, c: int) -> InducedProgram:
        expression = Expr(
            "SUB",
            None,
            (
                Expr(
                    "SUB",
                    None,
                    (Expr("ARG", a, (), "num"), Expr("ARG", b, (), "num")),
                    "num",
                ),
                Expr("ARG", c, (), "num"),
            ),
            "num",
        )
        return InducedProgram(expression, (), 0, 0)

    def test_alpha_normalizes_repeated_subtrees_across_programs(self) -> None:
        first = self._remaining_program(0, 1, 2)
        second = self._remaining_program(2, 0, 1)
        library = induce_macro_library((first, second))
        self.assertEqual(len(library.macros), 1)
        macro = library.macros[0]
        self.assertEqual(macro.support_programs, 2)
        self.assertEqual(macro.arity, 3)
        self.assertEqual(macro.parameter_types, ("num", "num", "num"))

    def test_single_program_subtree_is_not_retained(self) -> None:
        library = induce_macro_library((self._remaining_program(0, 1, 2),))
        self.assertEqual(library.macros, ())

    def test_macro_solves_depth_three_target_with_depth_one_search(self) -> None:
        library = induce_macro_library(
            (self._remaining_program(0, 1, 2), self._remaining_program(2, 0, 1))
        )
        rows = (
            (16, 3, 4, 2),
            (30, 5, 7, 3),
            (25, 2, 8, 4),
            (40, 10, 5, 6),
        )
        traces = tuple(
            TransitionTrace.build(values, {}, {}, (values[0] - values[1] - values[2]) * values[3])
            for values in rows
        )
        result = synthesize_expression_with_library(
            traces,
            tuple(trace.output for trace in traces),
            library,
            max_depth=1,
            max_candidates=5_000,
        )
        self.assertEqual(result.stats.maximum_depth, 1)
        self.assertGreaterEqual(result.macro_calls, 1)
        probe = TransitionTrace.build((60, 15, 10, 2), {}, {}, 70)
        self.assertEqual(result.expression.evaluate(probe), 70)

    def test_phase11b_records_search_and_representation_boundaries(self) -> None:
        payload = run()
        self.assertTrue(payload["target_task"]["baseline_without_library_failed"])
        self.assertEqual(payload["target_task"]["heldout_accuracy"], 1.0)
        self.assertTrue(payload["adoption"]["adopted"])
        self.assertTrue(payload["scalability_verdict"]["phase11b_success"])


if __name__ == "__main__":
    unittest.main()
