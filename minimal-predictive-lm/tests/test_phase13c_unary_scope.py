from __future__ import annotations

import unittest

from minimal_predictive_lm.phase13c_experiment import build_scope_corrected_algebra_model


class Phase13cUnaryScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model = build_scope_corrected_algebra_model()

    def test_unary_scope_binds_inside_multiplication(self) -> None:
        self.assertEqual(self.model.predict("2 * -3 =").output, -6)
        self.assertEqual(self.model.predict("-2 * -3 =").output, 6)
        self.assertEqual(self.model.predict("8 - 3 * -2 =").output, 14)

    def test_nested_negative_expression(self) -> None:
        self.assertEqual(
            self.model.predict("((-1 + 2 + 9 * 5) - (-2 + -4 + -4 * -7)) =").output,
            24,
        )
        self.assertEqual(
            self.model.predict("((-9 * -5 - 6 + -2) - (-8 - -6 * -3 * 1)) =").output,
            63,
        )

    def test_scope_is_induced_as_higher_than_multiplication(self) -> None:
        precedence = self.model.expression.precedence_map()
        self.assertGreater(precedence["neg"], precedence["*"])
        self.assertEqual(self.model.domain_specific_handlers, 0)


if __name__ == "__main__":
    unittest.main()
