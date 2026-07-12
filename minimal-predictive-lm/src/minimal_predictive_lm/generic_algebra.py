from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import itertools
import json
import re
import unicodedata
from typing import Iterable, Mapping, Protocol, Sequence

from .universal_program_induction import (
    InducedProgram,
    TransitionTrace,
    induce_program,
)


Scalar = int | Fraction | bool | str
_TOKEN_RE = re.compile(r"True|False|not|and|or|\d+|[()+\-*/]", re.IGNORECASE)
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_&'./-]*")


def _bits(payload: object) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ) * 8


def _freeze(value: Scalar) -> object:
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, (int, Fraction)):
        number = Fraction(value)
        return ("fraction", number.numerator, number.denominator)
    return ("str", value)


def _same(left: Scalar, right: Scalar) -> bool:
    return _freeze(left) == _freeze(right)


@dataclass(frozen=True)
class OperatorObservation:
    token: str
    arguments: tuple[Scalar, ...]
    result: Scalar


@dataclass(frozen=True)
class ExpressionExample:
    text: str
    result: Scalar


class OperatorProgram(Protocol):
    arity: int

    def apply(self, arguments: Sequence[Scalar]) -> Scalar:
        ...

    def render(self) -> object:
        ...

    @property
    def description_bits(self) -> int:
        ...


@dataclass(frozen=True)
class InducedOperatorProgram:
    arity: int
    program: InducedProgram

    def apply(self, arguments: Sequence[Scalar]) -> Scalar:
        if len(arguments) != self.arity:
            raise ValueError("operator arity mismatch")
        _, output = self.program.execute(arguments, {})
        return output

    def render(self) -> object:
        return {
            "kind": "induced_program",
            "arity": self.arity,
            "output": self.program.output.render(),
        }

    @property
    def description_bits(self) -> int:
        return _bits(self.render())


@dataclass(frozen=True)
class TruthTableOperatorProgram:
    arity: int
    rows: tuple[tuple[tuple[bool, ...], bool], ...]

    def apply(self, arguments: Sequence[Scalar]) -> Scalar:
        if len(arguments) != self.arity or not all(
            isinstance(value, bool) for value in arguments
        ):
            raise ValueError("truth-table operator requires boolean arguments")
        table = dict(self.rows)
        key = tuple(bool(value) for value in arguments)
        if key not in table:
            raise ValueError("truth-table row is missing")
        return table[key]

    def render(self) -> object:
        return {
            "kind": "truth_table",
            "arity": self.arity,
            "rows": [[list(arguments), result] for arguments, result in self.rows],
        }

    @property
    def description_bits(self) -> int:
        return _bits(self.render())


@dataclass(frozen=True)
class OperatorSpec:
    token: str
    program: OperatorProgram

    @property
    def arity(self) -> int:
        return self.program.arity

    def render(self) -> object:
        return {"token": self.token, "program": self.program.render()}


@dataclass(frozen=True)
class ExpressionAlgebra:
    operators: tuple[OperatorSpec, ...]
    precedence: tuple[tuple[str, int], ...]
    precedence_candidates_evaluated: int

    def operator_map(self) -> dict[str, OperatorSpec]:
        return {spec.token: spec for spec in self.operators}

    def precedence_map(self) -> dict[str, int]:
        return dict(self.precedence)

    def evaluate(self, text: str) -> Scalar | None:
        return _evaluate_expression(text, self.operator_map(), self.precedence_map())

    def render(self) -> object:
        return {
            "operators": [spec.render() for spec in self.operators],
            "precedence": [list(row) for row in self.precedence],
        }

    @property
    def description_bits(self) -> int:
        return _bits(self.render())


@dataclass(frozen=True)
class OrderingExample:
    prompt: str
    output: str


@dataclass(frozen=True)
class SequenceOrderingProgram:
    mode: str
    cues: tuple[str, ...]

    def apply(self, prompt: str) -> str | None:
        words = {word.casefold() for word in _WORD_RE.findall(prompt)}
        if not words.intersection(self.cues):
            return None
        items = extract_sequence(prompt)
        if len(items) < 2:
            return None
        if self.mode == "lexicographic_ascending":
            ordered = sorted(items, key=lambda item: item.casefold())
        elif self.mode == "lexicographic_descending":
            ordered = sorted(items, key=lambda item: item.casefold(), reverse=True)
        elif self.mode == "length_ascending":
            ordered = sorted(items, key=lambda item: (len(item), item.casefold()))
        elif self.mode == "length_descending":
            ordered = sorted(items, key=lambda item: (-len(item), item.casefold()))
        else:
            raise ValueError(f"unknown ordering mode: {self.mode}")
        return " ".join(ordered)

    def render(self) -> object:
        return {"mode": self.mode, "cues": list(self.cues)}

    @property
    def description_bits(self) -> int:
        return _bits(self.render())


@dataclass(frozen=True)
class AlgebraPrediction:
    output: Scalar | None
    family: str | None
    operations: int


@dataclass(frozen=True)
class GenericAlgebraModel:
    expression: ExpressionAlgebra
    ordering: SequenceOrderingProgram
    calibration_examples: int
    domain_specific_handlers: int = 0

    def predict(self, prompt: str) -> AlgebraPrediction:
        expression_output = self.expression.evaluate(prompt)
        if expression_output is not None:
            return AlgebraPrediction(expression_output, "expression", len(prompt))
        ordering_output = self.ordering.apply(prompt)
        if ordering_output is not None:
            return AlgebraPrediction(ordering_output, "sequence_ordering", len(prompt))
        return AlgebraPrediction(None, None, 1)

    def render(self) -> object:
        return {
            "expression": self.expression.render(),
            "ordering": self.ordering.render(),
            "calibration_examples": self.calibration_examples,
            "domain_specific_handlers": self.domain_specific_handlers,
        }

    @property
    def description_bits(self) -> int:
        return _bits(self.render())


def _induce_operator_program(rows: Sequence[OperatorObservation]) -> OperatorProgram:
    if not rows:
        raise ValueError("operator requires observations")
    arity = len(rows[0].arguments)
    if any(len(row.arguments) != arity for row in rows):
        raise ValueError("operator arity is not stable")
    if all(
        all(isinstance(value, bool) for value in row.arguments)
        and isinstance(row.result, bool)
        for row in rows
    ):
        table: dict[tuple[bool, ...], bool] = {}
        for row in rows:
            key = tuple(bool(value) for value in row.arguments)
            result = bool(row.result)
            incumbent = table.get(key)
            if incumbent is not None and incumbent != result:
                raise ValueError("inconsistent truth-table observation")
            table[key] = result
        return TruthTableOperatorProgram(arity, tuple(sorted(table.items())))
    traces = tuple(
        TransitionTrace.build(row.arguments, {}, {}, row.result) for row in rows
    )
    result = induce_program(traces, max_depth=3, max_candidates=50_000)
    return InducedOperatorProgram(arity, result.program)


def induce_operator_specs(
    observations: Iterable[OperatorObservation],
) -> tuple[OperatorSpec, ...]:
    grouped: dict[str, list[OperatorObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.token.casefold(), []).append(observation)
    return tuple(
        OperatorSpec(token, _induce_operator_program(tuple(rows)))
        for token, rows in sorted(grouped.items())
    )


def _strip_expression_wrapper(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).strip()
    if normalized.endswith("="):
        normalized = normalized[:-1].strip()
    if normalized.casefold().endswith(" is"):
        normalized = normalized[:-3].strip()
    return normalized


def _tokenize_expression(text: str, operator_tokens: set[str]) -> tuple[object, ...] | None:
    expression = _strip_expression_wrapper(text)
    matches = list(_TOKEN_RE.finditer(expression))
    if not matches:
        return None
    cursor = 0
    tokens: list[object] = []
    previous_kind = "start"
    for match in matches:
        if expression[cursor : match.start()].strip():
            return None
        raw = match.group(0)
        lowered = raw.casefold()
        cursor = match.end()
        if lowered == "true":
            tokens.append(True)
            previous_kind = "value"
        elif lowered == "false":
            tokens.append(False)
            previous_kind = "value"
        elif raw.isdigit():
            tokens.append(int(raw))
            previous_kind = "value"
        elif raw == "(":
            tokens.append(raw)
            previous_kind = "left_paren"
        elif raw == ")":
            tokens.append(raw)
            previous_kind = "value"
        else:
            token = lowered
            if token == "-" and previous_kind in {"start", "operator", "left_paren"}:
                token = "neg"
            if token not in operator_tokens:
                return None
            tokens.append(token)
            previous_kind = "operator"
    if expression[cursor:].strip():
        return None
    return tuple(tokens)


def _evaluate_expression(
    text: str,
    operators: Mapping[str, OperatorSpec],
    precedence: Mapping[str, int],
) -> Scalar | None:
    tokens = _tokenize_expression(text, set(operators))
    if tokens is None:
        return None
    output: list[object] = []
    stack: list[str] = []
    try:
        for token in tokens:
            if isinstance(token, (int, bool)):
                output.append(token)
                continue
            if token == "(":
                stack.append(token)
                continue
            if token == ")":
                while stack and stack[-1] != "(":
                    output.append(stack.pop())
                if not stack:
                    return None
                stack.pop()
                continue
            spec = operators[str(token)]
            current_precedence = precedence[str(token)]
            right_associative = spec.arity == 1
            while stack and stack[-1] != "(":
                top = stack[-1]
                top_precedence = precedence[top]
                should_pop = (
                    top_precedence > current_precedence
                    if right_associative
                    else top_precedence >= current_precedence
                )
                if not should_pop:
                    break
                output.append(stack.pop())
            stack.append(str(token))
        while stack:
            token = stack.pop()
            if token == "(":
                return None
            output.append(token)

        values: list[Scalar] = []
        for token in output:
            if isinstance(token, (int, bool)):
                values.append(token)
                continue
            spec = operators[str(token)]
            if len(values) < spec.arity:
                return None
            arguments = values[-spec.arity :]
            del values[-spec.arity :]
            values.append(spec.program.apply(arguments))
        return values[0] if len(values) == 1 else None
    except (KeyError, TypeError, ValueError, ZeroDivisionError, IndexError):
        return None


def induce_expression_algebra(
    observations: Iterable[OperatorObservation],
    expression_examples: Iterable[ExpressionExample],
    *,
    maximum_precedence_levels: int = 3,
) -> ExpressionAlgebra:
    specs = induce_operator_specs(observations)
    examples = tuple(expression_examples)
    if not examples:
        raise ValueError("precedence induction requires expression examples")
    tokens = tuple(spec.token for spec in specs)
    operator_map = {spec.token: spec for spec in specs}
    candidates = 0
    valid: list[tuple[tuple[int, ...], tuple[tuple[str, int], ...]]] = []
    for ranks in itertools.product(
        range(1, maximum_precedence_levels + 1), repeat=len(tokens)
    ):
        if min(ranks) != 1:
            continue
        used = sorted(set(ranks))
        if used != list(range(1, max(used) + 1)):
            continue
        candidates += 1
        mapping = dict(zip(tokens, ranks))
        if all(
            (output := _evaluate_expression(example.text, operator_map, mapping))
            is not None
            and _same(output, example.result)
            for example in examples
        ):
            valid.append((ranks, tuple(zip(tokens, ranks))))
    if not valid:
        raise ValueError("no precedence assignment explains calibration expressions")
    _, selected = min(
        valid,
        key=lambda row: (
            len(set(row[0])),
            max(row[0]),
            sum(row[0]),
            row[0],
        ),
    )
    return ExpressionAlgebra(specs, selected, candidates)


def extract_sequence(prompt: str) -> tuple[str, ...]:
    if ":" not in prompt:
        return ()
    segment = prompt.rsplit(":", 1)[1].strip()
    return tuple(part for part in segment.split() if part)


def _apply_ordering(mode: str, items: Sequence[str]) -> tuple[str, ...]:
    if mode == "lexicographic_ascending":
        return tuple(sorted(items, key=lambda item: item.casefold()))
    if mode == "lexicographic_descending":
        return tuple(sorted(items, key=lambda item: item.casefold(), reverse=True))
    if mode == "length_ascending":
        return tuple(sorted(items, key=lambda item: (len(item), item.casefold())))
    if mode == "length_descending":
        return tuple(sorted(items, key=lambda item: (-len(item), item.casefold())))
    raise ValueError(mode)


def induce_sequence_ordering(
    examples: Iterable[OrderingExample],
) -> SequenceOrderingProgram:
    rows = tuple(examples)
    if len(rows) < 2:
        raise ValueError("ordering induction requires at least two examples")
    candidates = (
        "lexicographic_ascending",
        "lexicographic_descending",
        "length_ascending",
        "length_descending",
    )
    valid: list[str] = []
    for mode in candidates:
        if all(
            " ".join(_apply_ordering(mode, extract_sequence(row.prompt))) == row.output
            for row in rows
        ):
            valid.append(mode)
    if not valid:
        raise ValueError("no ordering program explains examples")
    mode = min(valid, key=lambda value: (_bits(value), value))
    cue_counts: dict[str, int] = {}
    for row in rows:
        prefix = row.prompt.rsplit(":", 1)[0]
        for word in {word.casefold() for word in _WORD_RE.findall(prefix)}:
            cue_counts[word] = cue_counts.get(word, 0) + 1
    cues = tuple(sorted(word for word, count in cue_counts.items() if count >= 2))
    if not cues:
        raise ValueError("ordering operation has no reusable lexical cue")
    return SequenceOrderingProgram(mode, cues)


def induce_generic_algebra_model(
    operator_observations: Iterable[OperatorObservation],
    expression_examples: Iterable[ExpressionExample],
    ordering_examples: Iterable[OrderingExample],
) -> GenericAlgebraModel:
    operator_rows = tuple(operator_observations)
    expression_rows = tuple(expression_examples)
    ordering_rows = tuple(ordering_examples)
    return GenericAlgebraModel(
        induce_expression_algebra(operator_rows, expression_rows),
        induce_sequence_ordering(ordering_rows),
        len(operator_rows) + len(expression_rows) + len(ordering_rows),
    )
