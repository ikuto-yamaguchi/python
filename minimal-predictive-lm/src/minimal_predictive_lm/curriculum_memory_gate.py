from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable, Sequence
import zlib


@dataclass(frozen=True)
class GateObservation:
    example_id: str
    base_scores: tuple[float, ...]
    memory_scores: tuple[float, ...]
    active_postings: int
    stem_length: int
    option_lengths: tuple[int, ...]
    answer_index: int

    @property
    def base_index(self) -> int:
        return max(range(len(self.base_scores)), key=lambda index: self.base_scores[index])

    @property
    def memory_index(self) -> int:
        return max(range(len(self.memory_scores)), key=lambda index: self.memory_scores[index])


def _margin(scores: Sequence[float]) -> float:
    ordered = sorted(scores, reverse=True)
    return ordered[0] - ordered[1] if len(ordered) > 1 else 0.0


def gate_features(row: GateObservation) -> tuple[float, ...]:
    base_margin = _margin(row.base_scores)
    memory_margin = _margin(row.memory_scores)
    base_top = max(row.base_scores, default=0.0)
    memory_top = max(row.memory_scores, default=0.0)
    mean_option = sum(row.option_lengths) / max(1, len(row.option_lengths))
    option_range = max(row.option_lengths, default=0) - min(row.option_lengths, default=0)
    posting_log = math.log1p(row.active_postings)
    return (
        base_margin,
        memory_margin,
        memory_margin - base_margin,
        base_margin * memory_margin,
        base_margin * base_margin,
        memory_margin * memory_margin,
        base_top,
        memory_top,
        posting_log,
        posting_log * memory_margin,
        min(4.0, row.stem_length / 100.0),
        min(4.0, mean_option / 20.0),
        min(4.0, option_range / 20.0),
    )


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        exponent = math.exp(-min(value, 40.0))
        return 1.0 / (1.0 + exponent)
    exponent = math.exp(max(value, -40.0))
    return exponent / (1.0 + exponent)


@dataclass(frozen=True)
class QuantizedCurriculumGate:
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[int, ...]
    weight_scale: float
    bias: float
    threshold: float
    metadata: dict[str, object]

    FORMAT = "quantized-curriculum-trust-gate-001"

    def probability(self, row: GateObservation) -> float:
        raw = gate_features(row)
        normalized = tuple(
            (value - mean) / scale
            for value, mean, scale in zip(raw, self.means, self.scales)
        )
        logit = self.bias + self.weight_scale * sum(
            weight * value for weight, value in zip(self.weights, normalized)
        )
        return _sigmoid(logit)

    def choose_index(self, row: GateObservation) -> int:
        if row.base_index == row.memory_index:
            return row.base_index
        return self.memory_index if self.probability(row) >= self.threshold else row.base_index

    def to_bytes(self) -> bytes:
        payload = {
            "format": self.FORMAT,
            "means": self.means,
            "scales": self.scales,
            "weights": self.weights,
            "weight_scale": self.weight_scale,
            "bias": self.bias,
            "threshold": self.threshold,
            "metadata": self.metadata,
        }
        return zlib.compress(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "QuantizedCurriculumGate":
        payload = json.loads(zlib.decompress(data))
        if payload.get("format") != cls.FORMAT:
            raise ValueError("unsupported curriculum gate format")
        return cls(
            means=tuple(float(value) for value in payload["means"]),
            scales=tuple(float(value) for value in payload["scales"]),
            weights=tuple(int(value) for value in payload["weights"]),
            weight_scale=float(payload["weight_scale"]),
            bias=float(payload["bias"]),
            threshold=float(payload["threshold"]),
            metadata=dict(payload.get("metadata", {})),
        )


def _statistics(rows: Sequence[GateObservation]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    features = [gate_features(row) for row in rows]
    dimensions = len(features[0])
    means = tuple(
        sum(row[index] for row in features) / len(features)
        for index in range(dimensions)
    )
    scales: list[float] = []
    for index, mean in enumerate(means):
        variance = sum((row[index] - mean) ** 2 for row in features) / len(features)
        scales.append(math.sqrt(variance) or 1.0)
    return means, tuple(scales)


def _fit_float(
    rows: Sequence[GateObservation],
    *,
    epochs: int = 180,
    learning_rate: float = 0.08,
    l2: float = 0.002,
) -> tuple[tuple[float, ...], tuple[float, ...], list[float], float]:
    disagreements = [row for row in rows if row.base_index != row.memory_index]
    if not disagreements:
        raise ValueError("curriculum gate needs disagreements")
    means, scales = _statistics(disagreements)
    dimensions = len(means)
    weights = [0.0] * dimensions
    bias = 0.0
    positive = sum(row.memory_index == row.answer_index for row in disagreements)
    negative = len(disagreements) - positive
    positive_weight = len(disagreements) / max(1.0, 2.0 * positive)
    negative_weight = len(disagreements) / max(1.0, 2.0 * negative)

    ordered = sorted(
        disagreements,
        key=lambda row: hashlib.sha256(("gate-order:" + row.example_id).encode()).digest(),
    )
    for epoch in range(epochs):
        rate = learning_rate / math.sqrt(1.0 + epoch / 12.0)
        for row in ordered:
            raw = gate_features(row)
            x = tuple(
                (value - mean) / scale
                for value, mean, scale in zip(raw, means, scales)
            )
            target = 1.0 if row.memory_index == row.answer_index else 0.0
            sample_weight = positive_weight if target else negative_weight
            prediction = _sigmoid(bias + sum(w * value for w, value in zip(weights, x)))
            error = sample_weight * (target - prediction)
            bias += rate * error
            for index in range(dimensions):
                weights[index] += rate * (error * x[index] - l2 * weights[index])
    return means, scales, weights, bias


def _accuracy(rows: Sequence[GateObservation], model: QuantizedCurriculumGate) -> int:
    return sum(model.choose_index(row) == row.answer_index for row in rows)


def _select_threshold(
    rows: Sequence[GateObservation],
    provisional: QuantizedCurriculumGate,
) -> float:
    candidates = tuple(index / 20.0 for index in range(3, 19))
    return max(
        candidates,
        key=lambda threshold: (
            _accuracy(
                rows,
                QuantizedCurriculumGate(
                    provisional.means,
                    provisional.scales,
                    provisional.weights,
                    provisional.weight_scale,
                    provisional.bias,
                    threshold,
                    provisional.metadata,
                ),
            ),
            threshold,
        ),
    )


def train_gate(
    rows: Sequence[GateObservation],
    *,
    metadata: dict[str, object] | None = None,
) -> QuantizedCurriculumGate:
    means, scales, float_weights, bias = _fit_float(rows)
    maximum = max((abs(value) for value in float_weights), default=1.0)
    weight_scale = maximum / 63.0 if maximum else 1.0
    quantized = tuple(
        max(-63, min(63, int(round(value / weight_scale))))
        for value in float_weights
    )
    provisional = QuantizedCurriculumGate(
        means,
        scales,
        quantized,
        weight_scale,
        bias,
        0.5,
        dict(metadata or {}),
    )
    threshold = _select_threshold(rows, provisional)
    return QuantizedCurriculumGate(
        means,
        scales,
        quantized,
        weight_scale,
        bias,
        threshold,
        dict(metadata or {}),
    )


def stable_fold(example_id: str, folds: int = 5) -> int:
    digest = hashlib.sha256(("curriculum-gate-fold:" + example_id).encode()).digest()
    return int.from_bytes(digest[:8], "little") % folds


def cross_validate_gate(
    rows: Sequence[GateObservation],
    *,
    folds: int = 5,
) -> dict[str, object]:
    predictions: dict[str, int] = {}
    fold_reports: list[dict[str, object]] = []
    for fold in range(folds):
        train = [row for row in rows if stable_fold(row.example_id, folds) != fold]
        test = [row for row in rows if stable_fold(row.example_id, folds) == fold]
        model = train_gate(
            train,
            metadata={"fold": fold, "training_rows": len(train)},
        )
        base_correct = sum(row.base_index == row.answer_index for row in test)
        memory_correct = sum(row.memory_index == row.answer_index for row in test)
        gated_correct = _accuracy(test, model)
        for row in test:
            predictions[row.example_id] = model.choose_index(row)
        fold_reports.append(
            {
                "fold": fold,
                "train_rows": len(train),
                "test_rows": len(test),
                "threshold": model.threshold,
                "base_correct": base_correct,
                "memory_correct": memory_correct,
                "gated_correct": gated_correct,
                "gated_gain_over_base": gated_correct - base_correct,
            }
        )
    base_correct = sum(row.base_index == row.answer_index for row in rows)
    memory_correct = sum(row.memory_index == row.answer_index for row in rows)
    gated_correct = sum(predictions[row.example_id] == row.answer_index for row in rows)
    return {
        "folds": folds,
        "rows": len(rows),
        "base_correct": base_correct,
        "memory_correct": memory_correct,
        "gated_correct": gated_correct,
        "base_accuracy": base_correct / len(rows),
        "memory_accuracy": memory_correct / len(rows),
        "gated_accuracy": gated_correct / len(rows),
        "gated_gain_over_base": gated_correct - base_correct,
        "fold_reports": fold_reports,
        "subject_name_feature_used": False,
        "prompt_text_feature_used": False,
    }
