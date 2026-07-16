from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .cic_choice_data import (
    ChoiceExample,
    choice_features,
    legacy_choice_features,
    stable_choice_split,
)


def _dot(
    weights: Mapping[int, int | float] | np.ndarray,
    features: Mapping[int, int | float],
) -> float:
    if isinstance(weights, np.ndarray):
        return float(
            sum(float(weights[index]) * float(value) for index, value in features.items())
        )
    return float(
        sum(float(weights.get(index, 0)) * float(value) for index, value in features.items())
    )


@dataclass
class LegacyChoiceMechanism:
    weights: dict[int, float]
    dimensions: int
    epochs: int

    def predict(self, stem: str, options: Sequence[str]) -> tuple[int, int]:
        scores = [
            _dot(
                self.weights,
                legacy_choice_features(
                    stem, option, index, dimensions=self.dimensions
                ),
            )
            for index, option in enumerate(options)
        ]
        return int(np.argmax(np.asarray(scores))), len(options)


def train_legacy_choice_mechanism(
    rows: Sequence[ChoiceExample],
    *,
    epochs: int,
    dimensions: int = 16384,
    seed: int = 0,
) -> LegacyChoiceMechanism:
    weights = np.zeros(dimensions, dtype=np.float32)
    cached = [
        [
            legacy_choice_features(
                row.stem, option, index, dimensions=dimensions
            )
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
            scores = [_dot(weights, features) for features in features_by_option]
            predicted = int(np.argmax(np.asarray(scores)))
            gold = rows[row_index].answer_index
            if predicted == gold:
                continue
            for index, value in features_by_option[gold].items():
                weights[index] += rate * value
            for index, value in features_by_option[predicted].items():
                weights[index] -= rate * value
    nonzero = np.flatnonzero(weights)
    return LegacyChoiceMechanism(
        {int(index): float(weights[index]) for index in nonzero},
        dimensions,
        epochs,
    )


@dataclass
class RawChoiceMechanism:
    weights: dict[int, float]
    dimensions: int
    epochs: int
    aggressiveness: float = 0.25
    averaged: bool = True
    hash_replicas: int = 1
    relation_scope: str = "tail"

    def predict(self, stem: str, options: Sequence[str]) -> tuple[int, int]:
        scores = [
            _dot(
                self.weights,
                choice_features(
                    stem,
                    option,
                    index,
                    dimensions=self.dimensions,
                    hash_replicas=self.hash_replicas,
                    relation_scope=self.relation_scope,
                ),
            )
            for index, option in enumerate(options)
        ]
        return int(np.argmax(np.asarray(scores))), len(options)


def _difference(
    positive: Mapping[int, float], negative: Mapping[int, float]
) -> dict[int, float]:
    result = dict(positive)
    for index, value in negative.items():
        result[index] = result.get(index, 0.0) - value
        if abs(result[index]) < 1e-12:
            result.pop(index)
    return result


def train_choice_mechanism(
    rows: Sequence[ChoiceExample],
    *,
    epochs: int,
    dimensions: int = 32768,
    seed: int = 0,
    aggressiveness: float = 0.25,
    hash_replicas: int = 1,
    relation_scope: str = "tail",
) -> RawChoiceMechanism:
    """Train an averaged passive-aggressive option ranker.

    Multiple independent hashes occupy disjoint vector blocks. relation_scope
    controls whether fixed-cost question/option relations are drawn from the
    input tail or spread across the complete input.
    """

    weights = np.zeros(dimensions, dtype=np.float32)
    totals = np.zeros(dimensions, dtype=np.float64)
    timestamps = np.zeros(dimensions, dtype=np.int64)
    cached = [
        [
            choice_features(
                row.stem,
                option,
                index,
                dimensions=dimensions,
                hash_replicas=hash_replicas,
                relation_scope=relation_scope,
            )
            for index, option in enumerate(row.options)
        ]
        for row in rows
    ]
    generator = random.Random(seed)
    step = 0
    for _epoch in range(epochs):
        order = list(range(len(rows)))
        generator.shuffle(order)
        for row_index in order:
            step += 1
            features_by_option = cached[row_index]
            scores = [_dot(weights, features) for features in features_by_option]
            gold = rows[row_index].answer_index
            strongest_wrong = max(
                (index for index in range(len(scores)) if index != gold),
                key=lambda index: scores[index],
            )
            margin = scores[gold] - scores[strongest_wrong]
            if margin >= 1.0:
                continue
            delta = _difference(
                features_by_option[gold], features_by_option[strongest_wrong]
            )
            squared_norm = sum(value * value for value in delta.values())
            tau = min(
                aggressiveness,
                (1.0 - margin) / (squared_norm + 1e-12),
            )
            for index, value in delta.items():
                totals[index] += (step - timestamps[index]) * float(weights[index])
                timestamps[index] = step
                weights[index] += tau * value

    if step:
        totals += (step + 1 - timestamps) * weights
        averaged = totals / (step + 1)
    else:
        averaged = weights.astype(np.float64)
    nonzero = np.flatnonzero(np.abs(averaged) > 1e-9)
    return RawChoiceMechanism(
        weights={int(index): float(averaged[index]) for index in nonzero},
        dimensions=dimensions,
        epochs=epochs,
        aggressiveness=aggressiveness,
        averaged=True,
        hash_replicas=hash_replicas,
        relation_scope=relation_scope,
    )


def choice_accuracy(
    model: LegacyChoiceMechanism | RawChoiceMechanism | "QuantizedChoiceMechanism",
    rows: Sequence[ChoiceExample],
) -> tuple[int, int, float]:
    correct = 0
    work = 0
    for row in rows:
        predicted, checked = model.predict(row.stem, row.options)
        correct += int(predicted == row.answer_index)
        work += checked
    return correct, len(rows), work / len(rows) if rows else 0.0


def choose_legacy_choice_epochs(
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
        model = train_legacy_choice_mechanism(
            inner_train, epochs=epochs, dimensions=dimensions
        )
        correct, total, _work = choice_accuracy(model, validation)
        scores[epochs] = correct / total if total else 0.0
    selected = max(candidates, key=lambda value: (scores[value], -value))
    return selected, scores


def choose_choice_epochs(
    rows: Sequence[ChoiceExample],
    *,
    candidates: Sequence[int] = (1, 2, 3, 4, 6),
    dimensions: int = 32768,
    aggressiveness: float = 0.25,
    hash_replicas: int = 1,
    relation_scope: str = "tail",
) -> tuple[int, dict[int, float]]:
    inner_train, validation = stable_choice_split(
        rows, test_threshold=1500, namespace="inner:"
    )
    scores: dict[int, float] = {}
    for epochs in candidates:
        model = train_choice_mechanism(
            inner_train,
            epochs=epochs,
            dimensions=dimensions,
            aggressiveness=aggressiveness,
            hash_replicas=hash_replicas,
            relation_scope=relation_scope,
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
    hash_replicas: int = 1
    relation_scope: str = "tail"

    @classmethod
    def from_raw(
        cls,
        model: RawChoiceMechanism,
        *,
        quantization_limit: int = 63,
        top_weights: int = 8192,
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
        return cls(
            dimensions=model.dimensions,
            scale=scale,
            weights=quantized,
            hash_replicas=model.hash_replicas,
            relation_scope=model.relation_scope,
        )

    def predict(self, stem: str, options: Sequence[str]) -> tuple[int, int]:
        scores = [
            self.scale
            * _dot(
                self.weights,
                choice_features(
                    stem,
                    option,
                    index,
                    dimensions=self.dimensions,
                    hash_replicas=self.hash_replicas,
                    relation_scope=self.relation_scope,
                ),
            )
            for index, option in enumerate(options)
        ]
        return int(np.argmax(np.asarray(scores))), len(options)
