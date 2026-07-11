from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import json
import math
from typing import Iterable, Sequence

from .universal_program_induction import (
    Expr,
    InducedProgram,
    SearchStats,
    TransitionTrace,
    UnexpressibleTaskError,
    _atoms,
    _consistent_type,
    _freeze,
    _signature,
)


_LEAF_OPS = frozenset({"ARG", "CONST", "STATE"})
_DYNAMIC_BINDING_OPS = frozenset({"ARG", "STATE"})


@dataclass(frozen=True)
class Macro:
    identifier: str
    body: Expr
    parameter_types: tuple[str, ...]
    support_programs: int

    @property
    def arity(self) -> int:
        return len(self.parameter_types)

    @property
    def description_bits(self) -> int:
        payload = {
            "id": self.identifier,
            "body": self.body.render(),
            "parameter_types": list(self.parameter_types),
            "support_programs": self.support_programs,
        }
        return len(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
                "utf-8"
            )
        ) * 8

    def instantiate(self, arguments: Sequence[Expr]) -> Expr:
        if len(arguments) != self.arity:
            raise ValueError(
                f"macro {self.identifier} expects {self.arity} arguments, got {len(arguments)}"
            )
        for expected, argument in zip(self.parameter_types, arguments):
            if expected != argument.value_type:
                raise TypeError(
                    f"macro {self.identifier} expected {expected}, got {argument.value_type}"
                )

        def substitute(expr: Expr) -> Expr:
            if expr.op == "ARG":
                return arguments[int(expr.value)]
            return Expr(
                expr.op,
                expr.value,
                tuple(substitute(child) for child in expr.children),
                expr.value_type,
            )

        return substitute(self.body)


@dataclass(frozen=True)
class MacroLibrary:
    macros: tuple[Macro, ...]

    @property
    def description_bits(self) -> int:
        return sum(macro.description_bits for macro in self.macros)


@dataclass(frozen=True)
class CompactExpr:
    op: str
    value: int | str | None = None
    children: tuple["CompactExpr", ...] = ()
    value_type: str = "any"

    def render(self) -> object:
        if self.op in _LEAF_OPS:
            return [self.op, self.value]
        if self.op == "CALL":
            return ["CALL", self.value, *(child.render() for child in self.children)]
        return [self.op, *(child.render() for child in self.children)]

    @property
    def description_bits(self) -> int:
        return len(
            json.dumps(
                self.render(), ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
        ) * 8

    @property
    def macro_calls(self) -> int:
        return int(self.op == "CALL") + sum(child.macro_calls for child in self.children)


@dataclass(frozen=True)
class LibraryCandidate:
    expanded: Expr
    compact: CompactExpr


@dataclass(frozen=True)
class LibrarySearchResult:
    candidate: LibraryCandidate
    stats: SearchStats

    @property
    def expression(self) -> Expr:
        return self.candidate.expanded

    @property
    def compact_description_bits(self) -> int:
        return self.candidate.compact.description_bits

    @property
    def macro_calls(self) -> int:
        return self.candidate.compact.macro_calls


@dataclass(frozen=True)
class MacroAdoptionDecision:
    adopted: bool
    macro_bits: int
    compact_program_bits: int
    expanded_program_bits: int
    per_call_program_saving_bits: int
    search_saving_evaluations: int
    normalized_lifetime_gain_bits: int
    break_even_calls_from_storage_only: int | None


def _operator_count(expr: Expr) -> int:
    return int(expr.op not in _LEAF_OPS) + sum(
        _operator_count(child) for child in expr.children
    )


def _subtrees(expr: Expr) -> tuple[Expr, ...]:
    rows = [expr]
    for child in expr.children:
        rows.extend(_subtrees(child))
    return tuple(rows)


def _alpha_normalize(expr: Expr) -> Expr | None:
    mapping: dict[int, int] = {}

    def visit(node: Expr) -> Expr | None:
        if node.op == "STATE":
            # Phase 11b only abstracts argument-parametric expressions.  Exact
            # state keys would turn the library into a domain-specific cache.
            return None
        if node.op == "ARG":
            source = int(node.value)
            target = mapping.setdefault(source, len(mapping))
            return Expr("ARG", target, (), node.value_type)
        children: list[Expr] = []
        for child in node.children:
            normalized = visit(child)
            if normalized is None:
                return None
            children.append(normalized)
        return Expr(node.op, node.value, tuple(children), node.value_type)

    return visit(expr)


def _parameter_types(body: Expr) -> tuple[str, ...]:
    observed: dict[int, str] = {}

    def visit(expr: Expr) -> None:
        if expr.op == "ARG":
            index = int(expr.value)
            previous = observed.get(index)
            if previous is not None and previous != expr.value_type:
                raise TypeError("one macro parameter has inconsistent types")
            observed[index] = expr.value_type
        for child in expr.children:
            visit(child)

    visit(body)
    if not observed:
        return ()
    if sorted(observed) != list(range(max(observed) + 1)):
        raise ValueError("macro parameters are not contiguous")
    return tuple(observed[index] for index in range(max(observed) + 1))


def _canonical_key(expr: Expr) -> str:
    return json.dumps(expr.render(), ensure_ascii=False, separators=(",", ":"))


def induce_macro_library(
    programs: Iterable[InducedProgram],
    *,
    minimum_support: int = 2,
    minimum_operator_count: int = 2,
) -> MacroLibrary:
    if minimum_support < 2:
        raise ValueError("minimum_support must be at least two distinct programs")

    support: dict[str, set[int]] = {}
    bodies: dict[str, Expr] = {}
    for program_index, program in enumerate(programs):
        expressions = [program.output]
        for key, value in program.updates:
            expressions.extend((key, value))
        seen_in_program: set[str] = set()
        for expression in expressions:
            for subtree in _subtrees(expression):
                if _operator_count(subtree) < minimum_operator_count:
                    continue
                normalized = _alpha_normalize(subtree)
                if normalized is None or not _parameter_types(normalized):
                    continue
                key = _canonical_key(normalized)
                if key in seen_in_program:
                    continue
                seen_in_program.add(key)
                support.setdefault(key, set()).add(program_index)
                bodies[key] = normalized

    selected = [
        (key, bodies[key], len(program_ids))
        for key, program_ids in support.items()
        if len(program_ids) >= minimum_support
    ]
    selected.sort(
        key=lambda row: (
            -_operator_count(row[1]),
            row[1].description_bits,
            row[0],
        )
    )
    return MacroLibrary(
        tuple(
            Macro(
                identifier=f"M{index}",
                body=body,
                parameter_types=_parameter_types(body),
                support_programs=count,
            )
            for index, (_, body, count) in enumerate(selected)
        )
    )


def _compact_atom(expr: Expr) -> CompactExpr:
    return CompactExpr(expr.op, expr.value, (), expr.value_type)


def _macro_candidates(
    library: MacroLibrary,
    atoms: Sequence[Expr],
) -> Iterable[LibraryCandidate]:
    # Macro parameters stand for dynamic values.  Constants discovered from the
    # training outputs remain inside macro bodies and are not enumerated as call
    # arguments; otherwise arity-k calls grow with every observed literal^k.
    dynamic_atoms = tuple(atom for atom in atoms if atom.op in _DYNAMIC_BINDING_OPS)
    for macro in library.macros:
        typed_choices = [
            tuple(
                atom
                for atom in dynamic_atoms
                if atom.value_type == parameter_type
            )
            for parameter_type in macro.parameter_types
        ]
        if any(not choices for choices in typed_choices):
            continue
        for arguments in product(*typed_choices):
            expanded = macro.instantiate(arguments)
            compact = CompactExpr(
                "CALL",
                macro.identifier,
                tuple(_compact_atom(argument) for argument in arguments),
                expanded.value_type,
            )
            yield LibraryCandidate(expanded, compact)


def synthesize_expression_with_library(
    traces: Iterable[TransitionTrace],
    targets: Sequence[object],
    library: MacroLibrary,
    *,
    max_depth: int = 1,
    max_candidates: int = 10_000,
) -> LibrarySearchResult:
    items = tuple(traces)
    if not items:
        raise ValueError("at least one trace is required")
    if len(items) != len(targets):
        raise ValueError("target count must equal trace count")
    target_type = _consistent_type(targets)  # type: ignore[arg-type]
    if target_type is None:
        raise UnexpressibleTaskError("target values do not have one stable type")
    target_signature = tuple(_freeze(value) for value in targets)

    representatives: dict[tuple[str, tuple[object, ...]], LibraryCandidate] = {}
    evaluations = 0
    best: LibraryCandidate | None = None

    def consider(candidate: LibraryCandidate) -> bool:
        nonlocal evaluations, best
        if evaluations >= max_candidates:
            raise UnexpressibleTaskError("candidate budget exhausted")
        evaluations += 1
        signature = _signature(candidate.expanded, items)
        if signature is None:
            return False
        key = (candidate.expanded.value_type, signature)
        incumbent = representatives.get(key)
        score = (
            candidate.compact.description_bits,
            candidate.expanded.description_bits,
            repr(candidate.compact.render()),
        )
        improved = incumbent is None or score < (
            incumbent.compact.description_bits,
            incumbent.expanded.description_bits,
            repr(incumbent.compact.render()),
        )
        if improved:
            representatives[key] = candidate
        if candidate.expanded.value_type == target_type and signature == target_signature:
            if best is None or score < (
                best.compact.description_bits,
                best.expanded.description_bits,
                repr(best.compact.render()),
            ):
                best = candidate
        return improved

    atoms = _atoms(items)
    base = tuple(LibraryCandidate(atom, _compact_atom(atom)) for atom in atoms)
    layer: list[LibraryCandidate] = []
    for candidate in (*base, *_macro_candidates(library, atoms)):
        if consider(candidate):
            layer.append(candidate)
    if best is not None:
        return LibrarySearchResult(
            best,
            SearchStats(evaluations, len(representatives), 0),
        )

    specs = (
        ("ADD", "num", "num"),
        ("SUB", "num", "num"),
        ("MUL", "num", "num"),
        ("DIV", "num", "num"),
        ("CONCAT", "str", "str"),
    )
    commutative = {"ADD", "MUL"}
    for depth in range(1, max_depth + 1):
        next_layer: list[LibraryCandidate] = []
        for op, input_type, output_type in specs:
            parents = [row for row in layer if row.expanded.value_type == input_type]
            typed_atoms = [row for row in base if row.expanded.value_type == input_type]
            for parent in parents:
                for atom in typed_atoms:
                    orientations = [(parent, atom)]
                    if op not in commutative:
                        orientations.append((atom, parent))
                    for left, right in orientations:
                        candidate = LibraryCandidate(
                            Expr(
                                op,
                                None,
                                (left.expanded, right.expanded),
                                output_type,
                            ),
                            CompactExpr(
                                op,
                                None,
                                (left.compact, right.compact),
                                output_type,
                            ),
                        )
                        if consider(candidate):
                            next_layer.append(candidate)
        if best is not None:
            return LibrarySearchResult(
                best,
                SearchStats(evaluations, len(representatives), depth),
            )
        layer = next_layer
        if not layer:
            break

    raise UnexpressibleTaskError(
        f"no library expression found within depth={max_depth}, candidates={evaluations}"
    )


def expression_accuracy(
    expression: Expr,
    traces: Iterable[TransitionTrace],
) -> float:
    items = tuple(traces)
    return sum(
        _freeze(expression.evaluate(trace)) == _freeze(trace.output) for trace in items
    ) / len(items)


def decide_macro_adoption(
    macro: Macro,
    result: LibrarySearchResult,
    *,
    baseline_candidate_budget: int,
    expected_future_calls: int = 1,
    candidate_evaluation_cost_bits: int = 1,
    verification_accuracy: float = 1.0,
) -> MacroAdoptionDecision:
    compact_bits = result.compact_description_bits
    expanded_bits = result.expression.description_bits
    per_call_saving = max(0, expanded_bits - compact_bits)
    search_saving = max(0, baseline_candidate_budget - result.stats.candidate_evaluations)
    gain = (
        per_call_saving * expected_future_calls
        + search_saving * candidate_evaluation_cost_bits
        - macro.description_bits
    )
    break_even = None
    if per_call_saving > 0:
        break_even = math.ceil(macro.description_bits / per_call_saving)
    return MacroAdoptionDecision(
        adopted=verification_accuracy == 1.0 and gain > 0,
        macro_bits=macro.description_bits,
        compact_program_bits=compact_bits,
        expanded_program_bits=expanded_bits,
        per_call_program_saving_bits=per_call_saving,
        search_saving_evaluations=search_saving,
        normalized_lifetime_gain_bits=gain,
        break_even_calls_from_storage_only=break_even,
    )
