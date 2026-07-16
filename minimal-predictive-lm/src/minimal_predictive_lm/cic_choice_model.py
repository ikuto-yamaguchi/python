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

CompactVector = tuple[np.ndarray, np.ndarray]


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


def _compact(features: Mapping[int, int | float]) -> CompactVector:
    return (
        np.fromiter(features.keys(), dtype=np.int32, count=len(features)),
        np.fromiter(features.values(), dtype=np.float32, count=len(features)),
    )


def _compact_dot(weights: np.ndarray, features: CompactVector) -> float:
    indices, values = features
    return float(weights[indices] @ values) if len(indices) else 0.0


def _compact_difference(positive: CompactVector, negative: CompactVector) -> CompactVector:
    positive_indices, positive_values = positive
    negative_indices, negative_values = negative
    indices = np.concatenate((positive_indices, negative_indices))
    values = np.concatenate((positive_values, -negative_values))
    unique, inverse = np.unique(indices, return_inverse=True)
    reduced = np.zeros(len(unique), dtype=np.float32)
    np.add.at(reduced, inverse, values)
    keep = np.abs(reduced) > 1e-12
    return unique[keep].astype(np.int32, copy=False), reduced[keep]


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

    Feature dictionaries are immediately packed into int32/float32 arrays.
    This keeps the exact sparse update semantics while avoiding the multi-GB
    Python-dict cache that dominated CIC-007's first multidomain run.
    """

    weights = np.zeros(dimensions, dtype=np.float32)
    totals = np.zeros(dimensions, dtype=np.float64)
    timestamps = np.zeros(dimensions, dtype=np.int64)
    cached: list[list[CompactVector]] = [
        [
            _compact(
                choice_features(
                    row.stem,
                    option,
                    index,
                    dimensions=dimensions,
                    hash_replicas=hash_replicas,
                    relation_scope=relation_scope,
                )
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
            scores = [_compact_dot(weights, features) for features in features_by_option]
            gold = rows[row_index].answer_index
            strongest_wrong = max(
                (index for index in range(len(scores)) if index != gold),
                key=lambda index: scores[index],
            )
            margin = scores[gold] - scores[strongest_wrong]
            if margin >= 1.0:
                continue
            delta_indices, delta_values = _compact_difference(
                features_by_option[gold], features_by_option[strongest_wrong]
            )
            squared_norm = float(delta_values @ delta_values)
            tau = min(
                aggressiveness,
                (1.0 - margin) / (squared_norm + 1e-12),
            )
            totals[delta_indices] += (
                step - timestamps[delta_indices]
            ) * weights[delta_indices]
            timestamps[delta_indices] = step
            weights[delta_indices] += tau * delta_values

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
