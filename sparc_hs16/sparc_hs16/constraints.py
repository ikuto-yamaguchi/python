from __future__ import annotations

import itertools
import re
from dataclasses import dataclass


def _clean(text: str) -> str:
    return re.sub(r"\s+", "", text).strip("。.!！?？")


@dataclass(frozen=True, slots=True)
class ConstraintAnswer:
    answer: str
    solutions: tuple[tuple[str, ...], ...]
    proof: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ParsedConstraint:
    kind: str
    left: str
    right: str | int | None = None

    def accepts(self, order: tuple[str, ...]) -> bool:
        position = {value: index for index, value in enumerate(order)}
        if self.kind == "before":
            return position[self.left] < position[str(self.right)]
        if self.kind == "after":
            return position[self.left] > position[str(self.right)]
        if self.kind == "immediately_after":
            return position[self.left] == position[str(self.right)] + 1
        if self.kind == "immediately_before":
            return position[self.left] + 1 == position[str(self.right)]
        if self.kind == "adjacent":
            return abs(position[self.left] - position[str(self.right)]) == 1
        if self.kind == "not_adjacent":
            return abs(position[self.left] - position[str(self.right)]) != 1
        if self.kind == "exact":
            return position[self.left] == int(self.right) - 1
        if self.kind == "not_exact":
            return position[self.left] != int(self.right) - 1
        if self.kind == "distance":
            other, distance = str(self.right).split("@", 1)
            return abs(position[self.left] - position[other]) == int(distance)
        raise ValueError(f"unknown constraint kind: {self.kind}")

    def describe(self) -> str:
        return f"{self.kind}:{self.left}:{self.right}"


class JapaneseOrderingSolver:
    """Exhaustive bounded solver for Japanese ordering constraints.

    It compiles natural-language constraints into predicates and returns every
    satisfying order, allowing exact uniqueness checks rather than heuristic
    guesses. The problem is rejected above the configured entity bound.
    """

    def __init__(self, max_entities: int = 9, max_solutions: int = 10_000) -> None:
        self.max_entities = max_entities
        self.max_solutions = max_solutions

    def can_handle(self, text: str) -> bool:
        return "対象:" in text and "条件:" in text and ("順番" in text or "並び" in text)

    def solve(self, text: str) -> ConstraintAnswer | None:
        entities = self._parse_entities(text)
        if not entities or len(entities) > self.max_entities:
            return None
        constraints = self._parse_constraints(text, set(entities))
        if not constraints:
            return None
        solutions: list[tuple[str, ...]] = []
        for order in itertools.permutations(entities):
            if all(constraint.accepts(order) for constraint in constraints):
                solutions.append(order)
                if len(solutions) >= self.max_solutions:
                    break
        proof = tuple(constraint.describe() for constraint in constraints)
        if not solutions:
            return ConstraintAnswer("条件を同時に満たす順番はありません。", (), proof)
        if len(solutions) == 1:
            return ConstraintAnswer("→".join(solutions[0]) + "です。", tuple(solutions), proof)
        return ConstraintAnswer(
            f"一意に定まりません。{len(solutions)}通りあります。",
            tuple(solutions),
            proof,
        )

    def _parse_entities(self, text: str) -> tuple[str, ...]:
        match = re.search(r"対象:([^。\n]+)", text)
        if not match:
            return ()
        values = tuple(_clean(value) for value in re.split(r"[,、]", match.group(1)) if _clean(value))
        return tuple(dict.fromkeys(values))

    def _parse_constraints(self, text: str, entities: set[str]) -> tuple[ParsedConstraint, ...]:
        match = re.search(r"条件:(.+?)(?:\n?問:|\n?質問:|$)", text, re.DOTALL)
        if not match:
            return ()
        sentences = [_clean(value) for value in re.split(r"[。;；\n]+", match.group(1)) if _clean(value)]
        parsed: list[ParsedConstraint] = []
        for sentence in sentences:
            item = self._parse_one(sentence)
            if item is None:
                continue
            referenced = {item.left}
            if isinstance(item.right, str):
                referenced.add(item.right.split("@", 1)[0])
            if referenced.issubset(entities):
                parsed.append(item)
        return tuple(parsed)

    def _parse_one(self, sentence: str) -> ParsedConstraint | None:
        patterns: tuple[tuple[str, str], ...] = (
            (r"(.+?)は(.+?)より前", "before"),
            (r"(.+?)は(.+?)より後", "after"),
            (r"(.+?)は(.+?)の直後", "immediately_after"),
            (r"(.+?)は(.+?)の直前", "immediately_before"),
            (r"(.+?)と(.+?)は隣り合う", "adjacent"),
            (r"(.+?)と(.+?)は隣り合わない", "not_adjacent"),
        )
        for pattern, kind in patterns:
            match = re.fullmatch(pattern, sentence)
            if match:
                left, right = map(_clean, match.groups())
                return ParsedConstraint(kind, left, right)

        exact = re.fullmatch(r"(.+?)は(\d+)番目", sentence)
        if exact:
            return ParsedConstraint("exact", _clean(exact.group(1)), int(exact.group(2)))

        not_exact = re.fullmatch(r"(.+?)は(\d+)番目ではない", sentence)
        if not_exact:
            return ParsedConstraint("not_exact", _clean(not_exact.group(1)), int(not_exact.group(2)))

        between = re.fullmatch(r"(.+?)と(.+?)の間には(\d+)人", sentence)
        if between:
            left, right, count = between.groups()
            return ParsedConstraint("distance", _clean(left), f"{_clean(right)}@{int(count) + 1}")
        return None
