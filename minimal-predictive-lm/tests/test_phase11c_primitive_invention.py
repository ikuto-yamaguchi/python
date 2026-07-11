from __future__ import annotations

import unittest

from minimal_predictive_lm.phase11c_experiment import run
from minimal_predictive_lm.primitive_invention import (
    AffineCharacterPrimitive,
    StringTransformExample,
    decide_primitive_adoption,
    evaluate_primitive_proposals,
    primitive_accuracy,
    select_reusable_primitive,
)
from minimal_predictive_lm.universal_program_induction import (
    TransitionTrace,
    UnexpressibleTaskError,
    induce_program,
)


class PrimitiveInventionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.training = (
            StringTransformExample(
                "labels",
                "sphinx of black quartz judge my vow",
                "SPHINX OF BLACK QUARTZ JUDGE MY VOW",
            ),
            StringTransformExample(
                "commands",
                "pack my box with five dozen liquor jugs",
                "PACK MY BOX WITH FIVE DOZEN LIQUOR JUGS",
            ),
        )
        self.validation = (
            StringTransformExample("labels", "phase eleven 17", "PHASE ELEVEN 17"),
            StringTransformExample("commands", "run test now", "RUN TEST NOW"),
            StringTransformExample("dialogue", "open file-z", "OPEN FILE-Z"),
        )

    def test_fixed_grammar_cannot_express_transform(self) -> None:
        traces = tuple(
            TransitionTrace.build((row.source,), {}, {}, row.target)
            for row in self.training
        )
        with self.assertRaises(UnexpressibleTaskError):
            induce_program(traces, max_depth=2, max_candidates=10_000)

    def test_training_lookup_is_rejected_by_cross_family_validation(self) -> None:
        rows = evaluate_primitive_proposals(self.training, self.validation)
        lookup = next(row for row in rows if row.primitive.kind == "lookup")
        self.assertEqual(lookup.training_accuracy, 1.0)
        self.assertLess(lookup.validation_accuracy, 1.0)

    def test_selects_compact_affine_primitive(self) -> None:
        selected = select_reusable_primitive(
            self.training,
            self.validation,
            minimum_validation_families=3,
        )
        self.assertIsInstance(selected.primitive, AffineCharacterPrimitive)
        self.assertEqual(selected.primitive.lower_codepoint, ord("a"))
        self.assertEqual(selected.primitive.upper_codepoint, ord("z"))
        self.assertEqual(selected.primitive.offset, -32)
        self.assertEqual(selected.validation_accuracy, 1.0)

    def test_primitive_transfers_to_unseen_application_domain(self) -> None:
        selected = select_reusable_primitive(
            self.training,
            self.validation,
            minimum_validation_families=3,
        )
        novel = (
            StringTransformExample("repository", "feature branch", "FEATURE BRANCH"),
            StringTransformExample("sensor", "motor line-3", "MOTOR LINE-3"),
        )
        self.assertEqual(primitive_accuracy(selected.primitive, novel), 1.0)

    def test_unicode_shift_remains_a_reported_failure(self) -> None:
        selected = select_reusable_primitive(
            self.training,
            self.validation,
            minimum_validation_families=3,
        )
        shifted = (
            StringTransformExample("unicode", "café", "CAFÉ"),
            StringTransformExample("unicode", "straße", "STRASSE"),
        )
        self.assertEqual(primitive_accuracy(selected.primitive, shifted), 0.0)

    def test_lifetime_objective_rejects_one_off_cache(self) -> None:
        selected = select_reusable_primitive(
            self.training,
            self.validation,
            minimum_validation_families=3,
        )
        once = decide_primitive_adoption(
            selected,
            self.validation,
            expected_future_calls=1,
            baseline_error_rate=1.0,
        )
        repeated = decide_primitive_adoption(
            selected,
            self.validation,
            expected_future_calls=100,
            baseline_error_rate=1.0,
        )
        self.assertFalse(once.adopted)
        self.assertTrue(repeated.adopted)

    def test_phase11c_reports_success_without_open_ended_claim(self) -> None:
        payload = run()
        self.assertTrue(payload["verdict"]["phase11c_success"])
        self.assertFalse(payload["verdict"]["representation_invention_is_open_ended"])
        self.assertFalse(payload["verdict"]["stage_c_score_changed"])


if __name__ == "__main__":
    unittest.main()
