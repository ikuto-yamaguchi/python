from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log2
from typing import Sequence

import numpy as np

from .registers import (
    BIT_ONE,
    BIT_ZERO,
    FILLER,
    KEY_BASE,
    QUERY,
    WRITE,
    Phase,
    RegisterLanguage,
)


@dataclass(frozen=True)
class CandidateResult:
    slots: int
    write_offset: int
    query_count: int
    errors: int | None
    nll_bits: float
    runtime_data_bits: int
    program_bits: int
    objective_bits: float


def sample_tokens(
    language: RegisterLanguage, token_count: int, rng: np.random.Generator
) -> np.ndarray:
    state = language.initial_state
    tokens = np.empty(token_count, dtype=np.int16)
    for index in range(token_count):
        distribution = language.next_distribution(state)
        token = int(rng.choice(language.alphabet_size, p=distribution))
        tokens[index] = token
        state = language.step(state, token)
    return tokens


def _integer_code_bits(value: int) -> int:
    """A small monotone proxy for a self-delimiting integer code length."""
    if value <= 0:
        return 1
    width = value.bit_length()
    return 2 * width + 1


def evaluate_candidate(
    tokens: Sequence[int],
    slots: int,
    write_offset: int,
    error_probability: float = 1e-6,
    state_bit_weight: float = 1.0,
    program_bit_weight: float = 1.0,
) -> CandidateResult:
    if slots < 0:
        raise ValueError("slots must be non-negative")
    if slots == 0 and write_offset != 0:
        raise ValueError("zero-slot candidate must use zero offset")
    if slots > 0 and not 0 <= write_offset < slots:
        raise ValueError("write_offset out of range")

    memory = [0] * slots
    phase = Phase.READY
    pending_key = -1
    query_count = 0
    errors = 0
    nll_bits = 0.0

    for token in tokens:
        token = int(token)
        if phase == Phase.READY:
            if token == WRITE:
                phase = Phase.WRITE_KEY
            elif token == QUERY:
                phase = Phase.QUERY_KEY
            elif token != FILLER:
                raise ValueError("invalid token stream in READY")
            continue

        if phase == Phase.WRITE_KEY:
            if token < KEY_BASE:
                raise ValueError("expected key after WRITE")
            pending_key = token - KEY_BASE
            phase = Phase.WRITE_VALUE
            continue

        if phase == Phase.WRITE_VALUE:
            if token not in (BIT_ZERO, BIT_ONE):
                raise ValueError("expected bit after WRITE key")
            if slots > 0:
                address = (pending_key + write_offset) % slots
                memory[address] = int(token == BIT_ONE)
            phase = Phase.READY
            pending_key = -1
            continue

        if phase == Phase.QUERY_KEY:
            if token < KEY_BASE:
                raise ValueError("expected key after QUERY")
            pending_key = token - KEY_BASE
            phase = Phase.QUERY_VALUE
            continue

        if phase == Phase.QUERY_VALUE:
            if token not in (BIT_ZERO, BIT_ONE):
                raise ValueError("expected bit after QUERY key")
            actual = int(token == BIT_ONE)
            query_count += 1
            if slots == 0:
                nll_bits += 1.0
            else:
                predicted = memory[pending_key % slots]
                correct = predicted == actual
                errors += int(not correct)
                probability = 1.0 - error_probability if correct else error_probability
                nll_bits -= log2(probability)
            phase = Phase.READY
            pending_key = -1
            continue

        raise RuntimeError(f"unknown phase {phase}")

    runtime_bits = slots
    program_bits = _integer_code_bits(slots)
    if slots > 0:
        program_bits += max(1, ceil(log2(slots)))
    objective = (
        nll_bits
        + state_bit_weight * runtime_bits
        + program_bit_weight * program_bits
    )
    return CandidateResult(
        slots=slots,
        write_offset=write_offset,
        query_count=query_count,
        errors=None if slots == 0 else errors,
        nll_bits=nll_bits,
        runtime_data_bits=runtime_bits,
        program_bits=program_bits,
        objective_bits=objective,
    )


def search_register_programs(
    tokens: Sequence[int], maximum_slots: int
) -> list[CandidateResult]:
    results = [evaluate_candidate(tokens, 0, 0)]
    for slots in range(1, maximum_slots + 1):
        for offset in range(slots):
            results.append(evaluate_candidate(tokens, slots, offset))
    results.sort(key=lambda result: (result.objective_bits, result.slots, result.write_offset))
    return results
