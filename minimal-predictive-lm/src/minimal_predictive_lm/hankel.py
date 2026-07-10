from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Mapping, Sequence

import numpy as np

from .processes import FinitePredictiveProcess, Word


def enumerate_words(alphabet_size: int, maximum_length: int) -> list[Word]:
    words: list[Word] = [()]
    alphabet = range(alphabet_size)
    for length in range(1, maximum_length + 1):
        words.extend(tuple(word) for word in product(alphabet, repeat=length))
    return words


def exact_hankel(
    process: FinitePredictiveProcess, maximum_prefix_length: int
) -> tuple[list[Word], list[Word], np.ndarray]:
    prefixes = enumerate_words(process.alphabet_size, maximum_prefix_length)
    suffixes = prefixes.copy()
    matrix = np.asarray(
        [[process.probability(prefix + suffix) for suffix in suffixes] for prefix in prefixes],
        dtype=np.float64,
    )
    return prefixes, suffixes, matrix


def shifted_hankel(
    process: FinitePredictiveProcess,
    prefixes: Sequence[Word],
    suffixes: Sequence[Word],
    symbol: int,
) -> np.ndarray:
    return np.asarray(
        [
            [process.probability(prefix + (symbol,) + suffix) for suffix in suffixes]
            for prefix in prefixes
        ],
        dtype=np.float64,
    )


def numerical_rank(matrix: np.ndarray, relative_tolerance: float = 1e-10) -> int:
    singular_values = np.linalg.svd(matrix, compute_uv=False)
    if singular_values.size == 0 or singular_values[0] == 0.0:
        return 0
    return int(np.count_nonzero(singular_values > relative_tolerance * singular_values[0]))


@dataclass(frozen=True)
class SpectralRealization:
    initial: np.ndarray
    operators: tuple[np.ndarray, ...]
    terminal: np.ndarray
    singular_values: np.ndarray

    @property
    def rank(self) -> int:
        return int(self.initial.shape[0])

    def probability(self, word: Sequence[int]) -> float:
        state = self.initial
        for symbol in word:
            state = state @ self.operators[symbol]
        return float(state @ self.terminal)


def spectral_realization(
    process: FinitePredictiveProcess, maximum_prefix_length: int, rank: int
) -> SpectralRealization:
    prefixes, suffixes, hankel = exact_hankel(process, maximum_prefix_length)
    left, singular_values, right_t = np.linalg.svd(hankel, full_matrices=False)
    if not 1 <= rank <= singular_values.size:
        raise ValueError("rank is outside the available factorization")
    left = left[:, :rank]
    singular_values = singular_values[:rank]
    right_t = right_t[:rank, :]
    root = np.sqrt(singular_values)
    prefix_factor = left * root[None, :]
    suffix_factor = root[:, None] * right_t
    prefix_inverse = np.linalg.pinv(prefix_factor)
    suffix_inverse = np.linalg.pinv(suffix_factor)
    operators = tuple(
        prefix_inverse
        @ shifted_hankel(process, prefixes, suffixes, symbol)
        @ suffix_inverse
        for symbol in process.alphabet
    )
    empty_prefix = prefixes.index(())
    empty_suffix = suffixes.index(())
    return SpectralRealization(
        initial=prefix_factor[empty_prefix].copy(),
        operators=operators,
        terminal=suffix_factor[:, empty_suffix].copy(),
        singular_values=singular_values.copy(),
    )


def empirical_prefix_probabilities(
    sequences: np.ndarray, maximum_length: int, alphabet_size: int
) -> dict[Word, float]:
    if sequences.ndim != 2:
        raise ValueError("sequences must have shape [sample, position]")
    if maximum_length > sequences.shape[1]:
        raise ValueError("maximum_length exceeds sampled sequence length")
    sample_count = sequences.shape[0]
    probabilities: dict[Word, float] = {(): 1.0}
    codes = np.zeros(sample_count, dtype=np.int64)
    for length in range(1, maximum_length + 1):
        codes = codes * alphabet_size + sequences[:, length - 1]
        counts = np.bincount(codes, minlength=alphabet_size**length)
        for code, count in enumerate(counts):
            if count == 0:
                continue
            digits = [0] * length
            remainder = code
            for index in range(length - 1, -1, -1):
                digits[index] = remainder % alphabet_size
                remainder //= alphabet_size
            probabilities[tuple(digits)] = float(count) / sample_count
    return probabilities


def empirical_hankel(
    probabilities: Mapping[Word, float], alphabet_size: int, maximum_prefix_length: int
) -> np.ndarray:
    words = enumerate_words(alphabet_size, maximum_prefix_length)
    return np.asarray(
        [[probabilities.get(prefix + suffix, 0.0) for suffix in words] for prefix in words],
        dtype=np.float64,
    )


def largest_gap_rank(singular_values: np.ndarray, maximum_rank: int | None = None) -> int:
    """A deliberately naive baseline, retained because it fails instructively."""
    if singular_values.size < 2:
        return int(singular_values.size)
    limit = singular_values.size - 1 if maximum_rank is None else min(maximum_rank, singular_values.size - 1)
    ratios = (singular_values[:limit] + 1e-15) / (singular_values[1 : limit + 1] + 1e-15)
    return int(np.argmax(ratios) + 1)


@dataclass(frozen=True)
class SplitNoiseRankEstimate:
    rank: int
    singular_values: np.ndarray
    noise_floor: float
    threshold: float


def estimate_rank_from_split_noise(
    first_hankel: np.ndarray,
    second_hankel: np.ndarray,
    threshold_multiplier: float = 1.0,
) -> SplitNoiseRankEstimate:
    """Estimate signal rank from two independent empirical Hankel matrices.

    If H1=T+E1 and H2=T+E2 with comparable independent noise, the noise in
    their average has half the standard deviation of H1-H2. Therefore
    0.5*||H1-H2||_2 is an empirical operator-norm noise floor for the average.
    """
    if first_hankel.shape != second_hankel.shape:
        raise ValueError("split Hankel matrices must have the same shape")
    average = 0.5 * (first_hankel + second_hankel)
    singular_values = np.linalg.svd(average, compute_uv=False)
    difference_norm = np.linalg.svd(first_hankel - second_hankel, compute_uv=False)[0]
    noise_floor = 0.5 * float(difference_norm)
    threshold = threshold_multiplier * noise_floor
    rank = int(np.count_nonzero(singular_values > threshold))
    return SplitNoiseRankEstimate(rank, singular_values, noise_floor, threshold)
