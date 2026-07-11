from __future__ import annotations

import unittest

from minimal_predictive_lm.phase11a_experiment import run
from minimal_predictive_lm.universal_program_induction import (
    TransitionTrace,
    UnexpressibleTaskError,
    induce_program,
    program_accuracy,
)


class UniversalProgramInductionTests(unittest.TestCase):
    def test_induces_arithmetic_without_operation_label(self) -> None:
        training = tuple(
            TransitionTrace.build((left, right), {}, {}, left + right)
            for left, right in ((2, 7), (5, 11), (13, 4), (21, 9))
        )
        heldout = tuple(
            TransitionTrace.build((left, right), {}, {}, left + right)
            for left, right in ((55, 23), (89, 7), (144, 32))
        )
        result = induce_program(training)
        self.assertEqual(result.program.output.op, "ADD")
        self.assertEqual(program_accuracy(result.program, heldout), 1.0)

    def test_composes_state_read_and_arithmetic(self) -> None:
        training = tuple(
            TransitionTrace.build(
                (delta,),
                {"count": current},
                {"count": current + delta},
                current + delta,
            )
            for current, delta in ((2, 5), (7, 3), (11, 8), (20, 4))
        )
        heldout = tuple(
            TransitionTrace.build(
                (delta,),
                {"count": current},
                {"count": current + delta},
                current + delta,
            )
            for current, delta in ((50, 13), (100, 25))
        )
        result = induce_program(training)
        self.assertIn("STATE", result.program.operations())
        self.assertIn("ADD", result.program.operations())
        self.assertEqual(program_accuracy(result.program, heldout), 1.0)

    def test_infers_state_key_affix_without_domain_handler(self) -> None:
        rows = (
            ("box", "warehouse", "laboratory"),
            ("sample", "desk", "inspection"),
            ("tool", "shelf-a", "shelf-b"),
            ("sensor", "line-1", "line-2"),
        )
        training = tuple(
            TransitionTrace.build(
                (subject, destination),
                {f"location:{subject}": origin},
                {f"location:{subject}": destination},
                destination,
            )
            for subject, origin, destination in rows
        )
        result = induce_program(training)
        self.assertIn("CONCAT", result.program.operations())
        after, output = result.program.execute(
            ("motor", "repair"),
            {"location:motor": "storage"},
        )
        self.assertEqual(after, {"location:motor": "repair"})
        self.assertEqual(output, "repair")

    def test_induces_conditional_from_outcomes(self) -> None:
        training = tuple(
            TransitionTrace.build(
                (status,),
                {},
                {},
                "ROLLBACK" if status == "FAIL" else "REPORT",
            )
            for status in ("FAIL", "PASS", "FAIL", "PASS")
        )
        result = induce_program(training)
        self.assertEqual(result.program.output.op, "IF_EQ")
        self.assertEqual(program_accuracy(result.program, training), 1.0)

    def test_composes_multistep_revenue_program(self) -> None:
        training_values = (
            (16, 3, 4, 2),
            (30, 5, 7, 3),
            (25, 2, 8, 4),
            (40, 10, 5, 6),
            (18, 1, 2, 5),
            (50, 12, 8, 3),
        )
        training = tuple(
            TransitionTrace.build(values, {}, {}, (values[0] - values[1] - values[2]) * values[3])
            for values in training_values
        )
        result = induce_program(training, max_depth=3, max_candidates=250_000)
        self.assertIn("SUB", result.program.operations())
        self.assertIn("MUL", result.program.operations())
        heldout = (
            TransitionTrace.build((60, 15, 10, 2), {}, {}, 70),
            TransitionTrace.build((22, 4, 3, 7), {}, {}, 105),
        )
        self.assertEqual(program_accuracy(result.program, heldout), 1.0)

    def test_missing_primitive_is_reported_not_hidden(self) -> None:
        traces = tuple(
            TransitionTrace.build((raw,), {}, {}, raw.upper())
            for raw in ("red", "blue", "green", "quiet", "robot", "field")
        )
        with self.assertRaises(UnexpressibleTaskError):
            induce_program(traces, max_depth=3, max_candidates=100_000)

    def test_phase11a_requires_no_domain_handlers(self) -> None:
        payload = run()
        self.assertEqual(payload["architecture"]["domain_specific_handlers"], 0)
        self.assertEqual(
            payload["architecture"]["human_engine_code_changes_for_novel_tasks"],
            0,
        )
        self.assertTrue(payload["aggregate"]["all_heldout_accuracy"])
        self.assertTrue(payload["representation_boundary"]["unexpressible_detected"])
        self.assertTrue(payload["scalability_verdict"]["phase11a_success"])


if __name__ == "__main__":
    unittest.main()
