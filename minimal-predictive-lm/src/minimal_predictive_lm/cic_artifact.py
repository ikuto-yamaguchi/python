from __future__ import annotations

import json
import zlib
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Sequence

from .cic_expr import Expression, extract_numbers, parse_expression
from .cic_features import hashed_features, sparse_dot
from .cic_training import CandidateExample, RawMechanismModel


@dataclass(frozen=True)
class QuantizedMechanism:
    scale: float
    weights: dict[int, int]
    expression: str


@dataclass
class CICArtifact:
    dimensions: int
    mechanisms: dict[str, QuantizedMechanism]
    metadata: dict[str, object]

    @cached_property
    def parsed_expressions(self) -> dict[str, Expression]:
        return {key: parse_expression(row.expression) for key, row in self.mechanisms.items()}

    @classmethod
    def from_raw(
        cls,
        model: RawMechanismModel,
        *,
        top_weights: int | None = None,
        quantization_limit: int = 127,
        metadata: dict[str, object] | None = None,
    ) -> "CICArtifact":
        mechanisms: dict[str, QuantizedMechanism] = {}
        for key, row in model.weights.items():
            items = sorted(row.items(), key=lambda item: abs(item[1]), reverse=True)
            if top_weights is not None:
                items = items[:top_weights]
            maximum = max((abs(value) for _index, value in items), default=0.0)
            scale = maximum / quantization_limit if maximum else 1.0
            quantized = {
                index: int(round(value / scale))
                for index, value in items
                if int(round(value / scale)) != 0
            }
            mechanisms[key] = QuantizedMechanism(
                scale, quantized, model.expressions[key].key
            )
        return cls(model.dimensions, mechanisms, metadata or {})

    def predict(self, question: str) -> tuple[int | None, str | None, int]:
        features = hashed_features(question, dimensions=self.dimensions)
        numbers = extract_numbers(question)
        best: tuple[float, int, str] | None = None
        checked = 0
        for key, mechanism in self.mechanisms.items():
            value = self.parsed_expressions[key].evaluate(numbers)
            if value is None or value.denominator != 1:
                continue
            checked += 1
            score = mechanism.scale * sparse_dot(mechanism.weights, features)
            candidate = (score, int(value), key)
            if best is None or candidate[0] > best[0]:
                best = candidate
        if best is None:
            return None, None, checked
        return best[1], best[2], checked

    def to_bytes(self) -> bytes:
        payload = {
            "format": "cic-001",
            "dimensions": self.dimensions,
            "metadata": self.metadata,
            "mechanisms": {
                key: {
                    "scale": row.scale,
                    "weights": {str(index): value for index, value in row.weights.items()},
                    "expression": row.expression,
                }
                for key, row in self.mechanisms.items()
            },
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return zlib.compress(raw, level=9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "CICArtifact":
        payload = json.loads(zlib.decompress(data))
        mechanisms = {
            key: QuantizedMechanism(
                float(row["scale"]),
                {int(index): int(value) for index, value in row["weights"].items()},
                str(row["expression"]),
            )
            for key, row in payload["mechanisms"].items()
        }
        return cls(
            int(payload["dimensions"]),
            mechanisms,
            dict(payload.get("metadata", {})),
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "CICArtifact":
        return cls.from_bytes(Path(path).read_bytes())


def artifact_accuracy(
    artifact: CICArtifact,
    rows: Sequence[CandidateExample],
) -> tuple[int, int, float]:
    correct = 0
    work = 0
    for row in rows:
        prediction, _mechanism, checked = artifact.predict(row.example.question)
        work += checked
        correct += int(prediction == row.example.answer)
    return correct, len(rows), work / len(rows) if rows else 0.0
