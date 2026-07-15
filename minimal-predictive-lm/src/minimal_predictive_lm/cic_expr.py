from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

NUMBER_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def extract_numbers(text: str) -> tuple[Fraction, ...]:
    return tuple(Fraction(token.replace(",", "")) for token in NUMBER_RE.findall(text))


@dataclass(frozen=True)
class Expression:
    op: str
    left: "Expression | None" = None
    right: "Expression | None" = None
    index: int | None = None
    constant: Fraction | None = None

    @classmethod
    def number(cls, index: int) -> "Expression":
        return cls("number", index=index)

    @classmethod
    def const(cls, value: int | Fraction) -> "Expression":
        return cls("const", constant=Fraction(value))

    @property
    def key(self) -> str:
        if self.op == "number":
            return f"n{self.index}"
        if self.op == "const":
            return f"c{self.constant}"
        assert self.left is not None and self.right is not None
        return f"({self.op} {self.left.key} {self.right.key})"

    @property
    def cost(self) -> int:
        if self.op == "number":
            return 1
        if self.op == "const":
            return 2
        assert self.left is not None and self.right is not None
        return 1 + self.left.cost + self.right.cost

    def evaluate(self, numbers: Sequence[Fraction]) -> Fraction | None:
        if self.op == "number":
            assert self.index is not None
            return numbers[self.index] if self.index < len(numbers) else None
        if self.op == "const":
            return self.constant
        assert self.left is not None and self.right is not None
        left = self.left.evaluate(numbers)
        right = self.right.evaluate(numbers)
        if left is None or right is None:
            return None
        if self.op == "+":
            return left + right
        if self.op == "-":
            return left - right
        if self.op == "*":
            return left * right
        if self.op == "/":
            return None if right == 0 else left / right
        raise ValueError(f"unknown operation: {self.op}")


def parse_expression(text: str) -> Expression:
    tokens = re.findall(r"\(|\)|[^\s()]+", text)
    position = 0

    def parse() -> Expression:
        nonlocal position
        token = tokens[position]
        position += 1
        if token.startswith("n") and token[1:].isdigit():
            return Expression.number(int(token[1:]))
        if token.startswith("c"):
            return Expression.const(Fraction(token[1:]))
        if token != "(":
            raise ValueError(f"invalid expression token: {token}")
        op = tokens[position]
        position += 1
        left = parse()
        right = parse()
        if tokens[position] != ")":
            raise ValueError("missing closing parenthesis")
        position += 1
        return Expression(op, left, right)

    result = parse()
    if position != len(tokens):
        raise ValueError("trailing expression tokens")
    return result


def _cue_constants(question: str) -> tuple[int, ...]:
    constants: list[int] = []
    if "%" in question or "パーセント" in question:
        constants.append(100)
    if "半分" in question or "半額" in question:
        constants.append(2)
    if "ダース" in question:
        constants.append(12)
    return tuple(constants)


@dataclass(frozen=True)
class SynthesisResult:
    expressions: tuple[Expression, ...]
    expansions: int


def synthesize_expressions(
    question: str,
    answer: int | Fraction,
    *,
    max_terms: int = 4,
    max_values_per_mask: int = 350,
    max_solutions: int = 16,
) -> SynthesisResult:
    numbers = extract_numbers(question)[:7]
    if not numbers:
        return SynthesisResult((), 0)
    atoms: list[tuple[Fraction, Expression]] = [
        (value, Expression.number(index)) for index, value in enumerate(numbers)
    ]
    atoms.extend((Fraction(value), Expression.const(value)) for value in _cue_constants(question))
    atoms = atoms[:9]
    atom_count = len(atoms)
    target = Fraction(answer)
    tables: dict[int, dict[Fraction, Expression]] = {
        1 << index: {value: expression}
        for index, (value, expression) in enumerate(atoms)
    }
    expansions = 0
    for size in range(2, min(max_terms, atom_count) + 1):
        for mask in range(1, 1 << atom_count):
            if mask.bit_count() != size:
                continue
            values: dict[Fraction, Expression] = {}
            submask = (mask - 1) & mask
            while submask:
                other = mask ^ submask
                if other and submask < other and submask in tables and other in tables:
                    for left_value, left_expr in tables[submask].items():
                        for right_value, right_expr in tables[other].items():
                            candidates = [
                                ("+", left_value + right_value, left_expr, right_expr),
                                ("*", left_value * right_value, left_expr, right_expr),
                                ("-", left_value - right_value, left_expr, right_expr),
                                ("-", right_value - left_value, right_expr, left_expr),
                            ]
                            if right_value:
                                candidates.append(("/", left_value / right_value, left_expr, right_expr))
                            if left_value:
                                candidates.append(("/", right_value / left_value, right_expr, left_expr))
                            expansions += len(candidates)
                            for op, value, first, second in candidates:
                                if abs(value) > 10**9 or value.denominator > 1000:
                                    continue
                                if op in {"+", "*"} and first.key > second.key:
                                    first, second = second, first
                                expression = Expression(op, first, second)
                                existing = values.get(value)
                                if existing is None or (expression.cost, expression.key) < (
                                    existing.cost,
                                    existing.key,
                                ):
                                    values[value] = expression
                submask = (submask - 1) & mask
            if len(values) > max_values_per_mask:
                ranked = sorted(
                    values.items(),
                    key=lambda item: (
                        abs(float(item[0] - target)),
                        item[1].cost,
                        item[1].key,
                    ),
                )[:max_values_per_mask]
                values = dict(ranked)
            if values:
                tables[mask] = values
    solutions: dict[str, Expression] = {}
    for values in tables.values():
        expression = values.get(target)
        if expression is not None:
            solutions[expression.key] = expression
    ranked = sorted(solutions.values(), key=lambda row: (row.cost, row.key))[:max_solutions]
    return SynthesisResult(tuple(ranked), expansions)
