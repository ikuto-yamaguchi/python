from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable

from .sparse_causal_induction import (
    CausalTrainingExample,
    SparseCausalPrototypeModel,
    train_sparse_causal_prototypes,
)


def train_routed_sparse_causal_prototypes(
    examples: Iterable[CausalTrainingExample],
    *,
    maximum_features_per_prototype: int = 384,
    maximum_posting_frequency: int = 6,
) -> SparseCausalPrototypeModel:
    base = train_sparse_causal_prototypes(
        examples,
        maximum_features_per_prototype=maximum_features_per_prototype,
    )
    frequency: Counter[str] = Counter()
    for prototype in base.prototypes:
        frequency.update(feature for feature, _weight in prototype.weights)

    postings: dict[str, list[int]] = defaultdict(list)
    for index, prototype in enumerate(base.prototypes):
        for feature, _weight in prototype.weights:
            if frequency[feature] <= maximum_posting_frequency:
                postings[feature].append(index)

    return SparseCausalPrototypeModel(
        base.prototypes,
        {feature: tuple(indices) for feature, indices in postings.items()},
        minimum_score=base.minimum_score,
        minimum_margin=base.minimum_margin,
    )
