from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import ceil, log2
from typing import Sequence

import numpy as np

from .processes import FinitePredictiveProcess, Word


def fixed_length_words(alphabet_size: int, length: int) -> list[Word]:
    return [tuple(word) for word in product(range(alphabet_size), repeat=length)]


@dataclass(frozen=True)
class CausalTableMachine:
    """A crystallized predictive machine with O(1) work per observed symbol."""

    emission_probabilities: np.ndarray
    next_states: np.ndarray
    initial_state: int
    representatives: tuple[Word, ...]

    @property
    def state_count(self) -> int:
        return int(self.emission_probabilities.shape[0])

    @property
    def alphabet_size(self) -> int:
        return int(self.emission_probabilities.shape[1])

    @property
    def runtime_state_bits(self) -> int:
        return 0 if self.state_count <= 1 else ceil(log2(self.state_count))

    def probability(self, word: Sequence[int]) -> float:
        state = self.initial_state
        probability = 1.0
        for symbol in word:
            probability *= float(self.emission_probabilities[state, symbol])
            state = int(self.next_states[state, symbol])
        return probability


@dataclass
class _Cluster:
    prototype: np.ndarray
    histories: list[Word]


def discover_exact_causal_machine(
    process: FinitePredictiveProcess,
    history_length: int,
    future_horizon: int,
    tolerance: float = 1e-10,
) -> CausalTableMachine:
    """Group histories that induce the same finite-horizon future distribution.

    The dense predictive geometry is crystallized into a discrete state and
    transition table. This separates minimum dimension from minimum runtime
    compute: an SVD basis is dense, while the equivalent causal table needs
    only a state ID and one transition lookup per observed symbol.
    """
    histories = [
        history
        for history in fixed_length_words(process.alphabet_size, history_length)
        if process.probability(history) > 0.0
    ]
    futures = fixed_length_words(process.alphabet_size, future_horizon)
    clusters: list[_Cluster] = []

    def feature(history: Word) -> np.ndarray:
        return process.conditional_future_distribution(history, futures)

    def classify(vector: np.ndarray) -> int:
        distances = [float(np.max(np.abs(vector - cluster.prototype))) for cluster in clusters]
        index = int(np.argmin(distances))
        if distances[index] > tolerance:
            raise RuntimeError(
                f"history maps outside discovered causal states: distance={distances[index]:.3e}"
            )
        return index

    for history in histories:
        vector = feature(history)
        for cluster in clusters:
            if float(np.max(np.abs(vector - cluster.prototype))) <= tolerance:
                cluster.histories.append(history)
                break
        else:
            clusters.append(_Cluster(vector, [history]))

    representatives = tuple(cluster.histories[0] for cluster in clusters)
    emission_probabilities = np.empty(
        (len(clusters), process.alphabet_size), dtype=np.float64
    )
    next_states = np.empty((len(clusters), process.alphabet_size), dtype=np.int64)
    for state, history in enumerate(representatives):
        history_probability = process.probability(history)
        for symbol in process.alphabet:
            extended = history + (symbol,)
            emission_probabilities[state, symbol] = (
                process.probability(extended) / history_probability
            )
            next_states[state, symbol] = classify(feature(extended))

    initial_state = classify(feature(()))
    return CausalTableMachine(
        emission_probabilities=emission_probabilities,
        next_states=next_states,
        initial_state=initial_state,
        representatives=representatives,
    )
