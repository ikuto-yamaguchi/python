from __future__ import annotations

import hashlib
from collections import Counter
from typing import Mapping

from .cic_expr import NUMBER_RE, extract_numbers


def normalize_question(text: str) -> str:
    return NUMBER_RE.sub("<N>", text)


def hashed_features(text: str, *, dimensions: int = 4096) -> dict[int, int]:
    normalized = normalize_question(text)
    values: Counter[int] = Counter({0: 1})
    for width in (2, 3, 4, 5):
        for index in range(max(0, len(normalized) - width + 1)):
            token = normalized[index : index + width]
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            code = int.from_bytes(digest, "little")
            feature = 1 + code % (dimensions - 1)
            values[feature] += 1 if code >> 63 else -1
    count_token = f"COUNT={len(extract_numbers(text))}"
    code = int.from_bytes(hashlib.blake2b(count_token.encode(), digest_size=8).digest(), "little")
    values[1 + code % (dimensions - 1)] += 2
    return {index: max(-4, min(4, value)) for index, value in values.items()}


def sparse_dot(weights: Mapping[int, int | float], features: Mapping[int, int]) -> float:
    return float(sum(weights.get(index, 0) * value for index, value in features.items()))
