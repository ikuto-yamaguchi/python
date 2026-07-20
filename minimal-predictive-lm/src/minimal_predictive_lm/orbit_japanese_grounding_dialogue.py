from __future__ import annotations

import math
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Iterable

from .orbit_japanese_grounding_core import (
    NUMBER, Binding, Episode, GroundedOrbit, align, cosine, ngrams,
)

@dataclass(frozen=True)
class DialogueTurn:
    text: str
    before: str
    after: str


@dataclass(frozen=True)
class Dialogue:
    turns: tuple[DialogueTurn, ...]


@dataclass(frozen=True)
class DiscoursePattern:
    operator: str
    abstract: str
    count: int


class DiscourseOrbit:
    """Retains one executable binding instead of attending over full dialogue history."""

    def __init__(self) -> None:
        self.base = GroundedOrbit()
        self.patterns: list[DiscoursePattern] = []
        self.pattern_grams: list[Counter[str]] = []
        self.cue_weights: dict[str, dict[str, float]] = {}
        self.context: Binding | None = None
        self.failures: list[str] = []

    @staticmethod
    def abstract(text: str) -> str:
        return NUMBER.sub("<N>", re.sub(r"\s+", "", text))

    @staticmethod
    def current_binding(turn: DialogueTurn) -> Binding | None:
        changed = [row for row in align(turn.before, turn.after) if row[2]]
        negative = [row for row in changed if row[2] < 0]
        positive = [row for row in changed if row[2] > 0]
        if len(negative) != 1 or len(positive) != 1:
            return None
        source, destination = negative[0][0], positive[0][0]
        common = set(source.content) & set(destination.content)
        if not common:
            return None
        item = max(common, key=len)
        sources = [value for value in source.content if value != item]
        destinations = [value for value in destination.content if value != item]
        if not sources or not destinations:
            return None
        return Binding(
            max(sources, key=len),
            max(destinations, key=len),
            item,
            abs(negative[0][2]),
        )

    @staticmethod
    def relation(previous: Binding, current: Binding | None, turn: DialogueTurn) -> str | None:
        if turn.before == turn.after:
            return "NOOP"
        if current is None or current.item != previous.item:
            return None
        if current.src == previous.src and current.dst == previous.dst:
            return "REUSE"
        if current.src == previous.dst and current.dst == previous.src:
            return "SWAP" if NUMBER.search(turn.text) else "UNDO"
        return None

    def fit(self, dialogues: Iterable[Dialogue]) -> None:
        explicit: list[Episode] = []
        grouped: Counter[tuple[str, str]] = Counter()
        for dialogue in dialogues:
            previous: Binding | None = None
            for index, turn in enumerate(dialogue.turns):
                current = self.current_binding(turn)
                if index == 0:
                    explicit.append(Episode(turn.text, turn.before, turn.after))
                    previous = current
                    if previous is None:
                        self.failures.append(turn.text)
                    continue
                if previous is None:
                    self.failures.append(turn.text)
                    continue
                operator = self.relation(previous, current, turn)
                if operator is None:
                    self.failures.append(turn.text)
                    continue
                grouped[(operator, self.abstract(turn.text))] += 1
                if current is not None:
                    previous = current
        self.base.fit(explicit)
        self.patterns = [DiscoursePattern(op, abstract, count) for (op, abstract), count in grouped.items()]
        self.pattern_grams = [ngrams(pattern.abstract) for pattern in self.patterns]
        operator_grams: dict[str, Counter[str]] = defaultdict(Counter)
        for (operator, abstract), count in grouped.items():
            for gram, value in ngrams(abstract, (2, 3, 4)).items():
                operator_grams[operator][gram] += value * count
        vocabulary = set().union(*(set(values) for values in operator_grams.values()))
        weights: dict[str, dict[str, float]] = {}
        for operator, own in operator_grams.items():
            other: Counter[str] = Counter()
            for candidate, values in operator_grams.items():
                if candidate != operator:
                    other.update(values)
            own_total, other_total = sum(own.values()), sum(other.values())
            size = max(1, len(vocabulary))
            operator_weights: dict[str, float] = {}
            for gram, count in own.items():
                probability = (count + 1.0) / (own_total + size)
                alternative = (other.get(gram, 0) + 1.0) / (other_total + size)
                weight = math.log(probability / alternative)
                if weight > 0.35 and len(gram) >= 2:
                    operator_weights[gram] = weight
            weights[operator] = operator_weights
        self.cue_weights = weights

    def reset(self) -> None:
        self.context = None

    def predict_turn(self, text: str, before: str) -> tuple[str, dict[str, object]]:
        explicit, trace = self.base.predict(text, before)
        if trace.get("operator") == "TRANSFER" and explicit != before:
            binding = trace["binding"]
            assert isinstance(binding, dict)
            self.context = Binding(
                str(binding["src"]), str(binding["dst"]), str(binding["item"]), int(binding["amount"])
            )
            return explicit, {"layer": "base", **trace}
        if self.context is None:
            return before, {"layer": "discourse", "operator": "ABSTAIN", "reason": "no-context"}
        abstract = self.abstract(text)
        multi = ngrams(abstract, (2, 3, 4))
        cue_scores: dict[str, float] = {}
        for operator, weights in self.cue_weights.items():
            hits = sorted((weight for gram, weight in weights.items() if multi.get(gram)), reverse=True)
            cue_scores[operator] = statistics.mean(hits[:6]) if hits else 0.0
        ranked: list[tuple[float, DiscoursePattern]] = []
        for pattern, grams in zip(self.patterns, self.pattern_grams):
            score = 0.30 * cosine(ngrams(abstract), grams) + 0.70 * cue_scores.get(pattern.operator, 0.0)
            ranked.append((score, pattern))
        if not ranked:
            return before, {"layer": "discourse", "operator": "ABSTAIN"}
        score, pattern = max(ranked, key=lambda row: row[0])
        if score < 0.30:
            return before, {"layer": "discourse", "operator": "ABSTAIN", "score": score}
        previous = self.context
        if pattern.operator == "NOOP":
            return before, {"layer": "discourse", "operator": "NOOP", "score": score}
        number = NUMBER.search(text)
        amount = int(number.group(1)) if number else previous.amount
        current = (
            Binding(previous.src, previous.dst, previous.item, amount)
            if pattern.operator == "REUSE"
            else Binding(previous.dst, previous.src, previous.item, amount)
        )
        output, base_trace = self.base.apply(before, current)
        if output != before:
            self.context = current
        return output, {
            "layer": "discourse",
            "operator": pattern.operator,
            "score": score,
            "binding": asdict(current),
            "base_trace": base_trace,
        }
