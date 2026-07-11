from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
import re
import unicodedata
from typing import Iterable


PROGRAMS = ("ADD", "SUB", "MUL", "DIV", "PERCENT_OF")


@dataclass(frozen=True)
class MathTrace:
    raw: str
    answer: Fraction

    @classmethod
    def from_value(cls, raw: str, answer: int | Fraction) -> "MathTrace":
        return cls(raw, Fraction(answer))


@dataclass(frozen=True)
class MathRule:
    program: str
    feature: str
    support: int


@dataclass(frozen=True)
class MathPrediction:
    program: str | None
    answer: Fraction | None
    numbers: tuple[Fraction, ...]
    feature_reads: int
    matched_rules: int


@dataclass(frozen=True)
class MathProgramGrounder:
    rules: tuple[MathRule, ...]
    training_examples: int

    def predict(self, raw: str) -> MathPrediction:
        numbers = extract_numbers(raw)
        features = raw_features(raw)
        scores = {program: 0 for program in PROGRAMS}
        matched = 0
        index = {rule.feature: rule for rule in self.rules}
        for feature in features:
            rule = index.get(feature)
            if rule is None:
                continue
            matched += 1
            payload = feature.split(":", 1)[1]
            scores[rule.program] += len(payload)
        maximum = max(scores.values())
        winners = [program for program, score in scores.items() if score == maximum and score > 0]
        if len(winners) != 1 or len(numbers) != 2:
            return MathPrediction(None, None, numbers, len(features), matched)
        program = winners[0]
        try:
            answer = evaluate_program(program, numbers)
        except ZeroDivisionError:
            return MathPrediction(program, None, numbers, len(features), matched)
        return MathPrediction(program, answer, numbers, len(features), matched)

    @property
    def description_bits(self) -> int:
        program_bits = max(1, math.ceil(math.log2(len(PROGRAMS))))
        count_bits = max(1, math.ceil(math.log2(self.training_examples + 1)))
        pointer_bits = max(1, math.ceil(math.log2(len(self.rules) + 1)))
        return len(PROGRAMS) * 24 + sum(
            len(rule.feature.encode("utf-8")) * 8
            + program_bits
            + count_bits
            + pointer_bits
            + 8
            for rule in self.rules
        )


def canonical_text(raw: str) -> str:
    text = unicodedata.normalize("NFKC", raw).lower()
    text = text.replace("％", "%")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_numbers(raw: str) -> tuple[Fraction, ...]:
    text = canonical_text(raw)
    values: list[Fraction] = []
    for token in re.findall(r"[-+]?\d+(?:\.\d+)?", text):
        values.append(Fraction(token))
    return tuple(values)


def raw_features(raw: str) -> frozenset[str]:
    text = canonical_text(raw)
    features: set[str] = set()
    for token in text.split():
        features.add(f"w:{token}")
    for japanese in re.findall(r"[ぁ-んァ-ヶ一-龠]+", text):
        for width in range(1, min(6, len(japanese)) + 1):
            for start in range(len(japanese) - width + 1):
                features.add(f"j{width}:{japanese[start:start + width]}")
    for ascii_token in re.findall(r"[a-z_]+", text):
        features.add(f"a:{ascii_token}")
        for width in range(3, min(7, len(ascii_token)) + 1):
            for start in range(len(ascii_token) - width + 1):
                features.add(f"a{width}:{ascii_token[start:start + width]}")
    if "%" in text or "パーセント" in text:
        features.add("s:percent")
    return frozenset(features)


def evaluate_program(program: str, numbers: tuple[Fraction, ...]) -> Fraction:
    if len(numbers) != 2:
        raise ValueError("exactly two numbers are required")
    left, right = numbers
    if program == "ADD":
        return left + right
    if program == "SUB":
        return left - right
    if program == "MUL":
        return left * right
    if program == "DIV":
        if right == 0:
            raise ZeroDivisionError
        return left / right
    if program == "PERCENT_OF":
        return left * right / 100
    raise ValueError(program)


def infer_program(trace: MathTrace) -> str:
    numbers = extract_numbers(trace.raw)
    if len(numbers) != 2:
        raise ValueError(f"trace does not contain two numbers: {trace.raw!r}")
    matches: list[str] = []
    for program in PROGRAMS:
        try:
            if evaluate_program(program, numbers) == trace.answer:
                matches.append(program)
        except ZeroDivisionError:
            continue
    if len(matches) != 1:
        raise ValueError(f"program is not identifiable for {trace.raw!r}: {matches!r}")
    return matches[0]


def _feature_cost(feature: str) -> float:
    payload = feature.split(":", 1)[1]
    return len(feature.encode("utf-8")) * 8 + 8 + 96.0 / max(1, len(payload) ** 2)


def induce_math_grounder(
    traces: Iterable[MathTrace],
    *,
    minimum_support: int = 2,
) -> MathProgramGrounder:
    items = list(traces)
    if not items:
        raise ValueError("at least one math trace is required")
    labels = {trace.raw: infer_program(trace) for trace in items}
    features = {trace.raw: raw_features(trace.raw) for trace in items}
    rules: list[MathRule] = []

    for program in PROGRAMS:
        positives = [trace.raw for trace in items if labels[trace.raw] == program]
        negatives = [trace.raw for trace in items if labels[trace.raw] != program]
        if not positives:
            raise ValueError(f"program {program} has no examples")
        candidate_features = set().union(*(features[raw] for raw in positives))
        candidates: list[tuple[str, frozenset[str], float]] = []
        for feature in candidate_features:
            covered = frozenset(raw for raw in positives if feature in features[raw])
            contamination = sum(feature in features[raw] for raw in negatives)
            if len(covered) < minimum_support or contamination:
                continue
            candidates.append((feature, covered, _feature_cost(feature)))

        uncovered = set(positives)
        while uncovered:
            available = [item for item in candidates if item[1].intersection(uncovered)]
            if not available:
                raise ValueError(f"no stable feature cover for {program}: {sorted(uncovered)!r}")
            best = max(
                available,
                key=lambda item: (
                    len(item[1].intersection(uncovered)) / item[2],
                    len(item[1].intersection(uncovered)),
                    len(item[0]),
                    item[0],
                ),
            )
            rules.append(MathRule(program, best[0], len(best[1])))
            uncovered.difference_update(best[1])

    return MathProgramGrounder(
        tuple(sorted(rules, key=lambda rule: (rule.program, rule.feature))),
        len(items),
    )


def exact_surface_accuracy(training: Iterable[MathTrace], validation: Iterable[MathTrace]) -> float:
    lookup = {canonical_text(trace.raw): trace.answer for trace in training}
    items = list(validation)
    return sum(lookup.get(canonical_text(trace.raw)) == trace.answer for trace in items) / len(items)


def program_accuracy(grounder: MathProgramGrounder, validation: Iterable[MathTrace]) -> float:
    items = list(validation)
    return sum(grounder.predict(trace.raw).answer == trace.answer for trace in items) / len(items)
