from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .cic_choice_data import (
    ChoiceExample,
    choice_features,
    stable_choice_split,
)


def _dot(weights: Mapping[int, int | float], features: Mapping[int, int]) -> float:
    return float(sum(weights.get(index, 0) * value for index, value in features.items()))


@dataclass
class RawChoiceMechanism:
    weights: dict[int, float]
    dimensions: int
    epochs: int

    def predict(self, stem: str, options: Sequence[str]) -> tuple[int, int]:
        scores = [
            _dot(
                self.weights,
                choice_features(stem, option, index, dimensions=self.dimensions),
            )
            for index, option in enumerate(options)
        ]
        return int(np.argmax(np.asarray(scores))), len(options)


def train_choice_mechanism(
    rows: Sequence[ChoiceExample],
    *,
    epochs: int,
    dimensions: int = 16384,
    seed: int = 0,
) -> RawChoiceMechanism:
    weights = np.zeros(dimensions, dtype=np.float32)
    cached = [
        [
            choice_features(row.stem, option, index, dimensions=dimensions)
            for index, option in enumerate(row.options)
        ]
        for row in rows
    ]
    generator = random.Random(seed)
    for epoch in range(epochs):
        order = list(range(len(rows)))
        generator.shuffle(order)
        rate = 0.35 / (1.0 + 0.15 * epoch)
        for row_index in order:
            features_by_option = cached[row_index]
            scores = [
                sum(weights[index] * value for index, value in features.items())
                for features in features_by_option
            ]
            predicted = int(np.argmax(np.asarray(scores)))
            gold = rows[row_index].answer_index
            if predicted == gold:
                continue
            for index, value in features_by_option[gold].items():
                weights[index] += rate * value
            for index, value in features_by_option[predicted].items():
                weights[index] -= rate * value
    nonzero = np.flatnonzero(weights)
    return RawChoiceMechanism(
        {int(index): float(weights[index]) for index in nonzero},
        dimensions,
        epochs,
    )


def choice_accuracy(
    model: RawChoiceMechanism | "QuantizedChoiceMechanism",
    rows: Sequence[ChoiceExample],
) -> tuple[int, int, float]:
    correct = 0
    work = 0
    for row in rows:
        predicted, checked = model.predict(row.stem, row.options)
        correct += int(predicted == row.answer_index)
        work += checked
    return correct, len(rows), work / len(rows) if rows else 0.0


def choose_choice_epochs(
    rows: Sequence[ChoiceExample],
    *,
    candidates: Sequence[int] = (1, 2, 3, 4, 6, 8),
    dimensions: int = 16384,
) -> tuple[int, dict[int, float]]:
    inner_train, validation = stable_choice_split(
        rows, test_threshold=1500, namespace="inner:"
    )
    scores: dict[int, float] = {}
    for epochs in candidates:
        model = train_choice_mechanism(
            inner_train, epochs=epochs, dimensions=dimensions
        )
        correct, total, _work = choice_accuracy(model, validation)
        scores[epochs] = correct / total if total else 0.0
    selected = max(candidates, key=lambda value: (scores[value], -value))
    return selected, scores


@dataclass(frozen=True)
class QuantizedChoiceMechanism:
    dimensions: int
    scale: float
    weights: dict[int, int]

    @classmethod
    def from_raw(
        cls,
        model: RawChoiceMechanism,
        *,
        quantization_limit: int = 31,
        top_weights: int = 4096,
    ) -> "QuantizedChoiceMechanism":
        items = sorted(
            model.weights.items(), key=lambda item: abs(item[1]), reverse=True
        )[:top_weights]
        maximum = max((abs(value) for _index, value in items), default=0.0)
        scale = maximum / quantization_limit if maximum else 1.0
        quantized = {
            index: int(round(value / scale))
            for index, value in items
            if int(round(value / scale)) != 0
        }
        return cls(model.dimensions, scale, quantized)

    def predict(self, stem: str, options: Sequence[str]) -> tuple[int, int]:
        scores = [
            self.scale
            * _dot(
                self.weights,
                choice_features(stem, option, index, dimensions=self.dimensions),
            )
            for index, option in enumerate(options)
        ]
        return int(np.argmax(np.asarray(scores))), len(options)
