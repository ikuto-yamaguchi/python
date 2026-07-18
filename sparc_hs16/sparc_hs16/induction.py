from __future__ import annotations

import itertools
import json
import math
import re
from dataclasses import dataclass, field
from typing import Iterable

from .model import SafeArithmetic, SparseMemory


_NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?")


def extract_numbers(text: str) -> tuple[float, ...]:
    return tuple(float(value) for value in _NUMBER.findall(text))


def extract_answer_number(text: str) -> float:
    values = extract_numbers(text)
    if not values:
        raise ValueError("demonstration answer has no numeric value")
    return values[0]


def _equivalent(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)


@dataclass(frozen=True, slots=True)
class NumericDemonstration:
    prompt: str
    answer: str


@dataclass(slots=True)
class LearnedNumericProgram:
    name: str
    expression: str
    arity: int
    prompt_signatures: tuple[tuple[int, ...], ...]
    demonstrations: int
    candidates_checked: int

    def execute(self, prompt: str) -> float:
        values = extract_numbers(prompt)
        if len(values) != self.arity:
            raise ValueError(f"expected {self.arity} numbers, found {len(values)}")
        variables = {f"n{i}": value for i, value in enumerate(values)}
        return SafeArithmetic.eval(self.expression, variables)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "expression": self.expression,
            "arity": self.arity,
            "prompt_signatures": [list(signature) for signature in self.prompt_signatures],
            "demonstrations": self.demonstrations,
            "candidates_checked": self.candidates_checked,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LearnedNumericProgram":
        return cls(
            name=str(data["name"]),
            expression=str(data["expression"]),
            arity=int(data["arity"]),
            prompt_signatures=tuple(
                tuple(int(value) for value in signature)
                for signature in data.get("prompt_signatures", [])
            ),
            demonstrations=int(data.get("demonstrations", 0)),
            candidates_checked=int(data.get("candidates_checked", 0)),
        )


class NumericProgramInducer:
    """Infer a compact arithmetic program from demonstrations only.

    The search grammar is task-independent. No distance, inventory, price or
    other domain formula is supplied to the learner.
    """

    def __init__(self, max_depth: int = 2, max_candidates: int = 100_000) -> None:
        self.max_depth = max_depth
        self.max_candidates = max_candidates

    def fit(
        self,
        name: str,
        demonstrations: Iterable[NumericDemonstration],
        memory: SparseMemory,
    ) -> LearnedNumericProgram:
        rows = list(demonstrations)
        if len(rows) < 3:
            raise ValueError("at least three demonstrations are required")
        inputs = [extract_numbers(row.prompt) for row in rows]
        outputs = [extract_answer_number(row.answer) for row in rows]
        arities = {len(values) for values in inputs}
        if len(arities) != 1 or 0 in arities:
            raise ValueError("all demonstrations must have the same positive numeric arity")
        arity = arities.pop()
        variables = tuple(f"n{i}" for i in range(arity))
        checked = 0
        for expression in self._expressions(variables):
            checked += 1
            if checked > self.max_candidates:
                break
            try:
                predicted = [
                    SafeArithmetic.eval(
                        expression,
                        {f"n{i}": value for i, value in enumerate(values)},
                    )
                    for values in inputs
                ]
            except (ValueError, ZeroDivisionError, OverflowError, SyntaxError):
                continue
            if all(_equivalent(actual, expected) for actual, expected in zip(predicted, outputs)):
                return LearnedNumericProgram(
                    name=name,
                    expression=expression,
                    arity=arity,
                    prompt_signatures=tuple(memory.signature(row.prompt) for row in rows),
                    demonstrations=len(rows),
                    candidates_checked=checked,
                )
        raise ValueError("no exact compact program found within the induction budget")

    def _expressions(self, variables: tuple[str, ...]):
        atoms = list(variables) + ["0", "1", "2", "10", "100"]
        seen: set[str] = set()
        for atom in atoms:
            if atom not in seen:
                seen.add(atom)
                yield atom
        previous = list(atoms)
        for _depth in range(1, self.max_depth + 1):
            current: list[str] = []
            for left, right in itertools.product(previous, atoms):
                for op in ("+", "-", "*", "/"):
                    expression = f"({left}{op}{right})"
                    if expression in seen:
                        continue
                    seen.add(expression)
                    current.append(expression)
                    yield expression
            previous = current


@dataclass
class NumericMechanismBank:
    memory: SparseMemory
    programs: list[LearnedNumericProgram] = field(default_factory=list)
    route_threshold: float = 0.08

    def learn(self, name: str, demonstrations: Iterable[NumericDemonstration]) -> LearnedNumericProgram:
        program = NumericProgramInducer().fit(name, demonstrations, self.memory)
        self.programs.append(program)
        return program

    def solve(self, prompt: str) -> tuple[str, LearnedNumericProgram, float] | None:
        query = set(self.memory.signature(prompt))
        ranked: list[tuple[float, LearnedNumericProgram]] = []
        for program in self.programs:
            best_score = 0.0
            for signature in program.prompt_signatures:
                candidate = set(signature)
                union = len(query | candidate)
                score = len(query & candidate) / union if union else 0.0
                best_score = max(best_score, score)
            if best_score >= self.route_threshold:
                ranked.append((best_score, program))
        for score, program in sorted(ranked, key=lambda item: item[0], reverse=True):
            try:
                value = program.execute(prompt)
            except (ValueError, ZeroDivisionError, OverflowError, SyntaxError):
                continue
            return self._fmt(value), program, score
        return None

    def to_dict(self) -> dict:
        return {
            "route_threshold": self.route_threshold,
            "programs": [program.to_dict() for program in self.programs],
        }

    @classmethod
    def from_dict(cls, memory: SparseMemory, data: dict) -> "NumericMechanismBank":
        bank = cls(memory=memory, route_threshold=float(data.get("route_threshold", 0.08)))
        bank.programs = [
            LearnedNumericProgram.from_dict(program)
            for program in data.get("programs", [])
        ]
        return bank

    def serialized_bytes(self) -> int:
        return len(json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

    @staticmethod
    def _fmt(value: float) -> str:
        if abs(value - round(value)) < 1e-10:
            return str(int(round(value)))
        return f"{value:.10g}"
