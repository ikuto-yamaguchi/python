from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Iterable


def _ngrams(text: str, sizes: tuple[int, ...] = (1, 2, 3, 4)) -> set[str]:
    compact = "".join(text.lower().split())
    padded = f"^{compact}$"
    return {
        padded[index : index + size]
        for size in sizes
        for index in range(max(0, len(padded) - size + 1))
    }


@dataclass(frozen=True, slots=True)
class RouteExample:
    text: str
    label: str


@dataclass
class SparseMechanismRouter:
    """Tiny multiclass averaged-perceptron router over hashed character n-grams."""

    buckets: int = 4096
    labels: tuple[str, ...] = ("base", "numeric", "reading", "constraints", "conversation")
    weights: dict[str, dict[int, float]] = field(default_factory=dict)
    bias: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for label in self.labels:
            self.weights.setdefault(label, {})
            self.bias.setdefault(label, 0.0)

    def _feature(self, token: str) -> int:
        digest = hashlib.blake2s(token.encode("utf-8"), digest_size=4).digest()
        return int.from_bytes(digest, "little") % self.buckets

    def features(self, text: str) -> tuple[int, ...]:
        return tuple(sorted({self._feature(token) for token in _ngrams(text)}))

    def scores(self, text: str) -> dict[str, float]:
        features = self.features(text)
        return {
            label: self.bias[label] + sum(self.weights[label].get(feature, 0.0) for feature in features)
            for label in self.labels
        }

    def predict(self, text: str) -> tuple[str, float]:
        scores = self.scores(text)
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        label, top = ranked[0]
        second = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = top - second
        confidence = 1.0 - 1.0 / (1.0 + max(0.0, margin))
        return label, confidence

    def fit(self, examples: Iterable[RouteExample], epochs: int = 20) -> None:
        rows = list(examples)
        unknown = {row.label for row in rows} - set(self.labels)
        if unknown:
            raise ValueError(f"unknown route labels: {sorted(unknown)}")
        for _ in range(epochs):
            mistakes = 0
            for row in rows:
                predicted, _ = self.predict(row.text)
                if predicted == row.label:
                    continue
                mistakes += 1
                features = self.features(row.text)
                self.bias[row.label] += 1.0
                self.bias[predicted] -= 1.0
                for feature in features:
                    self.weights[row.label][feature] = self.weights[row.label].get(feature, 0.0) + 1.0
                    self.weights[predicted][feature] = self.weights[predicted].get(feature, 0.0) - 1.0
            if mistakes == 0:
                break
        self._prune_zeroes()

    def _prune_zeroes(self) -> None:
        for label in self.labels:
            self.weights[label] = {
                feature: value for feature, value in self.weights[label].items() if value != 0.0
            }

    def to_dict(self) -> dict:
        return {
            "buckets": self.buckets,
            "labels": list(self.labels),
            "weights": {
                label: {str(feature): value for feature, value in values.items()}
                for label, values in self.weights.items()
            },
            "bias": self.bias,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SparseMechanismRouter":
        router = cls(
            buckets=int(data.get("buckets", 4096)),
            labels=tuple(str(value) for value in data.get("labels", ())),
        )
        router.weights = {
            str(label): {int(feature): float(value) for feature, value in values.items()}
            for label, values in data.get("weights", {}).items()
        }
        router.bias = {str(label): float(value) for label, value in data.get("bias", {}).items()}
        router.__post_init__()
        return router

    def serialized_bytes(self) -> int:
        return len(json.dumps(self.to_dict(), separators=(",", ":")).encode("utf-8"))


def bootstrap_route_examples() -> list[RouteExample]:
    return [
        RouteExample("12+8×3を計算して", "base"),
        RouteExample("方程式3*x+2=17を解いて", "base"),
        RouteExample("750mをkmへ変換して", "base"),
        RouteExample("時速40kmで3時間進む距離は", "numeric"),
        RouteExample("在庫10個に4箱各3個を加える", "numeric"),
        RouteExample("例から覚えた計算で答えて", "numeric"),
        RouteExample("本文:葵は駅へ行った。問:葵はどこへ行った", "reading"),
        RouteExample("文章を読んで理由を答えて", "reading"),
        RouteExample("本文を根拠に誰が行ったか答えて", "reading"),
        RouteExample("対象:A、B、C。条件:AはBより前。問:順番は", "constraints"),
        RouteExample("条件を全部満たす並びを求めて", "constraints"),
        RouteExample("何通りの順序が可能か", "constraints"),
        RouteExample("私の名前は郁斗です", "conversation"),
        RouteExample("私が好きなものを覚えて", "conversation"),
        RouteExample("さっき話した目標は何", "conversation"),
    ]


def build_bootstrap_router() -> SparseMechanismRouter:
    router = SparseMechanismRouter()
    router.fit(bootstrap_route_examples(), epochs=40)
    return router
