from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
import math
from typing import Iterable, Mapping, Sequence


Scalar = int | Fraction | str | bool


@dataclass(frozen=True)
class TransitionTrace:
    """One domain-neutral transition observation.

    The learner receives only arguments, a sparse before/after state, and an
    observed output.  No domain name, operation label, or handwritten handler is
    supplied to the synthesizer.
    """

    arguments: tuple[Scalar, ...]
    before: tuple[tuple[str, Scalar], ...]
    after: tuple[tuple[str, Scalar], ...]
    output: Scalar

    @classmethod
    def build(
        cls,
        arguments: Sequence[Scalar],
        before: Mapping[str, Scalar],
        after: Mapping[str, Scalar],
        output: Scalar,
    ) -> "TransitionTrace":
        return cls(
            tuple(arguments),
            tuple(sorted(before.items())),
            tuple(sorted(after.items())),
            output,
        )

    def before_dict(self) -> dict[str, Scalar]:
        return dict(self.before)

    def after_dict(self) -> dict[str, Scalar]:
        return dict(self.after)


@dataclass(frozen=True)
class Expr:
    op: str
    value: Scalar | int | str | None = None
    children: tuple["Expr", ...] = ()
    value_type: str = "any"

    @property
    def depth(self) -> int:
        return 0 if not self.children else 1 + max(child.depth for child in self.children)

    @property
    def node_count(self) -> int:
        return 1 + sum(child.node_count for child in self.children)

    def render(self) -> object:
        if self.op in {"ARG", "CONST", "STATE"}:
            return [self.op, _json_scalar(self.value)]
        return [self.op, *(child.render() for child in self.children)]

    @property
    def description_bits(self) -> int:
        return len(
            json.dumps(self.render(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ) * 8

    def evaluate(self, trace: TransitionTrace) -> Scalar:
        if self.op == "ARG":
            return trace.arguments[int(self.value)]
        if self.op == "CONST":
            assert self.value is not None
            return self.value
        if self.op == "STATE":
            return trace.before_dict()[str(self.value)]

        values = tuple(child.evaluate(trace) for child in self.children)
        if self.op == "ADD":
            return _number(values[0]) + _number(values[1])
        if self.op == "SUB":
            return _number(values[0]) - _number(values[1])
        if self.op == "MUL":
            return _number(values[0]) * _number(values[1])
        if self.op == "DIV":
            divisor = _number(values[1])
            if divisor == 0:
                raise ZeroDivisionError
            return _number(values[0]) / divisor
        if self.op == "CONCAT":
            return str(values[0]) + str(values[1])
        if self.op == "IF_EQ":
            return values[2] if values[0] == values[1] else values[3]
        raise ValueError(f"unknown expression operation: {self.op}")


@dataclass(frozen=True)
class SearchStats:
    candidate_evaluations: int
    unique_signatures: int
    maximum_depth: int


@dataclass(frozen=True)
class ExpressionSearchResult:
    expression: Expr
    stats: SearchStats


@dataclass(frozen=True)
class InducedProgram:
    output: Expr
    updates: tuple[tuple[Expr, Expr], ...]
    candidate_evaluations: int
    unique_signatures: int

    def execute(
        self,
        arguments: Sequence[Scalar],
        before: Mapping[str, Scalar],
    ) -> tuple[dict[str, Scalar], Scalar]:
        probe = TransitionTrace.build(arguments, before, before, 0)
        after = dict(before)
        for key_expr, value_expr in self.updates:
            key = key_expr.evaluate(probe)
            if not isinstance(key, str):
                raise TypeError("state update key must evaluate to a string")
            after[key] = value_expr.evaluate(probe)
        return after, self.output.evaluate(probe)

    @property
    def description_bits(self) -> int:
        payload = {
            "output": self.output.render(),
            "updates": [[key.render(), value.render()] for key, value in self.updates],
        }
        return len(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ) * 8

    def operations(self) -> frozenset[str]:
        found: set[str] = set()

        def visit(expr: Expr) -> None:
            found.add(expr.op)
            for child in expr.children:
                visit(child)

        visit(self.output)
        for key, value in self.updates:
            visit(key)
            visit(value)
        return frozenset(found)


@dataclass(frozen=True)
class ProgramInductionResult:
    program: InducedProgram
    output_search: SearchStats
    update_searches: tuple[tuple[SearchStats, SearchStats], ...]


class UnexpressibleTaskError(RuntimeError):
    pass


def _json_scalar(value: object) -> object:
    if isinstance(value, Fraction):
        return {"fraction": [value.numerator, value.denominator]}
    return value


def _number(value: Scalar) -> Fraction:
    if isinstance(value, bool) or isinstance(value, str):
        raise TypeError(f"not numeric: {value!r}")
    return Fraction(value)


def _type_of(value: Scalar) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, str):
        return "str"
    return "num"


def _consistent_type(values: Iterable[Scalar]) -> str | None:
    observed = {_type_of(value) for value in values}
    return next(iter(observed)) if len(observed) == 1 else None


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return ("fraction", value.numerator, value.denominator)
    return value


def _repeated_constants(traces: Sequence[TransitionTrace]) -> tuple[Scalar, ...]:
    counts: dict[Scalar, int] = {}
    strings: list[str] = []
    argument_strings: list[str] = []

    def observe(value: Scalar) -> None:
        counts[value] = counts.get(value, 0) + 1
        if isinstance(value, str):
            strings.append(value)

    for trace in traces:
        for value in trace.arguments:
            observe(value)
            if isinstance(value, str):
                argument_strings.append(value)
        observe(trace.output)
        for key, value in trace.before + trace.after:
            observe(key)
            observe(value)

    constants: set[Scalar] = {0, 1, 100}
    constants.update(value for value, count in counts.items() if count >= 2)

    # Generic affix discovery lets the same learner infer keys such as
    # ``location:<entity>`` without being told what a location domain is.
    for text in strings:
        for argument in argument_strings:
            if not argument or argument not in text or text == argument:
                continue
            start = text.find(argument)
            prefix = text[:start]
            suffix = text[start + len(argument) :]
            if prefix:
                constants.add(prefix)
            if suffix:
                constants.add(suffix)
    return tuple(sorted(constants, key=lambda value: (_type_of(value), repr(value))))


def _atoms(traces: Sequence[TransitionTrace]) -> tuple[Expr, ...]:
    atoms: list[Expr] = []
    argument_count = len(traces[0].arguments)
    if any(len(trace.arguments) != argument_count for trace in traces):
        raise ValueError("all traces for one task must have the same argument arity")

    for index in range(argument_count):
        value_type = _consistent_type(trace.arguments[index] for trace in traces)
        if value_type is not None:
            atoms.append(Expr("ARG", index, (), value_type))

    for constant in _repeated_constants(traces):
        atoms.append(Expr("CONST", constant, (), _type_of(constant)))

    common_keys = set(traces[0].before_dict())
    for trace in traces[1:]:
        common_keys.intersection_update(trace.before_dict())
    for key in sorted(common_keys):
        value_type = _consistent_type(trace.before_dict()[key] for trace in traces)
        if value_type is not None:
            atoms.append(Expr("STATE", key, (), value_type))

    unique: dict[tuple[object, ...], Expr] = {}
    for atom in atoms:
        key = (atom.op, _freeze(atom.value), atom.value_type)
        current = unique.get(key)
        if current is None or atom.description_bits < current.description_bits:
            unique[key] = atom
    return tuple(sorted(unique.values(), key=lambda expr: (expr.description_bits, repr(expr.render()))))


def _signature(expr: Expr, traces: Sequence[TransitionTrace]) -> tuple[object, ...] | None:
    values: list[object] = []
    try:
        for trace in traces:
            values.append(_freeze(expr.evaluate(trace)))
    except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError):
        return None
    return tuple(values)


def synthesize_expression(
    traces: Iterable[TransitionTrace],
    targets: Sequence[Scalar],
    *,
    max_depth: int = 3,
    max_candidates: int = 250_000,
) -> ExpressionSearchResult:
    items = tuple(traces)
    if not items:
        raise ValueError("at least one trace is required")
    if len(items) != len(targets):
        raise ValueError("target count must equal trace count")
    target_type = _consistent_type(targets)
    if target_type is None:
        raise UnexpressibleTaskError("target values do not have one stable type")
    target_signature = tuple(_freeze(value) for value in targets)

    representatives: dict[tuple[str, tuple[object, ...]], Expr] = {}
    candidate_evaluations = 0
    best_match: Expr | None = None

    def consider(expr: Expr) -> None:
        nonlocal candidate_evaluations, best_match
        if candidate_evaluations >= max_candidates:
            raise UnexpressibleTaskError("candidate budget exhausted")
        signature = _signature(expr, items)
        candidate_evaluations += 1
        if signature is None:
            return
        key = (expr.value_type, signature)
        incumbent = representatives.get(key)
        if incumbent is None or (
            expr.description_bits,
            expr.node_count,
            repr(expr.render()),
        ) < (
            incumbent.description_bits,
            incumbent.node_count,
            repr(incumbent.render()),
        ):
            representatives[key] = expr
        if expr.value_type == target_type and signature == target_signature:
            if best_match is None or (
                expr.description_bits,
                expr.node_count,
                repr(expr.render()),
            ) < (
                best_match.description_bits,
                best_match.node_count,
                repr(best_match.render()),
            ):
                best_match = expr

    atoms = _atoms(items)
    for atom in atoms:
        consider(atom)
    if best_match is not None:
        return ExpressionSearchResult(
            best_match,
            SearchStats(candidate_evaluations, len(representatives), 0),
        )

    # A domain-neutral conditional schema.  Conditions are grounded from atomic
    # observations; branches may be any atomic value.  This is deliberately
    # bounded rather than pretending to solve unrestricted program synthesis.
    nonconstant_atoms = [atom for atom in atoms if atom.op != "CONST"]
    constant_atoms = [atom for atom in atoms if atom.op == "CONST"]
    branch_atoms = [atom for atom in atoms if atom.value_type == target_type]
    for left in nonconstant_atoms:
        for right in constant_atoms:
            if left.value_type != right.value_type:
                continue
            for when_true in branch_atoms:
                for when_false in branch_atoms:
                    if when_true == when_false:
                        continue
                    consider(
                        Expr(
                            "IF_EQ",
                            None,
                            (left, right, when_true, when_false),
                            target_type,
                        )
                    )
    if best_match is not None:
        return ExpressionSearchResult(
            best_match,
            SearchStats(candidate_evaluations, len(representatives), 1),
        )

    binary_specs = (
        ("ADD", "num", "num"),
        ("SUB", "num", "num"),
        ("MUL", "num", "num"),
        ("DIV", "num", "num"),
        ("CONCAT", "str", "str"),
    )
    commutative = {"ADD", "MUL"}

    for depth in range(1, max_depth + 1):
        snapshot = tuple(representatives.values())
        for op, input_type, output_type in binary_specs:
            candidates = [expr for expr in snapshot if expr.value_type == input_type]
            for left in candidates:
                for right in candidates:
                    if max(left.depth, right.depth) != depth - 1:
                        continue
                    if op in commutative and repr(left.render()) > repr(right.render()):
                        continue
                    consider(Expr(op, None, (left, right), output_type))
        if best_match is not None:
            return ExpressionSearchResult(
                best_match,
                SearchStats(candidate_evaluations, len(representatives), depth),
            )

    raise UnexpressibleTaskError(
        f"no expression found within depth={max_depth}, candidates={candidate_evaluations}"
    )


def _state_updates(trace: TransitionTrace) -> tuple[tuple[str, Scalar], ...]:
    before = trace.before_dict()
    after = trace.after_dict()
    removed = sorted(set(before) - set(after))
    if removed:
        raise UnexpressibleTaskError("state deletion is not in the Phase 11a grammar")
    return tuple(sorted((key, value) for key, value in after.items() if before.get(key) != value))


def induce_program(
    traces: Iterable[TransitionTrace],
    *,
    max_depth: int = 3,
    max_candidates: int = 250_000,
) -> ProgramInductionResult:
    items = tuple(traces)
    if not items:
        raise ValueError("at least one transition is required")

    output_search = synthesize_expression(
        items,
        tuple(trace.output for trace in items),
        max_depth=max_depth,
        max_candidates=max_candidates,
    )

    update_rows = tuple(_state_updates(trace) for trace in items)
    update_count = len(update_rows[0])
    if any(len(row) != update_count for row in update_rows):
        raise UnexpressibleTaskError("the number of state updates is not stable")

    updates: list[tuple[Expr, Expr]] = []
    update_stats: list[tuple[SearchStats, SearchStats]] = []
    candidate_evaluations = output_search.stats.candidate_evaluations
    unique_signatures = output_search.stats.unique_signatures
    for index in range(update_count):
        key_search = synthesize_expression(
            items,
            tuple(row[index][0] for row in update_rows),
            max_depth=max_depth,
            max_candidates=max_candidates,
        )
        value_search = synthesize_expression(
            items,
            tuple(row[index][1] for row in update_rows),
            max_depth=max_depth,
            max_candidates=max_candidates,
        )
        updates.append((key_search.expression, value_search.expression))
        update_stats.append((key_search.stats, value_search.stats))
        candidate_evaluations += (
            key_search.stats.candidate_evaluations + value_search.stats.candidate_evaluations
        )
        unique_signatures += key_search.stats.unique_signatures + value_search.stats.unique_signatures

    program = InducedProgram(
        output_search.expression,
        tuple(updates),
        candidate_evaluations,
        unique_signatures,
    )
    return ProgramInductionResult(program, output_search.stats, tuple(update_stats))


def program_accuracy(program: InducedProgram, traces: Iterable[TransitionTrace]) -> float:
    items = tuple(traces)
    correct = 0
    for trace in items:
        after, output = program.execute(trace.arguments, trace.before_dict())
        correct += int(after == trace.after_dict() and output == trace.output)
    return correct / len(items)


def surface_memorization_bits(traces: Iterable[TransitionTrace]) -> int:
    payload = [
        {
            "arguments": [_json_scalar(value) for value in trace.arguments],
            "before": [[key, _json_scalar(value)] for key, value in trace.before],
            "after": [[key, _json_scalar(value)] for key, value in trace.after],
            "output": _json_scalar(trace.output),
        }
        for trace in traces
    ]
    return len(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ) * 8


def hypothesis_information_lower_bound(candidate_evaluations: int) -> float:
    """Minimum bits needed merely to identify one candidate among those tried."""

    return math.log2(max(1, candidate_evaluations))
