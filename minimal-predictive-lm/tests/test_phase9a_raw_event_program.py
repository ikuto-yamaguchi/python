from __future__ import annotations

import unittest

from minimal_predictive_lm.phase9a_experiment import (
    NEAR_HELDOUT_SPECIFICATION,
    TRAINING_SPECIFICATION,
    _trace,
    _traces,
    run,
)
from minimal_predictive_lm.raw_event_program import (
    EffectTrace,
    execute_transform_workflow,
    exact_surface_accuracy,
    grounding_accuracy,
    induce_raw_grounder,
    infer_operation,
)


class Phase9aRawEventProgramTests(unittest.TestCase):
    def test_effect_trace_induces_four_operations(self) -> None:
        self.assertEqual(
            infer_operation(_trace("text", "write", "SET")),
            "SET",
        )
        self.assertEqual(
            infer_operation(_trace("tool", "observe", "VERIFY")),
            "VERIFY",
        )
        self.assertEqual(
            infer_operation(_trace("tool", "restore", "RETRACT")),
            "RETRACT",
        )
        self.assertEqual(
            infer_operation(_trace("text", "report", "EMIT")),
            "EMIT",
        )

    def test_empty_effect_is_rejected(self) -> None:
        state = (("value", "same"),)
        with self.assertRaises(ValueError):
            infer_operation(EffectTrace("text", "nothing", state, state))

    def test_raw_grounder_covers_training_and_near_heldout(self) -> None:
        training = _traces(TRAINING_SPECIFICATION)
        heldout = _traces(NEAR_HELDOUT_SPECIFICATION)
        grounder = induce_raw_grounder(training)
        self.assertEqual(grounding_accuracy(grounder, training), 1.0)
        self.assertEqual(exact_surface_accuracy(training, heldout), 0.0)
        self.assertEqual(grounding_accuracy(grounder, heldout), 1.0)

    def test_shared_model_is_smaller_and_more_accurate(self) -> None:
        payload = run()
        comparison = payload["shared_vs_separated"]
        self.assertLess(
            comparison["shared_description_bits"],
            comparison["separated_description_bits"],
        )
        self.assertEqual(comparison["shared_near_accuracy"], 1.0)
        self.assertLess(
            comparison["separated_near_accuracy"],
            comparison["shared_near_accuracy"],
        )

    def test_distant_lexical_shift_remains_a_failure(self) -> None:
        payload = run()
        self.assertLess(
            payload["raw_grounding"]["distant_lexical_shift_accuracy"],
            0.25,
        )

    def test_residual_calibration_improves_followup(self) -> None:
        calibration = run()["residual_calibration"]
        self.assertEqual(calibration["accuracy_before"], 0.0)
        self.assertGreaterEqual(calibration["accuracy_after"], 0.875)
        self.assertGreater(calibration["added_description_bits"], 0)

    def test_end_to_end_workflow_rolls_back_and_recovers(self) -> None:
        training = _traces(TRAINING_SPECIFICATION)
        grounder = induce_raw_grounder(training)
        request = (
            "transform関数を修正して。"
            "テストを実行して。"
            "失敗した場合は変更を元に戻して。"
            "別の修正を追加して。"
            "もう一度テストを実行して。"
            "最後に結果を報告して。"
        )
        result = execute_transform_workflow(request, grounder)
        self.assertEqual(
            result.plan,
            ("SET", "VERIFY", "RETRACT", "SET", "VERIFY", "EMIT"),
        )
        self.assertEqual(result.request_grounding_correct, 6)
        # Five single-effect artifacts are recovered. The final report contains
        # both an EMIT speech act and VERIFY content ("全テスト"), so the
        # current single-label grounder correctly exposes an unresolved tie.
        self.assertEqual(result.artifact_grounding_correct, 5)
        self.assertIsNone(result.events[-1].artifact_operation)
        self.assertEqual(result.final_state.expression, "x * x + 1")
        self.assertEqual(result.final_state.last_test, "PASS")
        self.assertIn("全テストに成功", result.final_state.report)
        self.assertEqual(result.conversion_boundaries_separate, 12)
        self.assertGreater(result.serialized_copy_bits_separate, 0)


if __name__ == "__main__":
    unittest.main()
