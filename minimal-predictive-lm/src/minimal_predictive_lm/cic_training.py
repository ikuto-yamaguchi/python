from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from .cic_expr import Expression, extract_numbers, synthesize_expressions
from .cic_features import hashed_features, sparse_dot


@dataclass(frozen=True)
class MathExample:
    question: str
    answer: int


@dataclass(frozen=True)
class CandidateExample:
    example: MathExample
    candidates: tuple[Expression, ...]


def load_mawps(path: str | Path) -> list[MathExample]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    result: list[MathExample] = []
    for row in rows:
        try:
            exact_answer = Fraction(str(row["answer"]))
        except (KeyError, ValueError, ZeroDivisionError):
            continue
        # CIC-001 currently emits integer answers only. Fractional labels must not
        # be silently truncated because that corrupts both training and evaluation.
        if exact_answer.denominator != 1:
            continue
        result.append(MathExample(str(row["question"]), exact_answer.numerator))
    return result


def compile_candidates(examples: Iterable[MathExample]) -> tuple[list[CandidateExample], int]:
    compiled: list[CandidateExample] = []
    expansions = 0
    for example in examples:
        synthesis = synthesize_expressions(example.question, example.answer)
        expansions += synthesis.expansions
        if synthesis.expressions:
            compiled.append(CandidateExample(example, synthesis.expressions))
    return compiled, expansions


def stable_outer_split(
    rows: Sequence[MathExample],
    *,
    test_threshold: int = 2000,
) -> tuple[list[MathExample], list[MathExample]]:
    """Split raw labelled rows before any answer-driven program synthesis."""
    train: list[MathExample] = []
    test: list[MathExample] = []
    for row in rows:
        code = int(hashlib.sha256(row.question.encode()).hexdigest(), 16) % 10000
        (test if code < test_threshold else train).append(row)
    return train, test


def stable_inner_split(
    rows: Sequence[CandidateExample],
    *,
    validation_threshold: int = 1500,
) -> tuple[list[CandidateExample], list[CandidateExample]]:
    train: list[CandidateExample] = []
    validation: list[CandidateExample] = []
    for row in rows:
        code = int(
            hashlib.sha256(("validation:" + row.example.question).encode()).hexdigest(), 16
        ) % 10000
        (validation if code < validation_threshold else train).append(row)
    return train, validation


def _choose_labels(
    rows: Sequence[CandidateExample],
    *,
    reuse_strength: float = 1.5,
) -> tuple[list[str], dict[str, Expression]]:
    support: Counter[str] = Counter()
    expressions: dict[str, Expression] = {}
    for row in rows:
        for rank, expression in enumerate(row.candidates):
            support[expression.key] += 1.0 / (rank + 1)
            expressions[expression.key] = expression
    labels: list[str] = []
    for row in rows:
        chosen = min(
            row.candidates,
            key=lambda expression: (
                expression.cost - reuse_strength * math.log2(1.0 + support[expression.key]),
                expression.key,
            ),
        )
        labels.append(chosen.key)
    return labels, expressions


@dataclass
class RawMechanismModel:
    weights: dict[str, dict[int, float]]
    expressions: dict[str, Expression]
    dimensions: int
    epochs: int

    def predict(self, question: str) -> tuple[int | None, str | None, int]:
        features = hashed_features(question, dimensions=self.dimensions)
        numbers = extract_numbers(question)
        best: tuple[float, int, str] | None = None
        checked = 0
        for key, weights in self.weights.items():
            value = self.expressions[key].evaluate(numbers)
            if value is None or value.denominator != 1:
                continue
            checked += 1
            score = sparse_dot(weights, features)
            candidate = (score, int(value), key)
            if best is None or candidate[0] > best[0]:
                best = candidate
        if best is None:
            return None, None, checked
        return best[1], best[2], checked


def train_raw_model(
    rows: Sequence[CandidateExample],
    *,
    epochs: int,
    dimensions: int = 4096,
    seed: int = 0,
) -> RawMechanismModel:
    labels, expressions = _choose_labels(rows)
    classes = sorted(set(labels))
    class_index = {key: index for index, key in enumerate(classes)}
    counts = Counter(labels)
    feature_rows = [hashed_features(row.example.question, dimensions=dimensions) for row in rows]
    weights = np.zeros((len(classes), dimensions), dtype=np.float32)
    for key, count in counts.items():
        weights[class_index[key], 0] = math.log(count + 1.0)
    generator = random.Random(seed)
    for epoch in range(epochs):
        order = list(range(len(rows)))
        generator.shuffle(order)
        learning_rate = 0.5 / (1.0 + 0.2 * epoch)
        for row_index in order:
            features = feature_rows[row_index]
            indices = np.fromiter(features.keys(), dtype=np.int32)
            values = np.fromiter(features.values(), dtype=np.float32)
            scores = weights[:, indices] @ values
            predicted_index = int(np.argmax(scores))
            gold_index = class_index[labels[row_index]]
            if predicted_index == gold_index:
                continue
            delta = learning_rate * values
            weights[gold_index, indices] += delta
            weights[predicted_index, indices] -= delta
    sparse_weights: dict[str, dict[int, float]] = {}
    for key, row_index in class_index.items():
        nonzero = np.flatnonzero(weights[row_index])
        sparse_weights[key] = {
            int(index): float(weights[row_index, index]) for index in nonzero
        }
    return RawMechanismModel(
        sparse_weights,
        {key: expressions[key] for key in classes},
        dimensions,
        epochs,
    )


def accuracy(model: RawMechanismModel, rows: Sequence[CandidateExample]) -> tuple[int, int, float]:
    correct = 0
    work = 0
    for row in rows:
        prediction, _mechanism, checked = model.predict(row.example.question)
        work += checked
        correct += int(prediction == row.example.answer)
    return correct, len(rows), work / len(rows) if rows else 0.0


def choose_epochs(
    rows: Sequence[CandidateExample],
    *,
    candidates: Sequence[int] = (1, 2, 3, 4, 5, 6),
    dimensions: int = 4096,
) -> tuple[int, dict[int, float]]:
    inner_train, validation = stable_inner_split(rows)
    scores: dict[int, float] = {}
    for epochs in candidates:
        model = train_raw_model(inner_train, epochs=epochs, dimensions=dimensions)
        correct, total, _work = accuracy(model, validation)
        scores[epochs] = correct / total if total else 0.0
    selected = max(candidates, key=lambda value: (scores[value], -value))
    return selected, scores
