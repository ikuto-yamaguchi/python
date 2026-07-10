from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

Word = tuple[int, ...]


@dataclass(frozen=True)
class FinitePredictiveProcess:
    """A finite unifilar stochastic process.

    For each state and emitted symbol there is exactly one next state. This is
    deliberately simpler than an HMM: the observed history and the initial
    state determine the internal state. It gives us processes whose true
    minimum predictive memory is known, so architecture claims can be tested
    against a mathematical lower bound.
    """

    emission_probabilities: np.ndarray
    next_states: np.ndarray
    initial_state: int = 0

    def __post_init__(self) -> None:
        emissions = np.asarray(self.emission_probabilities, dtype=np.float64)
        transitions = np.asarray(self.next_states, dtype=np.int64)
        if emissions.ndim != 2:
            raise ValueError("emission_probabilities must have shape [state, symbol]")
        if transitions.shape != emissions.shape:
            raise ValueError("next_states must have the same shape as emissions")
        if np.any(emissions < 0.0):
            raise ValueError("emission probabilities must be non-negative")
        if not np.allclose(emissions.sum(axis=1), 1.0):
            raise ValueError("emission probabilities must sum to one in each state")
        if np.any(transitions < 0) or np.any(transitions >= emissions.shape[0]):
            raise ValueError("next state index out of range")
        if not 0 <= self.initial_state < emissions.shape[0]:
            raise ValueError("initial_state out of range")
        object.__setattr__(self, "emission_probabilities", emissions)
        object.__setattr__(self, "next_states", transitions)

    @property
    def state_count(self) -> int:
        return int(self.emission_probabilities.shape[0])

    @property
    def alphabet_size(self) -> int:
        return int(self.emission_probabilities.shape[1])

    @property
    def alphabet(self) -> tuple[int, ...]:
        return tuple(range(self.alphabet_size))

    def state_after(self, word: Sequence[int]) -> int:
        state = self.initial_state
        for symbol in word:
            state = int(self.next_states[state, symbol])
        return state

    def probability(self, word: Sequence[int]) -> float:
        state = self.initial_state
        probability = 1.0
        for symbol in word:
            if not 0 <= symbol < self.alphabet_size:
                return 0.0
            probability *= float(self.emission_probabilities[state, symbol])
            state = int(self.next_states[state, symbol])
        return probability

    def conditional_future_distribution(
        self, history: Sequence[int], futures: Iterable[Word]
    ) -> np.ndarray:
        history_probability = self.probability(history)
        if history_probability <= 0.0:
            raise ValueError("cannot condition on an impossible history")
        return np.asarray(
            [self.probability(tuple(history) + future) / history_probability for future in futures],
            dtype=np.float64,
        )

    def sample_prefixes(
        self, sample_count: int, length: int, rng: np.random.Generator
    ) -> np.ndarray:
        """Draw independent sequences from the fixed initial state."""
        if sample_count <= 0 or length < 0:
            raise ValueError("sample_count must be positive and length non-negative")
        sequences = np.empty((sample_count, length), dtype=np.int16)
        states = np.full(sample_count, self.initial_state, dtype=np.int64)
        cumulative = np.cumsum(self.emission_probabilities, axis=1)
        for position in range(length):
            draws = rng.random(sample_count)
            rows = cumulative[states]
            symbols = (draws[:, None] > rows).sum(axis=1).astype(np.int64)
            sequences[:, position] = symbols
            states = self.next_states[states, symbols]
        return sequences


def iid_process(probability_of_one: float = 0.35) -> FinitePredictiveProcess:
    if not 0.0 < probability_of_one < 1.0:
        raise ValueError("probability_of_one must lie strictly between zero and one")
    return FinitePredictiveProcess(
        emission_probabilities=np.asarray([[1.0 - probability_of_one, probability_of_one]]),
        next_states=np.asarray([[0, 0]]),
    )


def modulo_ones_process(
    state_count: int,
    minimum_one_probability: float = 0.15,
    maximum_one_probability: float = 0.75,
) -> FinitePredictiveProcess:
    """State is the number of observed ones modulo ``state_count``."""
    if state_count < 2:
        raise ValueError("state_count must be at least two")
    probabilities = np.linspace(
        minimum_one_probability, maximum_one_probability, state_count, dtype=np.float64
    )
    emissions = np.stack((1.0 - probabilities, probabilities), axis=1)
    next_states = np.empty((state_count, 2), dtype=np.int64)
    next_states[:, 0] = np.arange(state_count)
    next_states[:, 1] = (np.arange(state_count) + 1) % state_count
    return FinitePredictiveProcess(emissions, next_states)
