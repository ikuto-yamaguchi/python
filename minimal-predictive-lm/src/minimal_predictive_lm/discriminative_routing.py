from __future__ import annotations

from dataclasses import dataclass
import itertools
import json
from typing import Iterable

from .generic_algebra import (
    AlgebraPrediction,
    ExpressionAlgebra,
    GenericAlgebraModel,
    OrderingExample,
    _WORD_RE,
    _apply_ordering,
    extract_sequence,
    induce_sequence_ordering,
)


def _bits(payload: object) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ) * 8


def _prefix_words(prompt: str) -> frozenset[str]:
    prefix = prompt.rsplit(":", 1)[0]
    return frozenset(word.casefold() for word in _WORD_RE.findall(prefix))


@dataclass(frozen=True)
class NegativeRoutingExample:
    prompt: str


@dataclass(frozen=True)
class DiscriminativeSequenceOrderingProgram:
    mode: str
    required_cues: tuple[str, ...]
    positive_examples: int
    negative_examples: int
    candidate_cue_sets: int

    def apply(self, prompt: str) -> str | None:
        words = _prefix_words(prompt)
        if not set(self.required_cues).issubset(words):
            return None
        items = extract_sequence(prompt)
        if len(items) < 2:
            return None
        return " ".join(_apply_ordering(self.mode, items))

    def render(self) -> object:
        return {
            "mode": self.mode,
            "required_cues": list(self.required_cues),
            "positive_examples": self.positive_examples,
            "negative_examples": self.negative_examples,
        }

    @property
    def description_bits(self) -> int:
        return _bits(self.render())


@dataclass(frozen=True)
class GuardedAlgebraModel:
    expression: ExpressionAlgebra
    ordering: DiscriminativeSequenceOrderingProgram
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


def induce_discriminative_sequence_ordering(
    positive_examples: Iterable[OrderingExample],
    negative_examples: Iterable[NegativeRoutingExample],
    *,
    maximum_cues: int = 3,
) -> DiscriminativeSequenceOrderingProgram:
    positives = tuple(positive_examples)
    negatives = tuple(negative_examples)
    if len(positives) < 2:
        raise ValueError("at least two positive ordering examples are required")
    if not negatives:
        raise ValueError("at least one negative routing example is required")

    base = induce_sequence_ordering(positives)
    positive_word_sets = tuple(_prefix_words(row.prompt) for row in positives)
    common = set.intersection(*(set(words) for words in positive_word_sets))
    negative_word_sets = tuple(_prefix_words(row.prompt) for row in negatives)

    candidates: list[tuple[str, ...]] = []
    evaluated = 0
    ordered_common = tuple(sorted(common))
    for size in range(1, min(maximum_cues, len(ordered_common)) + 1):
        for cues in itertools.combinations(ordered_common, size):
            evaluated += 1
            if all(set(cues).issubset(words) for words in positive_word_sets) and not any(
                set(cues).issubset(words) for words in negative_word_sets
            ):
                candidates.append(cues)
    if not candidates:
        raise ValueError("no cue conjunction separates ordering from negative prompts")
    selected = min(candidates, key=lambda cues: (_bits(list(cues)), len(cues), cues))
    return DiscriminativeSequenceOrderingProgram(
        base.mode,
        selected,
        len(positives),
        len(negatives),
        evaluated,
    )


def replace_ordering_with_discriminative_router(
    base: GenericAlgebraModel,
    positive_examples: Iterable[OrderingExample],
    negative_examples: Iterable[NegativeRoutingExample],
) -> GuardedAlgebraModel:
    positives = tuple(positive_examples)
    negatives = tuple(negative_examples)
    return GuardedAlgebraModel(
        base.expression,
        induce_discriminative_sequence_ordering(positives, negatives),
        base.calibration_examples + len(negatives),
    )
