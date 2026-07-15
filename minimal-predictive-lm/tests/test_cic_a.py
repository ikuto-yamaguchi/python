from fractions import Fraction
from minimal_predictive_lm.cic_expr import parse_expression


def test_cic_expression() -> None:
    expression = parse_expression("(* (- n0 n1) n2)")
    assert expression.evaluate((Fraction(16), Fraction(7), Fraction(2))) == 18
    assert parse_expression(expression.key).key == expression.key
