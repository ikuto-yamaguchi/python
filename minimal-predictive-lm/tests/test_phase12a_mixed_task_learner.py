from __future__ import annotations

from fractions import Fraction
import unittest

from minimal_predictive_lm.benchmark_harness import answer_is_correct
from minimal_predictive_lm.mixed_task_learner import (
    induce_mixed_task_model,
    mixed_model_accuracy,
    parse_prompt,
)
from minimal_predictive_lm.phase12a_experiment import (
    build_synthetic_manifest,
    calibration_interactions,
    synthetic_examples,
)


def _format(value: object | None) -> str:
    if value is None:
        return "__ABSTAIN__"
    if isinstance(value, Fraction):
        return (
            str(value.numerator)
            if value.denominator == 1
            else f"{value.numerator}/{value.denominator}"
        )
    return str(value)


class MixedTaskLearnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.calibration = calibration_interactions()
        cls.model = induce_mixed_task_model(cls.calibration)

    def test_generic_parser_extracts_state_arguments_and_features(self) -> None:
        parsed = parse_prompt("choose state_count=7 delta=5 mode=ready")
        self.assertEqual(parsed.before_dict(), {"count": 7})
        self.assertEqual(parsed.arguments, (5, "ready"))
        self.assertIn("word:choose", parsed.features)

    def test_one_learner_reproduces_all_calibration_interactions(self) -> None:
        self.assertEqual(mixed_model_accuracy(self.model, self.calibration), 1.0)
        self.assertEqual(self.model.domain_specific_handlers, 0)
        self.assertGreaterEqual(len(self.model.rules), 8)

    def test_same_input_signatures_are_separated_by_learned_features(self) -> None:
        self.assertEqual(
            self.model.predict("join left=causal right=graph").output,
            "causalgraph",
        )
        self.assertEqual(
            self.model.predict("claim value=green source=manual22").output,
            "manual22",
        )
        self.assertEqual(
            self.model.predict("choose status=ready yes=GO no=WAIT").output,
            "GO",
        )
        self.assertEqual(
            self.model.predict("event before=theta after=THETA result=PASS").output,
            "theta",
        )

    def test_state_transition_is_executed_not_only_answered(self) -> None:
        prediction = self.model.predict("state_count=40 delta=12")
        self.assertEqual(prediction.output, Fraction(52, 1))
        self.assertEqual(dict(prediction.after), {"count": Fraction(52, 1)})

    def test_invented_string_primitives_transfer_to_unseen_values(self) -> None:
        self.assertEqual(
            self.model.predict("convert forward value=repository").output,
            "sfqptjupsz",
        )
        self.assertEqual(
            self.model.predict("convert backward value=sfqptjupsz").output,
            "repository",
        )

    def test_all_synthetic_heldout_axes_are_correct(self) -> None:
        examples = synthetic_examples()
        correct = 0
        axes = set()
        for example in examples:
            axes.add(example.axis)
            prediction = self.model.predict(example.prompt)
            correct += int(answer_is_correct(example, _format(prediction.output)))
        self.assertEqual(correct, len(examples))
        self.assertGreaterEqual(len(axes), 6)

    def test_synthetic_manifest_cannot_authorize_public_parity(self) -> None:
        manifest = build_synthetic_manifest()
        self.assertFalse(manifest.public)
        self.assertGreater(len(manifest.examples), 20)


if __name__ == "__main__":
    unittest.main()
