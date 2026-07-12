from __future__ import annotations

from fractions import Fraction
import unittest

from minimal_predictive_lm.phase13b_experiment import build_algebra_model


class Phase13bGenericAlgebraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model = build_algebra_model()

    def test_one_expression_algebra_handles_numeric_and_boolean_domains(self) -> None:
        self.assertEqual(self.model.predict("( 4 + 3 ) * 2 =").output, 14)
        self.assertEqual(self.model.predict("-5 + 2 * 4 =").output, 3)
        self.assertIs(self.model.predict("not False or False is").output, True)
        self.assertIs(
            self.model.predict("True and ( False or True ) is").output,
            True,
        )

    def test_division_preserves_exact_fraction(self) -> None:
        self.assertEqual(self.model.predict("3 / 2 =").output, Fraction(3, 2))

    def test_one_ordering_program_transfers_to_identifiers_and_paths(self) -> None:
        self.assertEqual(
            self.model.predict(
                "Sort these API symbols alphabetically: render apply emit"
            ).output,
            "apply emit render",
        )
        self.assertEqual(
            self.model.predict(
                "Sort these filesystem paths alphabetically: /z /a /m"
            ).output,
            "/a /m /z",
        )

    def test_unrepresented_object_counting_abstains(self) -> None:
        self.assertIsNone(
            self.model.predict(
                "I have two apples and a pear. How many fruits do I have?"
            ).output
        )

    def test_model_contains_no_domain_specific_handlers(self) -> None:
        self.assertEqual(self.model.domain_specific_handlers, 0)
        self.assertGreater(self.model.description_bits, 0)
        self.assertGreater(self.model.expression.precedence_candidates_evaluated, 0)


if __name__ == "__main__":
    unittest.main()
