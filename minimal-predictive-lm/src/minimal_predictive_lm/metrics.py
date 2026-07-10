from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log2


@dataclass(frozen=True)
class RuntimeCost:
    model_bytes: int
    runtime_state_bits: int
    multiply_accumulates_per_symbol: int
    table_reads_per_symbol: int


def minimum_index_bytes(state_count: int) -> int:
    if state_count <= 1:
        return 0
    return max(1, ceil(log2(state_count) / 8))


def dense_spectral_cost(rank: int, alphabet_size: int, float_bytes: int = 4) -> RuntimeCost:
    parameters = alphabet_size * rank * rank + 2 * rank
    return RuntimeCost(
        model_bytes=parameters * float_bytes,
        runtime_state_bits=rank * float_bytes * 8,
        multiply_accumulates_per_symbol=rank * rank,
        table_reads_per_symbol=0,
    )


def causal_table_cost(
    state_count: int,
    alphabet_size: int,
    probability_bytes: int = 2,
) -> RuntimeCost:
    index_bytes = minimum_index_bytes(state_count)
    model_bytes = state_count * alphabet_size * (probability_bytes + index_bytes)
    state_bits = 0 if state_count <= 1 else ceil(log2(state_count))
    return RuntimeCost(
        model_bytes=model_bytes,
        runtime_state_bits=state_bits,
        multiply_accumulates_per_symbol=0,
        table_reads_per_symbol=2,
    )
