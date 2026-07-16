from __future__ import annotations

import base64
import json
import math
import re
import zlib
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .sparc_expression import SPARCHS6Model, _node_text
from .sparc_language import ReplyResult
from .sparc_programs import _format_number, _literal_anchors

Dim = tuple[int, int, int, int, int]
Node = tuple


@dataclass(frozen=True)
class UnitSpec:
    symbol: str
    dimension: Dim
    scale: float


ZERO: Dim = (0, 0, 0, 0, 0)
LENGTH: Dim = (1, 0, 0, 0, 0)
TIME: Dim = (0, 1, 0, 0, 0)
MASS: Dim = (0, 0, 1, 0, 0)
CURRENCY: Dim = (0, 0, 0, 1, 0)
COUNT: Dim = (0, 0, 0, 0, 1)
SPEED: Dim = (1, -1, 0, 0, 0)
AREA: Dim = (2, 0, 0, 0, 0)


def _dadd(a: Dim, b: Dim) -> Dim:
    return tuple(x + y for x, y in zip(a, b))  # type: ignore[return-value]


def _dsub(a: Dim, b: Dim) -> Dim:
    return tuple(x - y for x, y in zip(a, b))  # type: ignore[return-value]


UNIT_SPECS: dict[str, UnitSpec] = {
    "": UnitSpec("", ZERO, 1.0),
    "%": UnitSpec("%", ZERO, 0.01),
    "mm": UnitSpec("mm", LENGTH, 0.001),
    "cm": UnitSpec("cm", LENGTH, 0.01),
    "m": UnitSpec("m", LENGTH, 1.0),
    "km": UnitSpec("km", LENGTH, 1000.0),
    "秒": UnitSpec("秒", TIME, 1.0),
    "分": UnitSpec("分", TIME, 60.0),
    "時間": UnitSpec("時間", TIME, 3600.0),
    "時": UnitSpec("時", TIME, 3600.0),
    "g": UnitSpec("g", MASS, 0.001),
    "kg": UnitSpec("kg", MASS, 1.0),
    "円": UnitSpec("円", CURRENCY, 1.0),
    "人": UnitSpec("人", COUNT, 1.0),
    "個": UnitSpec("個", COUNT, 1.0),
    "本": UnitSpec("本", COUNT, 1.0),
    "枚": UnitSpec("枚", COUNT, 1.0),
    "m/s": UnitSpec("m/s", SPEED, 1.0),
    "km/h": UnitSpec("km/h", SPEED, 1000.0 / 3600.0),
    "mm²": UnitSpec("mm²", AREA, 1e-6),
    "cm²": UnitSpec("cm²", AREA, 1e-4),
    "m²": UnitSpec("m²", AREA, 1.0),
    "km²": UnitSpec("km²", AREA, 1e6),
    "平方mm": UnitSpec("平方mm", AREA, 1e-6),
    "平方cm": UnitSpec("平方cm", AREA, 1e-4),
    "平方m": UnitSpec("平方m", AREA, 1.0),
    "平方km": UnitSpec("平方km", AREA, 1e6),
}
_UNIT_PATTERN = "|".join(
    sorted((re.escape(key) for key in UNIT_SPECS if key), key=len, reverse=True)
)
_QUANTITY_RE = re.compile(rf"([-+]?\d+(?:\.\d+)?)\s*({_UNIT_PATTERN})?")
_OUTPUT_RE = re.compile(rf"何\s*({_UNIT_PATTERN})")


@dataclass(frozen=True)
class Quantity:
    raw_value: float
    unit: UnitSpec
    base_value: float


@dataclass(frozen=True)
class ParsedUnitProblem:
    template: str
    quantities: tuple[Quantity, ...]
    output_unit: UnitSpec


def _normalise(text: str) -> str:
    return re.sub(
        r"\s+", "", text.strip().replace("?", "？").replace("!", "！")
    ).strip("。！")


def parse_unit_problem(text: str) -> ParsedUnitProblem:
    text = _normalise(text)
    quantities: list[Quantity] = []
    chunks: list[str] = []
    cursor = 0
    for match in _QUANTITY_RE.finditer(text):
        if (
            match.start() > 0
            and text[match.start() - 1].isascii()
            and text[match.start() - 1].isalpha()
        ):
            continue
        value = float(match.group(1))
        symbol = match.group(2) or ""
        prefix = text[max(0, match.start() - 2) : match.start()]
        if prefix.endswith("時速") and symbol == "km":
            unit = UNIT_SPECS["km/h"]
        elif prefix.endswith("秒速") and symbol == "m":
            unit = UNIT_SPECS["m/s"]
        else:
            unit = UNIT_SPECS[symbol]
        chunks.append(text[cursor : match.start()])
        chunks.append(
            "{Q"
            + str(len(quantities))
            + ":"
            + ",".join(map(str, unit.dimension))
            + "}"
        )
        cursor = match.end()
        quantities.append(Quantity(value, unit, value * unit.scale))
    chunks.append(text[cursor:])

    output_unit: UnitSpec | None = None
    if "時速何km" in text:
        output_unit = UNIT_SPECS["km/h"]
    elif "秒速何m" in text:
        output_unit = UNIT_SPECS["m/s"]
    else:
        matches = list(_OUTPUT_RE.finditer(text))
        if matches:
            output_unit = UNIT_SPECS[matches[-1].group(1)]
    if output_unit is None:
        raise ValueError("problem must state an output unit after 何")
    if not quantities:
        raise ValueError("problem contains no quantities")
    return ParsedUnitProblem("".join(chunks), tuple(quantities), output_unit)


def answer_to_base(answer: str | float | int, output_unit: UnitSpec) -> float:
    if isinstance(answer, (float, int)):
        value = float(answer)
    else:
        match = _QUANTITY_RE.search(_normalise(str(answer)))
        if not match:
            raise ValueError("answer contains no quantity")
        value = float(match.group(1))
        symbol = match.group(2)
        if symbol:
            supplied = UNIT_SPECS[symbol]
            if supplied.dimension != output_unit.dimension:
                raise ValueError("answer unit dimension mismatch")
            return value * supplied.scale
    return value * output_unit.scale


def _eval(node: Node, values: Sequence[float]) -> float:
    kind = node[0]
    if kind == "var":
        return float(values[int(node[1])])
    if kind == "const":
        return float(node[1])
    op, left, right = node
    a = _eval(left, values)
    b = _eval(right, values)
    if op == "add":
        return a + b
    if op == "sub":
        return a - b
    if op == "mul":
        return a * b
    if op == "div":
        if abs(b) < 1e-12:
            raise ZeroDivisionError
        return a / b
    raise ValueError(op)


def _semantic(values: Sequence[float]) -> tuple[float, ...] | None:
    output: list[float] = []
    for value in values:
        if not math.isfinite(value) or abs(value) > 1e15:
            return None
        output.append(round(value, 10))
    return tuple(output)


@dataclass(frozen=True)
class TypedExpression:
    node: Node
    cost: int
    input_dimensions: tuple[Dim, ...]
    output_dimension: Dim
    semantic_states: int
    candidates_generated: int


@dataclass(frozen=True)
class _Candidate:
    node: Node
    cost: int
    outputs: tuple[float, ...]
    dimension: Dim
    text: str


def synthesize_typed_expression(
    examples: Sequence[tuple[tuple[float, ...], tuple[Dim, ...], float, Dim]],
    *,
    max_cost: int = 9,
    max_states: int = 100_000,
    backward_budget: int = 50_000,
) -> TypedExpression:
    if len(examples) < 2:
        raise ValueError("at least two examples are required")
    arity = len(examples[0][0])
    input_dimensions = examples[0][1]
    target_dimension = examples[0][3]
    if any(
        len(values) != arity
        or dimensions != input_dimensions
        or output_dimension != target_dimension
        for values, dimensions, _answer, output_dimension in examples
    ):
        raise ValueError("examples must have matching typed signatures")
    target = tuple(answer for _values, _dimensions, answer, _output in examples)
    target_key = _semantic(target)
    assert target_key is not None
    scale = max(1.0, sum(abs(value) for value in target) / len(target))

    atoms: list[_Candidate] = []
    for index, dimension in enumerate(input_dimensions):
        atoms.append(
            _Candidate(
                ("var", index),
                1,
                tuple(values[index] for values, _dimensions, _answer, _output in examples),
                dimension,
                f"N{index}",
            )
        )
    for constant in (1.0, 2.0, 3.0, 10.0, 100.0):
        atoms.append(
            _Candidate(
                ("const", constant),
                1,
                tuple(constant for _ in examples),
                ZERO,
                _format_number(constant),
            )
        )

    goals: set[tuple[tuple[float, ...], Dim]] = {(target_key, target_dimension)}
    frontier = set(goals)
    backward_depth = max(1, (max_cost - 1) // 2)
    for _depth in range(backward_depth):
        next_frontier: set[tuple[tuple[float, ...], Dim]] = set()
        for goal_values, goal_dimension in frontier:
            for atom in atoms:
                variants: list[tuple[tuple[float, ...], Dim]] = []
                if atom.dimension == goal_dimension:
                    variants.extend(
                        [
                            (
                                tuple(
                                    goal - value
                                    for goal, value in zip(goal_values, atom.outputs)
                                ),
                                goal_dimension,
                            ),
                            (
                                tuple(
                                    goal + value
                                    for goal, value in zip(goal_values, atom.outputs)
                                ),
                                goal_dimension,
                            ),
                            (
                                tuple(
                                    value - goal
                                    for goal, value in zip(goal_values, atom.outputs)
                                ),
                                goal_dimension,
                            ),
                        ]
                    )
                division_values: list[float] = []
                valid = True
                for goal, value in zip(goal_values, atom.outputs):
                    if abs(value) < 1e-12:
                        valid = False
                        break
                    division_values.append(goal / value)
                if valid:
                    variants.append(
                        (
                            tuple(division_values),
                            _dsub(goal_dimension, atom.dimension),
                        )
                    )
                variants.append(
                    (
                        tuple(
                            goal * value
                            for goal, value in zip(goal_values, atom.outputs)
                        ),
                        _dadd(goal_dimension, atom.dimension),
                    )
                )
                inverse_values: list[float] = []
                valid = True
                for goal, value in zip(goal_values, atom.outputs):
                    if abs(goal) < 1e-12:
                        valid = False
                        break
                    inverse_values.append(value / goal)
                if valid:
                    variants.append(
                        (
                            tuple(inverse_values),
                            _dsub(atom.dimension, goal_dimension),
                        )
                    )
                for values, dimension in variants:
                    key = _semantic(values)
                    if key is None or (key, dimension) in goals:
                        continue
                    goals.add((key, dimension))
                    next_frontier.add((key, dimension))
                    if len(goals) >= backward_budget:
                        break
                if len(goals) >= backward_budget:
                    break
            if len(goals) >= backward_budget:
                break
        frontier = next_frontier
        if not frontier or len(goals) >= backward_budget:
            break

    by_cost: dict[int, list[_Candidate]] = defaultdict(list)
    semantic: dict[tuple[tuple[float, ...], Dim], _Candidate] = {}
    generated = 0

    def add(candidate: _Candidate, *, atom: bool = False) -> TypedExpression | None:
        nonlocal generated
        generated += 1
        key = _semantic(candidate.outputs)
        if key is None or (key, candidate.dimension) in semantic:
            return None
        if not atom and (key, candidate.dimension) not in goals:
            return None
        semantic[(key, candidate.dimension)] = candidate
        by_cost[candidate.cost].append(candidate)
        mae = sum(
            abs(predicted - expected)
            for predicted, expected in zip(candidate.outputs, target)
        ) / len(target)
        if candidate.dimension == target_dimension and mae / scale <= 1e-9:
            return TypedExpression(
                candidate.node,
                candidate.cost,
                input_dimensions,
                target_dimension,
                len(semantic),
                generated,
            )
        if len(semantic) > max_states:
            raise RuntimeError("typed expression state budget exceeded")
        return None

    for candidate in atoms:
        found = add(candidate, atom=True)
        if found is not None:
            return found

    for cost in range(3, max_cost + 1, 2):
        for left_cost in range(1, cost - 1, 2):
            right_cost = cost - left_cost - 1
            if right_cost < 1:
                continue
            for left in tuple(by_cost.get(left_cost, ())):
                for right in tuple(by_cost.get(right_cost, ())):
                    for operation in ("add", "sub", "mul", "div"):
                        if operation in {"add", "mul"} and left.text > right.text:
                            continue
                        if (
                            operation in {"add", "sub"}
                            and left.dimension != right.dimension
                        ):
                            continue
                        if operation in {"add", "sub"}:
                            dimension = left.dimension
                        elif operation == "mul":
                            dimension = _dadd(left.dimension, right.dimension)
                        else:
                            dimension = _dsub(left.dimension, right.dimension)
                        outputs: list[float] = []
                        valid = True
                        for a, b in zip(left.outputs, right.outputs):
                            if operation == "add":
                                value = a + b
                            elif operation == "sub":
                                value = a - b
                            elif operation == "mul":
                                value = a * b
                            else:
                                if abs(b) < 1e-12:
                                    valid = False
                                    break
                                value = a / b
                            outputs.append(value)
                        if not valid:
                            continue
                        node = (operation, left.node, right.node)
                        found = add(
                            _Candidate(
                                node,
                                cost,
                                tuple(outputs),
                                dimension,
                                _node_text(node),
                            )
                        )
                        if found is not None:
                            return found
    raise ValueError("no dimensionally valid expression found")


@dataclass(frozen=True)
class TypedSchema:
    template: str
    expression_id: int
    input_dimensions: tuple[Dim, ...]
    output_symbol: str
    support: int


class SparseTypedPlanBank:
    def __init__(self, max_schemas: int = 100_000, max_candidates: int = 32) -> None:
        self.max_schemas = max_schemas
        self.max_candidates = max_candidates
        self.schemas: list[TypedSchema] = []
        self.expressions: list[TypedExpression] = []
        self.expression_ids: dict[str, int] = {}
        self.template_ids: dict[tuple[object, ...], int] = {}
        self.postings: dict[str, set[int]] = defaultdict(set)
        self.last_candidates = 0
        self.last_anchor_reads = 0
        self.last_synthesis_states = 0

    def _intern_expression(self, expression: TypedExpression) -> int:
        key = json.dumps(
            [
                expression.node,
                expression.input_dimensions,
                expression.output_dimension,
            ],
            separators=(",", ":"),
        )
        existing = self.expression_ids.get(key)
        if existing is not None:
            return existing
        expression_id = len(self.expressions)
        self.expressions.append(expression)
        self.expression_ids[key] = expression_id
        return expression_id

    def _register(
        self, problem: ParsedUnitProblem, expression: TypedExpression, support: int
    ) -> int:
        expression_id = self._intern_expression(expression)
        signature = (
            problem.template,
            tuple(quantity.unit.dimension for quantity in problem.quantities),
            problem.output_unit.symbol,
        )
        existing = self.template_ids.get(signature)
        if existing is not None:
            return existing
        if len(self.schemas) >= self.max_schemas:
            raise MemoryError("typed plan schema capacity reached")
        schema_id = len(self.schemas)
        schema = TypedSchema(
            problem.template,
            expression_id,
            tuple(quantity.unit.dimension for quantity in problem.quantities),
            problem.output_unit.symbol,
            support,
        )
        self.schemas.append(schema)
        self.template_ids[signature] = schema_id
        for anchor in _literal_anchors(problem.template) or {problem.template}:
            self.postings[anchor].add(schema_id)
        return schema_id

    def teach(
        self,
        examples: Iterable[tuple[str, str | float | int]],
        *,
        max_cost: int = 9,
    ) -> TypedExpression:
        rows: list[tuple[tuple[float, ...], tuple[Dim, ...], float, Dim]] = []
        first: ParsedUnitProblem | None = None
        for problem_text, answer in examples:
            problem = parse_unit_problem(problem_text)
            if first is None:
                first = problem
            if (
                problem.template != first.template
                or tuple(q.unit.dimension for q in problem.quantities)
                != tuple(q.unit.dimension for q in first.quantities)
                or problem.output_unit.dimension != first.output_unit.dimension
            ):
                raise ValueError("typed demonstrations must share one signature")
            rows.append(
                (
                    tuple(quantity.base_value for quantity in problem.quantities),
                    tuple(quantity.unit.dimension for quantity in problem.quantities),
                    answer_to_base(answer, problem.output_unit),
                    problem.output_unit.dimension,
                )
            )
        assert first is not None
        expression = synthesize_typed_expression(rows, max_cost=max_cost)
        self.last_synthesis_states = expression.semantic_states
        self._register(first, expression, len(rows))
        return expression

    def link_surface(
        self,
        problem_text: str,
        expression: TypedExpression,
        *,
        support: int = 1,
    ) -> int:
        problem = parse_unit_problem(problem_text)
        if (
            tuple(quantity.unit.dimension for quantity in problem.quantities)
            != expression.input_dimensions
            or problem.output_unit.dimension != expression.output_dimension
        ):
            raise ValueError("surface typed signature mismatch")
        return self._register(problem, expression, support)

    def _candidate_ids(self, problem: ParsedUnitProblem) -> list[int]:
        routes = sorted(
            (
                len(self.postings.get(anchor, ())),
                -len(anchor),
                anchor,
            )
            for anchor in _literal_anchors(problem.template)
            if self.postings.get(anchor)
        )
        votes: Counter[int] = Counter()
        reads = 0
        used_routes = 0
        for posting_size, negative_length, anchor in routes:
            if votes and posting_size > self.max_candidates * 4:
                break
            weight = (-negative_length) ** 2 / max(1, posting_size)
            for schema_id in self.postings[anchor]:
                votes[schema_id] += weight
                reads += 1
            used_routes += 1
            if used_routes >= 8 or len(votes) >= self.max_candidates:
                break
        self.last_anchor_reads = reads
        candidates = [
            schema_id for schema_id, _score in votes.most_common(self.max_candidates)
        ]
        self.last_candidates = len(candidates)
        return candidates

    def solve(self, problem_text: str) -> ReplyResult | None:
        try:
            problem = parse_unit_problem(problem_text)
        except ValueError:
            return None
        dimensions = tuple(
            quantity.unit.dimension for quantity in problem.quantities
        )
        for schema_id in self._candidate_ids(problem):
            schema = self.schemas[schema_id]
            if (
                schema.template != problem.template
                or schema.input_dimensions != dimensions
                or UNIT_SPECS[schema.output_symbol].dimension
                != problem.output_unit.dimension
            ):
                continue
            expression = self.expressions[schema.expression_id]
            value = _eval(
                expression.node,
                tuple(quantity.base_value for quantity in problem.quantities),
            ) / problem.output_unit.scale
            return ReplyResult(
                text=(
                    f"{_format_number(value)}{problem.output_unit.symbol}です。"
                    f"式は{_node_text(expression.node)}で、単位の次元も一致します。"
                ),
                confidence=min(
                    0.99, 0.75 + math.log2(schema.support + 1) * 0.05
                ),
                mechanism="unit-typed-plan",
                candidates_inspected=self.last_candidates,
                active_bits=len(problem.quantities),
                estimated_sparse_operations=(
                    self.last_anchor_reads
                    + self.last_candidates
                    + expression.cost
                ),
            )
        return None

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-unit-hs7",
            "max_schemas": self.max_schemas,
            "max_candidates": self.max_candidates,
            "expressions": [asdict(expression) for expression in self.expressions],
            "schemas": [asdict(schema) for schema in self.schemas],
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseTypedPlanBank":
        payload = json.loads(zlib.decompress(data))
        bank = cls(int(payload["max_schemas"]), int(payload["max_candidates"]))

        def tuples(value):
            if isinstance(value, list):
                return tuple(tuples(item) for item in value)
            return value

        for row in payload["expressions"]:
            expression = TypedExpression(
                tuples(row["node"]),
                int(row["cost"]),
                tuples(row["input_dimensions"]),
                tuples(row["output_dimension"]),
                int(row["semantic_states"]),
                int(row["candidates_generated"]),
            )
            bank._intern_expression(expression)
        for row in payload["schemas"]:
            schema = TypedSchema(
                str(row["template"]),
                int(row["expression_id"]),
                tuples(row["input_dimensions"]),
                str(row["output_symbol"]),
                int(row["support"]),
            )
            schema_id = len(bank.schemas)
            bank.schemas.append(schema)
            bank.template_ids[
                (schema.template, schema.input_dimensions, schema.output_symbol)
            ] = schema_id
            for anchor in _literal_anchors(schema.template) or {schema.template}:
                bank.postings[anchor].add(schema_id)
        return bank

    def report(self) -> dict[str, int | bool]:
        return {
            "typed_schemas": len(self.schemas),
            "unique_typed_plans": len(self.expressions),
            "serialized_bytes": len(self.to_bytes()),
            "last_candidates": self.last_candidates,
            "last_anchor_reads": self.last_anchor_reads,
            "last_synthesis_states": self.last_synthesis_states,
            "global_plan_scan_used": False,
        }


class SPARCHS7Model:
    def __init__(self, base: SPARCHS6Model | None = None) -> None:
        self.base = base or SPARCHS6Model()
        self.typed_plans = SparseTypedPlanBank()

    def teach_units(
        self,
        examples: Iterable[tuple[str, str | float | int]],
        *,
        max_cost: int = 9,
    ) -> TypedExpression:
        return self.typed_plans.teach(examples, max_cost=max_cost)

    def reply(self, text: str):
        result = self.typed_plans.solve(text)
        if result is not None:
            return result
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs7",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "typed": base64.b85encode(self.typed_plans.to_bytes()).decode("ascii"),
        }
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS7Model":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS6Model.from_bytes(base64.b85decode(payload["base"])))
        model.typed_plans = SparseTypedPlanBank.from_bytes(
            base64.b85decode(payload["typed"])
        )
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS7Model":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "base": self.base.report(),
            "typed_plans": self.typed_plans.report(),
            "serialized_bytes": len(self.to_bytes()),
            "unit_dimensional_checking": True,
        }
