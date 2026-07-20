from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


def _compact(text: str) -> str:
    return "".join(text.split())


def _grams(text: str, sizes: Sequence[int] = (2, 3)) -> tuple[str, ...]:
    value = _compact(text)
    out: list[str] = []
    for size in sizes:
        if len(value) < size:
            continue
        out.extend(value[i : i + size] for i in range(len(value) - size + 1))
    return tuple(dict.fromkeys(out))


def _bucket(label: str, dimensions: int) -> int:
    digest = hashlib.blake2b(label.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dimensions


def _quantize(value: float, bins: int = 10) -> int:
    return max(0, min(bins, int(value * bins)))


@dataclass(frozen=True, slots=True)
class PreferencePair:
    context: tuple[str, ...]
    chosen: str
    rejected: str


class InteractionFeatureMap:
    """Task-agnostic prompt/response relation features.

    No topic dictionary, response strategy labels, answer keys, or benchmark names
    are consumed. The map only sees raw dialogue text and bounded structural
    relations between the context and a candidate response.
    """

    def __init__(self, dimensions: int = 65_536, *, include_context: bool = True) -> None:
        if dimensions < 1024:
            raise ValueError("dimensions must be >= 1024")
        self.dimensions = dimensions
        self.include_context = include_context

    def encode(self, context: Sequence[str], response: str) -> dict[int, float]:
        user = context[-1] if context else ""
        history = "\n".join(context[-6:-1])
        user_grams = set(_grams(user))
        history_grams = set(_grams(history))
        response_grams = set(_grams(response))
        features: dict[int, float] = {}

        def add(label: str, value: float = 1.0) -> None:
            index = _bucket(label, self.dimensions)
            features[index] = features.get(index, 0.0) + value

        # Candidate-only fluency/style evidence. Kept as an explicit ablation.
        for gram in response_grams:
            add("R:" + gram, 1.0 / math.sqrt(max(1, len(response_grams))))

        rlen = len(_compact(response))
        add(f"RLEN:{min(20, rlen // 16)}")
        add(f"RQUEST:{int(response.rstrip().endswith(('?', '？')))}")
        add(f"RPUNCT:{min(8, sum(response.count(mark) for mark in '。！？!?'))}")

        if not self.include_context:
            return features

        # Context evidence and prompt-response interaction.
        for gram in user_grams:
            add("U:" + gram, 0.5 / math.sqrt(max(1, len(user_grams))))
        shared = user_grams & response_grams
        shared_history = history_grams & response_grams
        union = user_grams | response_grams
        overlap = len(shared) / max(1, len(union))
        history_overlap = len(shared_history) / max(1, len(history_grams | response_grams))
        add(f"OVERLAP:{_quantize(overlap)}")
        add(f"HREPEAT:{_quantize(history_overlap)}")
        add(f"LENRATIO:{min(12, int(rlen / max(1, len(_compact(user))) * 2))}")
        add(f"UQUEST:{int(user.rstrip().endswith(('?', '？')))}")
        add(f"TURNS:{min(8, len(context))}")

        # Shared lexical anchors are relation features, not topic-specific rules.
        for gram in shared:
            add("S:" + gram, 1.0 / math.sqrt(max(1, len(shared))))
        for gram in shared_history:
            add("H:" + gram, 0.5 / math.sqrt(max(1, len(shared_history))))

        # Bounded cross-features force prompt-conditioned evidence to compete
        # with response-only style. Sorting makes the read count deterministic.
        for ugram in sorted(user_grams)[:24]:
            for rgram in sorted(response_grams)[:24]:
                add("X:" + ugram + "|" + rgram, 1.0 / 24.0)
        return features


class SparsePairwiseRanker:
    """Non-neural pairwise preference learner with passive-aggressive updates."""

    def __init__(
        self,
        dimensions: int = 65_536,
        *,
        include_context: bool = True,
        aggressiveness: float = 0.5,
    ) -> None:
        self.feature_map = InteractionFeatureMap(dimensions, include_context=include_context)
        self.aggressiveness = float(aggressiveness)
        self.weights: dict[int, float] = {}
        self.updates = 0
        self.feature_reads = 0

    def _score_features(self, features: Mapping[int, float]) -> float:
        self.feature_reads += len(features)
        return sum(self.weights.get(index, 0.0) * value for index, value in features.items())

    def score(self, context: Sequence[str], response: str) -> float:
        return self._score_features(self.feature_map.encode(context, response))

    def prefer(self, context: Sequence[str], left: str, right: str) -> int:
        return 0 if self.score(context, left) >= self.score(context, right) else 1

    def rank(self, context: Sequence[str], candidates: Sequence[str]) -> tuple[int, ...]:
        return tuple(sorted(range(len(candidates)), key=lambda i: self.score(context, candidates[i]), reverse=True))

    def update(self, pair: PreferencePair) -> float:
        positive = self.feature_map.encode(pair.context, pair.chosen)
        negative = self.feature_map.encode(pair.context, pair.rejected)
        diff: dict[int, float] = dict(positive)
        for index, value in negative.items():
            diff[index] = diff.get(index, 0.0) - value
            if abs(diff[index]) < 1e-15:
                diff.pop(index, None)
        margin = sum(self.weights.get(index, 0.0) * value for index, value in diff.items())
        loss = max(0.0, 1.0 - margin)
        if loss == 0.0 or not diff:
            return loss
        norm = sum(value * value for value in diff.values())
        tau = min(self.aggressiveness, loss / max(1e-12, norm))
        for index, value in diff.items():
            updated = self.weights.get(index, 0.0) + tau * value
            if abs(updated) < 1e-12:
                self.weights.pop(index, None)
            else:
                self.weights[index] = updated
        self.updates += 1
        return loss

    def fit(self, pairs: Sequence[PreferencePair], *, epochs: int = 3, seed: int = 0) -> None:
        rng = random.Random(seed)
        order = list(range(len(pairs)))
        for _ in range(epochs):
            rng.shuffle(order)
            for index in order:
                self.update(pairs[index])

    def accuracy(self, pairs: Iterable[PreferencePair]) -> float:
        correct = 0
        total = 0
        for pair in pairs:
            correct += int(self.prefer(pair.context, pair.chosen, pair.rejected) == 0)
            total += 1
        return correct / total if total else 0.0

    def to_dict(self) -> dict:
        return {
            "format": "interaction-closure-ranker-v1",
            "dimensions": self.feature_map.dimensions,
            "include_context": self.feature_map.include_context,
            "aggressiveness": self.aggressiveness,
            "weights": {str(k): v for k, v in self.weights.items()},
            "updates": self.updates,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "SparsePairwiseRanker":
        if data.get("format") != "interaction-closure-ranker-v1":
            raise ValueError("unsupported format")
        model = cls(
            int(data["dimensions"]),
            include_context=bool(data["include_context"]),
            aggressiveness=float(data["aggressiveness"]),
        )
        model.weights = {int(k): float(v) for k, v in dict(data["weights"]).items()}
        model.updates = int(data.get("updates", 0))
        return model

    def serialized_bytes(self) -> int:
        return len(json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def shuffled_context_pairs(pairs: Sequence[PreferencePair], seed: int) -> list[PreferencePair]:
    rng = random.Random(seed)
    contexts = [pair.context for pair in pairs]
    rng.shuffle(contexts)
    return [PreferencePair(contexts[i], pair.chosen, pair.rejected) for i, pair in enumerate(pairs)]
