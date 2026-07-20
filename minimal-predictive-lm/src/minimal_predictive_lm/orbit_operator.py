from __future__ import annotations

from dataclasses import dataclass
import itertools
import re
from typing import Iterable, Mapping, Sequence

COEFFICIENTS = (-2, -1, 0, 1, 2)
NUMBER_RE = re.compile(r"-?\d+")


@dataclass(frozen=True)
class TransitionEpisode:
    text: str
    before: Mapping[str, int]
    after: Mapping[str, int]
    source_id: str = ""


@dataclass(frozen=True, order=True)
class AffineOperator:
    arity: int
    rows: tuple[tuple[int, int, int, int], ...]

    def apply_values(self, values: Sequence[int], control: int) -> tuple[int, ...]:
        x0, x1 = (tuple(values) + (0, 0))[:2]
        return tuple(a * x0 + b * x1 + c * control + d for a, b, c, d in self.rows)

    def canonical(self) -> tuple["AffineOperator", tuple[int, ...]]:
        if self.arity == 1:
            return self, (0,)
        variants = [(self.permute(p), p) for p in ((0, 1), (1, 0))]
        return min(variants, key=lambda item: item[0].rows)

    def permute(self, permutation: tuple[int, ...]) -> "AffineOperator":
        if self.arity == 1:
            return self
        inverse = [0] * self.arity
        for new_index, old_index in enumerate(permutation):
            inverse[old_index] = new_index
        rows = []
        for new_output in range(self.arity):
            old_row = self.rows[permutation[new_output]]
            remapped = [0, 0]
            for old_input in range(self.arity):
                remapped[inverse[old_input]] = old_row[old_input]
            rows.append((remapped[0], remapped[1], old_row[2], old_row[3]))
        return AffineOperator(self.arity, tuple(rows))


@dataclass(frozen=True)
class FitResult:
    operator: AffineOperator | None
    support: int
    total: int
    residuals: int


@dataclass(frozen=True)
class Prediction:
    after: dict[str, int] | None
    orbit_id: str | None
    active_candidates: int
    transport_verified: bool


def surface_pattern(text: str, entities: Iterable[str]) -> str:
    normalized = text
    for entity in sorted(set(entities), key=len, reverse=True):
        normalized = normalized.replace(entity, "<E>")
    return " ".join(NUMBER_RE.sub("<N>", normalized).split())


def parse_control(text: str, entities: Iterable[str] = ()) -> int:
    masked = text
    for entity in sorted(set(entities), key=len, reverse=True):
        masked = masked.replace(entity, "<E>")
    match = NUMBER_RE.search(masked)
    return int(match.group()) if match else 0


def ordered_roles(
    text: str,
    before: Mapping[str, int],
    after: Mapping[str, int] | None = None,
) -> tuple[str, ...]:
    candidates = sorted(
        (text.find(entity), entity)
        for entity in before
        if text.find(entity) >= 0
    )
    roles = [entity for _position, entity in candidates]
    if after is not None:
        for entity in before:
            if before.get(entity) != after.get(entity) and entity not in roles:
                roles.append(entity)
    if not roles:
        raise ValueError("episode text does not mention any state entity")
    return tuple(roles[:2])


def _row_score(
    coefficients: tuple[int, int, int, int],
    examples: Sequence[tuple[tuple[int, ...], int, int]],
) -> tuple[int, int]:
    correct = 0
    for values, control, target in examples:
        x0, x1 = (values + (0, 0))[:2]
        predicted = (
            coefficients[0] * x0
            + coefficients[1] * x1
            + coefficients[2] * control
            + coefficients[3]
        )
        correct += int(predicted == target)
    complexity = sum(abs(value) + int(value != 0) for value in coefficients)
    return correct, -complexity


def fit_operator(
    episodes: Sequence[TransitionEpisode],
    minimum_support: int = 2,
    minimum_fraction: float = 0.7,
) -> FitResult:
    prepared = []
    arity: int | None = None
    for episode in episodes:
        roles = ordered_roles(episode.text, episode.before, episode.after)
        arity = len(roles) if arity is None else arity
        if len(roles) != arity:
            continue
        values = tuple(int(episode.before[role]) for role in roles)
        targets = tuple(int(episode.after[role]) for role in roles)
        prepared.append((values, parse_control(episode.text, episode.before), targets))
    if not prepared or arity is None:
        return FitResult(None, 0, len(episodes), len(episodes))

    rows = []
    for output_index in range(arity):
        examples = [
            (values, control, targets[output_index])
            for values, control, targets in prepared
        ]
        best = max(
            itertools.product(COEFFICIENTS, repeat=4),
            key=lambda coefficients: _row_score(coefficients, examples),
        )
        rows.append(tuple(int(value) for value in best))
    operator = AffineOperator(arity, tuple(rows))
    support = sum(
        int(operator.apply_values(values, control) == targets)
        for values, control, targets in prepared
    )
    if support < minimum_support or support / len(prepared) < minimum_fraction:
        return FitResult(None, support, len(prepared), len(prepared) - support)
    return FitResult(operator, support, len(prepared), len(prepared) - support)
