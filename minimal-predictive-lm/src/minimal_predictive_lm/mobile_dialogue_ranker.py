from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
import random
import re
import unicodedata
import zlib
from typing import Iterable, Mapping, Sequence

import numpy as np


_TOKEN_RE = re.compile(r"[一-龯々]+|[ぁ-ん]+|[ァ-ヴー]+|[a-z0-9]+")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text).lower())


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(unicodedata.normalize("NFKC", text).lower()))


def _surface_features(text: str) -> tuple[str, ...]:
    normalized = _normalize(text)
    features: list[str] = []
    for width in (1, 2, 3):
        features.extend(
            normalized[index : index + width]
            for index in range(max(0, len(normalized) - width + 1))
        )
    features.extend("tok:" + token for token in _tokens(text))
    return tuple(features)


def _signed_hash(value: str, dimensions: int, person: bytes) -> tuple[int, float]:
    digest = hashlib.blake2b(
        value.encode("utf-8"), digest_size=8, person=person
    ).digest()
    raw = int.from_bytes(digest, "little")
    return raw % dimensions, 1.0 if raw & (1 << 63) else -1.0


def _normalized_sparse_vector(text: str, dimensions: int) -> dict[int, float]:
    values: dict[int, float] = defaultdict(float)
    for feature in _surface_features(text):
        index, sign = _signed_hash(feature, dimensions, b"mpm-dlg-ret")
        values[index] += sign
    norm = math.sqrt(sum(value * value for value in values.values()))
    if not norm:
        return {}
    return {index: value / norm for index, value in values.items()}


def _pair_features(
    prompt: str,
    response: str,
    dimensions: int,
) -> dict[int, float]:
    values: dict[int, float] = defaultdict(float)
    response_tokens = _tokens(response)
    response_signature = "|".join(response_tokens[:8]) or _normalize(response)[:32]
    for feature in _surface_features(prompt):
        index, sign = _signed_hash(
            "prompt:" + feature + "|response:" + response_signature,
            dimensions,
            b"mpm-dlg-pair",
        )
        values[index] += sign
    prompt_tokens = _tokens(prompt)
    for left in prompt_tokens[:12]:
        for right in response_tokens[:8]:
            index, sign = _signed_hash(
                "cross:" + left + "|" + right,
                dimensions,
                b"mpm-dlg-xrel",
            )
            values[index] += 0.5 * sign
    length_bucket = min(15, len(_normalize(prompt)) // 8)
    index, sign = _signed_hash(
        f"length:{length_bucket}|response:{response_signature}",
        dimensions,
        b"mpm-dlg-len",
    )
    values[index] += sign
    return dict(values)


def _dot(weights: Mapping[int, int | float], features: Mapping[int, float]) -> float:
    return float(
        sum(float(weights.get(index, 0)) * value for index, value in features.items())
    )


@dataclass(frozen=True)
class DialoguePair:
    prompt: str
    response: str


@dataclass(frozen=True)
class DialoguePrediction:
    response: str | None
    confidence: float
    candidates_scored: int
    retrieval_candidates: int


@dataclass(frozen=True)
class DialogueTrainingReport:
    pairs: int
    responses: int
    epochs: int
    updates: int
    quantized_weights: int
    serialized_bytes: int


class QuantizedDialogueRanker:
    """Shared mobile response selector trained from ordinary prompt/response pairs.

    The same hashed pair scorer and retrieval centroids are used for every subject.
    There is no subject name, benchmark label, or domain routing input. The ranker is
    intentionally a bounded candidate selector rather than a claim of open-ended
    generation; it expands the executable chat path from exact memorization to unseen
    paraphrases while the recurrent generator continues to develop.
    """

    FORMAT = "mobile-dialogue-ranker-001"

    def __init__(
        self,
        *,
        responses: Sequence[str],
        pair_dimensions: int,
        retrieval_dimensions: int,
        scale: float,
        weights: Mapping[int, int],
        centroids: Sequence[Mapping[int, int]],
        centroid_scales: Sequence[float],
        max_candidates: int = 24,
    ) -> None:
        if not responses:
            raise ValueError("at least one response is required")
        if len(responses) != len(centroids) or len(responses) != len(centroid_scales):
            raise ValueError("response and centroid counts must match")
        self.responses = tuple(str(value) for value in responses)
        self.pair_dimensions = int(pair_dimensions)
        self.retrieval_dimensions = int(retrieval_dimensions)
        self.scale = float(scale)
        self.weights = {int(index): int(value) for index, value in weights.items()}
        self.centroids = tuple(
            {int(index): int(value) for index, value in centroid.items()}
            for centroid in centroids
        )
        self.centroid_scales = tuple(float(value) for value in centroid_scales)
        self.max_candidates = int(max_candidates)

    @classmethod
    def fit(
        cls,
        pairs: Sequence[DialoguePair | tuple[str, str]],
        *,
        pair_dimensions: int = 65_536,
        retrieval_dimensions: int = 8_192,
        epochs: int = 8,
        aggressiveness: float = 0.20,
        top_weights: int = 32_768,
        centroid_top_features: int = 192,
        quantization_limit: int = 63,
        max_candidates: int = 24,
        seed: int = 0,
    ) -> tuple["QuantizedDialogueRanker", DialogueTrainingReport]:
        normalized_pairs = tuple(
            pair if isinstance(pair, DialoguePair) else DialoguePair(*pair)
            for pair in pairs
        )
        if len(normalized_pairs) < 2:
            raise ValueError("at least two dialogue pairs are required")
        responses = tuple(dict.fromkeys(pair.response for pair in normalized_pairs))
        if len(responses) < 2:
            raise ValueError("at least two distinct responses are required")
        response_index = {response: index for index, response in enumerate(responses)}

        centroid_accumulators: list[dict[int, float]] = [
            defaultdict(float) for _ in responses
        ]
        for pair in normalized_pairs:
            target = response_index[pair.response]
            for index, value in _normalized_sparse_vector(
                pair.prompt, retrieval_dimensions
            ).items():
                centroid_accumulators[target][index] += value

        raw_centroids: list[dict[int, float]] = []
        for values in centroid_accumulators:
            norm = math.sqrt(sum(value * value for value in values.values()))
            normalized = (
                {index: value / norm for index, value in values.items()}
                if norm
                else {}
            )
            raw_centroids.append(
                dict(
                    sorted(
                        normalized.items(),
                        key=lambda item: abs(item[1]),
                        reverse=True,
                    )[:centroid_top_features]
                )
            )

        weights = np.zeros(pair_dimensions, dtype=np.float32)
        generator = random.Random(seed)
        updates = 0
        for _epoch in range(epochs):
            order = list(range(len(normalized_pairs)))
            generator.shuffle(order)
            for row_index in order:
                pair = normalized_pairs[row_index]
                gold = response_index[pair.response]
                features = [
                    _pair_features(pair.prompt, response, pair_dimensions)
                    for response in responses
                ]
                scores = [
                    float(
                        sum(weights[index] * value for index, value in row.items())
                    )
                    for row in features
                ]
                strongest_wrong = max(
                    (index for index in range(len(responses)) if index != gold),
                    key=lambda index: scores[index],
                )
                margin = scores[gold] - scores[strongest_wrong]
                if margin >= 1.0:
                    continue
                delta: dict[int, float] = defaultdict(float)
                for index, value in features[gold].items():
                    delta[index] += value
                for index, value in features[strongest_wrong].items():
                    delta[index] -= value
                squared_norm = sum(value * value for value in delta.values())
                rate = min(
                    aggressiveness,
                    (1.0 - margin) / (squared_norm + 1e-12),
                )
                for index, value in delta.items():
                    weights[index] += rate * value
                updates += 1

        nonzero = np.flatnonzero(np.abs(weights) > 1e-9)
        strongest = sorted(
            ((int(index), float(weights[index])) for index in nonzero),
            key=lambda item: abs(item[1]),
            reverse=True,
        )[:top_weights]
        maximum = max((abs(value) for _index, value in strongest), default=0.0)
        scale = maximum / quantization_limit if maximum else 1.0
        quantized_weights = {
            index: int(round(value / scale))
            for index, value in strongest
            if int(round(value / scale)) != 0
        }

        quantized_centroids: list[dict[int, int]] = []
        centroid_scales: list[float] = []
        for centroid in raw_centroids:
            maximum = max((abs(value) for value in centroid.values()), default=0.0)
            centroid_scale = maximum / 63.0 if maximum else 1.0
            centroid_scales.append(centroid_scale)
            quantized_centroids.append(
                {
                    index: int(round(value / centroid_scale))
                    for index, value in centroid.items()
                    if int(round(value / centroid_scale)) != 0
                }
            )

        model = cls(
            responses=responses,
            pair_dimensions=pair_dimensions,
            retrieval_dimensions=retrieval_dimensions,
            scale=scale,
            weights=quantized_weights,
            centroids=quantized_centroids,
            centroid_scales=centroid_scales,
            max_candidates=max_candidates,
        )
        payload_bytes = len(model.to_bytes())
        return model, DialogueTrainingReport(
            pairs=len(normalized_pairs),
            responses=len(responses),
            epochs=epochs,
            updates=updates,
            quantized_weights=len(quantized_weights),
            serialized_bytes=payload_bytes,
        )

    def _retrieval_scores(self, prompt: str) -> list[float]:
        query = _normalized_sparse_vector(prompt, self.retrieval_dimensions)
        return [
            scale * _dot(centroid, query)
            for centroid, scale in zip(self.centroids, self.centroid_scales)
        ]

    def predict(
        self,
        prompt: str,
        *,
        minimum_confidence: float = 0.08,
    ) -> DialoguePrediction:
        retrieval = self._retrieval_scores(prompt)
        candidate_count = min(self.max_candidates, len(self.responses))
        candidate_indices = sorted(
            range(len(self.responses)),
            key=lambda index: retrieval[index],
            reverse=True,
        )[:candidate_count]
        scored: list[tuple[float, int]] = []
        for index in candidate_indices:
            features = _pair_features(
                prompt, self.responses[index], self.pair_dimensions
            )
            pair_score = self.scale * _dot(self.weights, features)
            scored.append((pair_score + 0.50 * retrieval[index], index))
        scored.sort(reverse=True)
        best_score, best_index = scored[0]
        runner_up = scored[1][0] if len(scored) > 1 else best_score - 1.0
        margin = best_score - runner_up
        retrieval_floor = max(0.0, retrieval[best_index])
        confidence = 0.65 * margin + 0.35 * retrieval_floor
        response = self.responses[best_index] if confidence >= minimum_confidence else None
        return DialoguePrediction(
            response=response,
            confidence=float(confidence),
            candidates_scored=len(scored),
            retrieval_candidates=candidate_count,
        )

    def to_bytes(self) -> bytes:
        payload = {
            "format": self.FORMAT,
            "responses": self.responses,
            "pair_dimensions": self.pair_dimensions,
            "retrieval_dimensions": self.retrieval_dimensions,
            "scale": self.scale,
            "weights": {str(index): value for index, value in self.weights.items()},
            "centroids": [
                {str(index): value for index, value in centroid.items()}
                for centroid in self.centroids
            ],
            "centroid_scales": self.centroid_scales,
            "max_candidates": self.max_candidates,
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return zlib.compress(raw, level=9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "QuantizedDialogueRanker":
        payload = json.loads(zlib.decompress(data))
        if payload.get("format") != cls.FORMAT:
            raise ValueError("unsupported dialogue ranker format")
        return cls(
            responses=tuple(str(value) for value in payload["responses"]),
            pair_dimensions=int(payload["pair_dimensions"]),
            retrieval_dimensions=int(payload["retrieval_dimensions"]),
            scale=float(payload["scale"]),
            weights={int(index): int(value) for index, value in payload["weights"].items()},
            centroids=tuple(
                {int(index): int(value) for index, value in centroid.items()}
                for centroid in payload["centroids"]
            ),
            centroid_scales=tuple(float(value) for value in payload["centroid_scales"]),
            max_candidates=int(payload["max_candidates"]),
        )

    def resource_report(self) -> dict[str, object]:
        active_features_estimate = 256
        return {
            "serialized_bytes": len(self.to_bytes()),
            "responses": len(self.responses),
            "quantized_weights": len(self.weights),
            "centroid_nonzeros": sum(len(value) for value in self.centroids),
            "max_candidates": self.max_candidates,
            "estimated_active_weight_bytes": (
                active_features_estimate * 5
                + self.max_candidates * active_features_estimate * 5
            ),
            "task_name_input_used": False,
            "domain_router_used": False,
            "transformer_used": False,
            "open_ended_generation_claimed": False,
            "highschool_level_passed": False,
        }
