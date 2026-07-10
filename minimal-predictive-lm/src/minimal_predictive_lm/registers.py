from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from math import ceil, log2
from typing import Sequence

import numpy as np


class Phase(IntEnum):
    READY = 0
    WRITE_KEY = 1
    WRITE_VALUE = 2
    QUERY_KEY = 3
    QUERY_VALUE = 4


WRITE = 0
QUERY = 1
FILLER = 2
BIT_ZERO = 3
BIT_ONE = 4
KEY_BASE = 5


@dataclass(frozen=True)
class RegisterState:
    memory_bits: int
    phase: Phase = Phase.READY
    pending_key: int = -1


@dataclass(frozen=True)
class RegisterLanguage:
    """An autoregressive language backed by K independently addressable bits.

    Grammar:
      READY -> WRITE key random_bit
             | QUERY key stored_bit
             | FILLER

    A flat causal-state table must distinguish all 2^K memory assignments.
    The factored implementation stores exactly K data bits and applies a small
    addressable update rule, avoiding exponential transition-table growth.
    """

    key_count: int
    write_probability: float = 0.4
    query_probability: float = 0.4
    filler_probability: float = 0.2

    def __post_init__(self) -> None:
        if self.key_count <= 0:
            raise ValueError("key_count must be positive")
        probabilities = (
            self.write_probability,
            self.query_probability,
            self.filler_probability,
        )
        if any(probability < 0.0 for probability in probabilities):
            raise ValueError("action probabilities must be non-negative")
        if not np.isclose(sum(probabilities), 1.0):
            raise ValueError("action probabilities must sum to one")

    @property
    def alphabet_size(self) -> int:
        return KEY_BASE + self.key_count

    @property
    def initial_state(self) -> RegisterState:
        return RegisterState(memory_bits=0)

    def key_token(self, key: int) -> int:
        if not 0 <= key < self.key_count:
            raise ValueError("key out of range")
        return KEY_BASE + key

    def decode_key(self, token: int) -> int:
        key = token - KEY_BASE
        if not 0 <= key < self.key_count:
            raise ValueError("token is not a key")
        return key

    def bit(self, memory_bits: int, key: int) -> int:
        return (memory_bits >> key) & 1

    def next_distribution(self, state: RegisterState) -> np.ndarray:
        distribution = np.zeros(self.alphabet_size, dtype=np.float64)
        if state.phase == Phase.READY:
            distribution[WRITE] = self.write_probability
            distribution[QUERY] = self.query_probability
            distribution[FILLER] = self.filler_probability
        elif state.phase in (Phase.WRITE_KEY, Phase.QUERY_KEY):
            distribution[KEY_BASE:] = 1.0 / self.key_count
        elif state.phase == Phase.WRITE_VALUE:
            distribution[BIT_ZERO] = 0.5
            distribution[BIT_ONE] = 0.5
        elif state.phase == Phase.QUERY_VALUE:
            value = self.bit(state.memory_bits, state.pending_key)
            distribution[BIT_ONE if value else BIT_ZERO] = 1.0
        else:
            raise RuntimeError(f"unsupported phase: {state.phase}")
        return distribution

    def step(self, state: RegisterState, token: int) -> RegisterState:
        distribution = self.next_distribution(state)
        if not 0 <= token < self.alphabet_size or distribution[token] <= 0.0:
            raise ValueError(f"token {token} is impossible in phase {state.phase.name}")

        if state.phase == Phase.READY:
            if token == WRITE:
                return RegisterState(state.memory_bits, Phase.WRITE_KEY)
            if token == QUERY:
                return RegisterState(state.memory_bits, Phase.QUERY_KEY)
            return state

        if state.phase == Phase.WRITE_KEY:
            return RegisterState(state.memory_bits, Phase.WRITE_VALUE, self.decode_key(token))

        if state.phase == Phase.WRITE_VALUE:
            mask = 1 << state.pending_key
            memory = state.memory_bits | mask if token == BIT_ONE else state.memory_bits & ~mask
            return RegisterState(memory, Phase.READY)

        if state.phase == Phase.QUERY_KEY:
            return RegisterState(state.memory_bits, Phase.QUERY_VALUE, self.decode_key(token))

        if state.phase == Phase.QUERY_VALUE:
            return RegisterState(state.memory_bits, Phase.READY)

        raise RuntimeError(f"unsupported phase: {state.phase}")

    def probability(self, sequence: Sequence[int], state: RegisterState | None = None) -> float:
        current = self.initial_state if state is None else state
        probability = 1.0
        for token in sequence:
            distribution = self.next_distribution(current)
            if not 0 <= token < self.alphabet_size:
                return 0.0
            probability *= float(distribution[token])
            if probability == 0.0:
                return 0.0
            current = self.step(current, token)
        return probability

    def write(self, state: RegisterState, key: int, value: int) -> RegisterState:
        tokens = (WRITE, self.key_token(key), BIT_ONE if value else BIT_ZERO)
        current = state
        for token in tokens:
            current = self.step(current, token)
        return current

    def query_tokens(self, state: RegisterState, key: int) -> tuple[int, int, int]:
        value = self.bit(state.memory_bits, key)
        return (QUERY, self.key_token(key), BIT_ONE if value else BIT_ZERO)

    def query(self, state: RegisterState, key: int) -> RegisterState:
        current = state
        for token in self.query_tokens(state, key):
            current = self.step(current, token)
        return current


@dataclass(frozen=True)
class RegisterCost:
    key_count: int
    predictive_memory_lower_bound_bits: int
    factored_data_memory_bits: int
    factored_total_runtime_bits: int
    flat_ready_states: int
    flat_enumerated_states: int
    flat_sparse_edges: int
    flat_sparse_table_bytes: int
    factored_parameter_bytes: int
    expected_data_bit_reads_per_token: float
    expected_data_bit_writes_per_token: float
    dense_fp32_state_write_bits_per_token: int
    write_traffic_reduction: float


def register_cost(language: RegisterLanguage) -> RegisterCost:
    key_count = language.key_count
    memory_assignments = 1 << key_count
    flat_states = memory_assignments * (3 + 2 * key_count)
    flat_edges = memory_assignments * (3 + 5 * key_count)
    state_index_bytes = max(1, ceil(log2(flat_states) / 8))
    token_bytes = max(1, ceil(log2(language.alphabet_size) / 8))
    probability_bytes = 2
    sparse_table_bytes = flat_edges * (state_index_bytes + token_bytes + probability_bytes)

    phase_bits = ceil(log2(len(Phase)))
    key_bits = 0 if key_count == 1 else ceil(log2(key_count))
    factored_total_bits = key_count + phase_bits + key_bits

    expected_tokens_per_ready_event = (
        language.filler_probability
        + 3.0 * language.write_probability
        + 3.0 * language.query_probability
    )
    writes_per_token = language.write_probability / expected_tokens_per_ready_event
    reads_per_token = language.query_probability / expected_tokens_per_ready_event
    dense_write_bits = 32 * key_count
    reduction = dense_write_bits / writes_per_token if writes_per_token > 0 else float("inf")

    factored_parameter_bytes = 10
    return RegisterCost(
        key_count=key_count,
        predictive_memory_lower_bound_bits=key_count,
        factored_data_memory_bits=key_count,
        factored_total_runtime_bits=factored_total_bits,
        flat_ready_states=memory_assignments,
        flat_enumerated_states=flat_states,
        flat_sparse_edges=flat_edges,
        flat_sparse_table_bytes=sparse_table_bytes,
        factored_parameter_bytes=factored_parameter_bytes,
        expected_data_bit_reads_per_token=reads_per_token,
        expected_data_bit_writes_per_token=writes_per_token,
        dense_fp32_state_write_bits_per_token=dense_write_bits,
        write_traffic_reduction=reduction,
    )


def distinguishing_query(language: RegisterLanguage, first: int, second: int) -> tuple[int, int]:
    """Return a key and deterministic answer token that distinguishes two memories."""
    difference = first ^ second
    if difference == 0:
        raise ValueError("memory assignments are identical")
    key = (difference & -difference).bit_length() - 1
    first_value = language.bit(first, key)
    return key, BIT_ONE if first_value else BIT_ZERO
