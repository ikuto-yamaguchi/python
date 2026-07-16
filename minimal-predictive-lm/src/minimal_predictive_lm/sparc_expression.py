from __future__ import annotations

import base64
import json
import math
import zlib
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .sparc_language import ReplyResult
from .sparc_programs import (
    SPARCHS5Model,
    _answer_number,
    _format_number,
    _literal_anchors,
    _numbers,
    _numeric_template,
)

Node = tuple


def _node_text(node: Node) -> str:
    kind = node[0]
    if kind == "var":
        return f"N{node[1]}"
    if kind == "const":
        return _format_number(float(node[1]))
    op, left, right = node
    symbol = {"add": "+", "sub": "-", "mul": "×", "div": "÷"}[op]
    return f"({_node_text(left)}{symbol}{_node_text(right)})"


def _node_explanation(node: Node) -> str:
    kind = node[0]
    if kind == "var":
        return f"{node[1] + 1}番目の数"
    if kind == "const":
        return _format_number(float(node[1]))
    op, left, right = node
    verb = {"add": "足す", "sub": "引く", "mul": "掛ける", "div": "割る"}[op]
    return f"{_node_explanation(left)}と{_node_explanation(right)}を{verb}"


def _eval_node(node: Node, values: Sequence[float]) -> float:
    kind = node[0]
    if kind == "var":
        return float(values[int(node[1])])
    if kind == "const":
        return float(node[1])
    op, left, right = node
    a = _eval_node(left, values)
    b = _eval_node(right, values)
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
    raise ValueError(f"unknown node operation: {op}")


@dataclass(frozen=True)
class SynthesizedExpression:
    node: Node
    cost: int
    arity: int
    expression: str
    candidates_generated: int
    semantic_states: int

    def run(self, values: Sequence[float]) -> float:
        return _eval_node(self.node, values)


@dataclass(frozen=True)
class _Candidate:
    node: Node
    cost: int
    outputs: tuple[float, ...]
    text: str


def _semantic_key(outputs: Sequence[float]) -> tuple[float, ...] | None:
    key: list[float] = []
    for value in outputs:
        if not math.isfinite(value) or abs(value) > 1e12:
            return None
        key.append(round(value, 10))
    return tuple(key)


def synthesize_expression(
    examples: Sequence[tuple[tuple[float, ...], float]],
    *,
    max_cost: int = 9,
    max_semantic_states: int = 250_000,
    backward_goal_budget: int = 100_000,
) -> SynthesizedExpression:
    if len(examples) < 2:
        raise ValueError("at least two examples are required")
    arity = len(examples[0][0])
    if any(len(values) != arity for values, _answer in examples):
        raise ValueError("inconsistent arity")
    target = tuple(float(answer) for _values, answer in examples)
    target_key = _semantic_key(target)
    assert target_key is not None
    scale = max(1.0, sum(abs(value) for value in target) / len(target))

    atom_candidates: list[_Candidate] = []
    for index in range(arity):
        atom_candidates.append(
            _Candidate(
                ("var", index),
                1,
                tuple(values[index] for values, _answer in examples),
                f"N{index}",
            )
        )
    for constant in (1.0, 2.0, 3.0, 10.0, 100.0):
        atom_candidates.append(
            _Candidate(
                ("const", constant),
                1,
                tuple(constant for _ in examples),
                _format_number(constant),
            )
        )

    backward_goals: set[tuple[float, ...]] = {target_key}
    frontier: set[tuple[float, ...]] = {target_key}
    backward_depth = max(1, (max_cost - 1) // 2)
    atom_outputs = [candidate.outputs for candidate in atom_candidates]
    for _depth in range(backward_depth):
        next_frontier: set[tuple[float, ...]] = set()
        for goal in frontier:
            for atom in atom_outputs:
                derived_vectors: list[list[float]] = [[], [], [], [], [], []]
                valid = [True] * 6
                for g, a in zip(goal, atom):
                    values = (
                        g - a,
                        g + a,
                        a - g,
                        g / a if abs(a) >= 1e-12 else math.nan,
                        g * a,
                        a / g if abs(g) >= 1e-12 else math.nan,
                    )
                    for index, value in enumerate(values):
                        if not math.isfinite(value) or abs(value) > 1e12:
                            valid[index] = False
                        derived_vectors[index].append(value)
                for index, vector in enumerate(derived_vectors):
                    if not valid[index]:
                        continue
                    key = _semantic_key(vector)
                    if key is None or key in backward_goals:
                        continue
                    backward_goals.add(key)
                    next_frontier.add(key)
                    if len(backward_goals) >= backward_goal_budget:
                        break
                if len(backward_goals) >= backward_goal_budget:
                    break
            if len(backward_goals) >= backward_goal_budget:
                break
        frontier = next_frontier
        if not frontier or len(backward_goals) >= backward_goal_budget:
            break

    by_cost: dict[int, list[_Candidate]] = defaultdict(list)
    semantic: dict[tuple[float, ...], _Candidate] = {}
    generated = 0

    def add(candidate: _Candidate, *, atom: bool = False) -> SynthesizedExpression | None:
        nonlocal generated
        generated += 1
        key = _semantic_key(candidate.outputs)
        if key is None or key in semantic:
            return None
        if not atom and key not in backward_goals:
            return None
        semantic[key] = candidate
        by_cost[candidate.cost].append(candidate)
        mae = sum(
            abs(predicted - expected)
            for predicted, expected in zip(candidate.outputs, target)
        ) / len(target)
        if mae / scale <= 1e-9:
            return SynthesizedExpression(
                candidate.node,
                candidate.cost,
                arity,
                candidate.text,
                generated,
                len(semantic),
            )
        if len(semantic) > max_semantic_states:
            raise RuntimeError("expression search state budget exceeded")
        return None

    for candidate in atom_candidates:
        found = add(candidate, atom=True)
        if found:
            return found

    for cost in range(3, max_cost + 1, 2):
        for left_cost in range(1, cost - 1, 2):
            right_cost = cost - left_cost - 1
            if right_cost < 1:
                continue
            for left in tuple(by_cost.get(left_cost, ())):
                for right in tuple(by_cost.get(right_cost, ())):
                    for op in ("add", "sub", "mul", "div"):
                        if op in {"add", "mul"} and left.text > right.text:
                            continue
                        outputs: list[float] = []
                        valid = True
                        for a, b in zip(left.outputs, right.outputs):
                            try:
                                if op == "add":
                                    value = a + b
                                elif op == "sub":
                                    value = a - b
                                elif op == "mul":
                                    value = a * b
                                else:
                                    if abs(b) < 1e-12:
                                        valid = False
                                        break
                                    value = a / b
                            except OverflowError:
                                valid = False
                                break
                            outputs.append(value)
                        if not valid:
                            continue
                        node = (op, left.node, right.node)
                        found = add(
                            _Candidate(node, cost, tuple(outputs), _node_text(node))
                        )
                        if found:
                            return found
    raise ValueError("no expression found within the search budget")


@dataclass(frozen=True)
class ExpressionSchema:
    template: str
    expression_id: int
    arity: int
    support: int


class SparseExpressionBank:
    """Sparse surface routing to synthesized, shared expression trees."""

    def __init__(self, max_schemas: int = 100_000, max_candidates: int = 32) -> None:
        self.max_schemas = max_schemas
        self.max_candidates = max_candidates
        self.schemas: list[ExpressionSchema] = []
        self.expressions: list[tuple[Node, int]] = []
        self.expression_to_id: dict[str, int] = {}
        self.template_to_schema: dict[str, int] = {}
        self.postings: dict[str, set[int]] = defaultdict(set)
        self.last_candidates = 0
        self.last_anchor_reads = 0
        self.last_expression_cost = 0
        self.last_synthesis_states = 0

    def _intern_expression(self, expression: SynthesizedExpression) -> int:
        key = json.dumps(expression.node, separators=(",", ":"), ensure_ascii=False)
        existing = self.expression_to_id.get(key)
        if existing is not None:
            return existing
        expression_id = len(self.expressions)
        self.expressions.append((expression.node, expression.cost))
        self.expression_to_id[key] = expression_id
        return expression_id

    def _register(self, template: str, expression: SynthesizedExpression, support: int) -> int:
        expression_id = self._intern_expression(expression)
        existing = self.template_to_schema.get(template)
        if existing is not None:
            previous = self.schemas[existing]
            self.schemas[existing] = ExpressionSchema(
                template,
                expression_id,
                expression.arity,
                previous.support + support,
            )
            return existing
        if len(self.schemas) >= self.max_schemas:
            raise MemoryError("expression schema capacity reached")
        schema_id = len(self.schemas)
        self.schemas.append(
            ExpressionSchema(template, expression_id, expression.arity, support)
        )
        self.template_to_schema[template] = schema_id
        for anchor in _literal_anchors(template) or {template}:
            self.postings[anchor].add(schema_id)
        return schema_id

    def teach(
        self,
        examples: Iterable[tuple[str, str | float | int]],
        *,
        max_cost: int = 9,
    ) -> SynthesizedExpression:
        rows = list(examples)
        grouped: dict[str, list[tuple[tuple[float, ...], float]]] = defaultdict(list)
        for problem, answer in rows:
            template, arity = _numeric_template(problem)
            values = _numbers(problem)
            if arity != len(values):
                raise AssertionError("numeric extraction mismatch")
            grouped[template].append((values, _answer_number(answer)))
        if len(grouped) != 1:
            raise ValueError("all demonstrations must share one numeric surface skeleton")
        template, numeric_examples = next(iter(grouped.items()))
        expression = synthesize_expression(numeric_examples, max_cost=max_cost)
        self.last_synthesis_states = expression.semantic_states
        self._register(template, expression, len(rows))
        return expression

    def link_surface(
        self,
        problem: str,
        expression: SynthesizedExpression,
        support: int = 1,
    ) -> int:
        template, arity = _numeric_template(problem)
        if arity != expression.arity:
            raise ValueError("surface arity does not match expression")
        return self._register(template, expression, support)

    def _candidate_ids(self, problem: str) -> list[int]:
        template, _arity = _numeric_template(problem)
        routes = sorted(
            (
                len(self.postings.get(anchor, ())),
                -len(anchor),
                anchor,
            )
            for anchor in _literal_anchors(template)
            if self.postings.get(anchor)
        )
        votes: Counter[int] = Counter()
        reads = 0
        used = 0
        for posting_size, neg_length, anchor in routes:
            if votes and posting_size > self.max_candidates * 4:
                break
            weight = (-neg_length) ** 2 / max(1, posting_size)
            for schema_id in self.postings[anchor]:
                votes[schema_id] += weight
                reads += 1
            used += 1
            if used >= 8 or len(votes) >= self.max_candidates:
                break
        self.last_anchor_reads = reads
        candidates = [schema_id for schema_id, _score in votes.most_common(self.max_candidates)]
        self.last_candidates = len(candidates)
        return candidates

    def solve(self, problem: str) -> ReplyResult | None:
        template, arity = _numeric_template(problem)
        values = _numbers(problem)
        for schema_id in self._candidate_ids(problem):
            schema = self.schemas[schema_id]
            if schema.template != template or schema.arity != arity:
                continue
            node, cost = self.expressions[schema.expression_id]
            try:
                answer = _eval_node(node, values)
            except (ValueError, ZeroDivisionError, OverflowError):
                continue
            if not math.isfinite(answer):
                continue
            self.last_expression_cost = cost
            return ReplyResult(
                text=(
                    f"{_format_number(answer)}です。"
                    f"式は{_node_text(node)}で、"
                    f"{_node_explanation(node)}手順です。"
                ),
                confidence=min(0.99, 0.74 + math.log2(schema.support + 1) * 0.05),
                mechanism="synthesized-expression-tree",
                candidates_inspected=self.last_candidates,
                active_bits=arity,
                estimated_sparse_operations=(
                    self.last_anchor_reads + self.last_candidates + cost
                ),
            )
        return None

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-expression-hs6",
            "max_schemas": self.max_schemas,
            "max_candidates": self.max_candidates,
            "expressions": [
                {"node": node, "cost": cost}
                for node, cost in self.expressions
            ],
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
    def from_bytes(cls, data: bytes) -> "SparseExpressionBank":
        payload = json.loads(zlib.decompress(data))
        bank = cls(int(payload["max_schemas"]), int(payload["max_candidates"]))
        for row in payload["expressions"]:
            node = _lists_to_tuples(row["node"])
            expression_id = len(bank.expressions)
            bank.expressions.append((node, int(row["cost"])))
            key = json.dumps(node, separators=(",", ":"), ensure_ascii=False)
            bank.expression_to_id[key] = expression_id
        for row in payload["schemas"]:
            schema = ExpressionSchema(
                str(row["template"]),
                int(row["expression_id"]),
                int(row["arity"]),
                int(row["support"]),
            )
            schema_id = len(bank.schemas)
            bank.schemas.append(schema)
            bank.template_to_schema[schema.template] = schema_id
            for anchor in _literal_anchors(schema.template) or {schema.template}:
                bank.postings[anchor].add(schema_id)
        return bank

    def report(self) -> dict[str, int | bool]:
        return {
            "expression_schemas": len(self.schemas),
            "unique_expression_trees": len(self.expressions),
            "anchor_edges": sum(len(ids) for ids in self.postings.values()),
            "serialized_bytes": len(self.to_bytes()),
            "last_candidates": self.last_candidates,
            "last_anchor_reads": self.last_anchor_reads,
            "last_expression_cost": self.last_expression_cost,
            "last_synthesis_states": self.last_synthesis_states,
            "global_expression_scan_used": False,
        }


def _lists_to_tuples(value):
    if isinstance(value, list):
        return tuple(_lists_to_tuples(item) for item in value)
    return value


class SPARCHS6Model:
    """HS5 curriculum plus dynamically synthesized expression trees."""

    def __init__(self, base: SPARCHS5Model | None = None) -> None:
        self.base = base or SPARCHS5Model()
        self.expressions = SparseExpressionBank()

    def teach_expression(
        self,
        examples: Iterable[tuple[str, str | float | int]],
        *,
        max_cost: int = 9,
    ) -> SynthesizedExpression:
        return self.expressions.teach(examples, max_cost=max_cost)

    def reply(self, text: str):
        if _numbers(text):
            result = self.expressions.solve(text)
            if result is not None:
                return result
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs6",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "expressions": base64.b85encode(self.expressions.to_bytes()).decode("ascii"),
        }
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS6Model":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS5Model.from_bytes(base64.b85decode(payload["base"])))
        model.expressions = SparseExpressionBank.from_bytes(
            base64.b85decode(payload["expressions"])
        )
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS6Model":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "base": self.base.report(),
            "expressions": self.expressions.report(),
            "serialized_bytes": len(self.to_bytes()),
            "dynamic_expression_synthesis": True,
        }
