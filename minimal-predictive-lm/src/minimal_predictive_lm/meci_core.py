from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from heapq import heappop, heappush
from math import ceil, gcd, log2
from typing import Hashable, Mapping, Sequence

History = Hashable
Query = Hashable
Answer = Hashable


def _ceil_log2(value: int) -> int:
    if value <= 1:
        return 0
    return ceil(log2(value))


@dataclass(frozen=True)
class OperationalQuotient:
    """Exact quotient of histories by task-relevant executable behaviour.

    Two histories share one state iff every declared query receives the same
    answer. For a finite query family this is the coarsest exact state
    representation; any exact agent must distinguish every distinct row.
    """

    queries: tuple[Query, ...]
    state_of: Mapping[History, int]
    signatures: tuple[tuple[Answer, ...], ...]

    @classmethod
    def build(
        cls,
        histories: Sequence[History],
        queries: Sequence[Query],
        answers: Mapping[tuple[History, Query], Answer],
    ) -> "OperationalQuotient":
        qtuple = tuple(queries)
        signature_to_state: dict[tuple[Answer, ...], int] = {}
        state_of: dict[History, int] = {}
        signatures: list[tuple[Answer, ...]] = []
        for history in histories:
            signature = tuple(answers[(history, query)] for query in qtuple)
            state = signature_to_state.get(signature)
            if state is None:
                state = len(signatures)
                signature_to_state[signature] = state
                signatures.append(signature)
            state_of[history] = state
        return cls(qtuple, state_of, tuple(signatures))

    @property
    def state_count(self) -> int:
        return len(self.signatures)

    @property
    def worst_case_memory_lower_bound_bits(self) -> int:
        return _ceil_log2(self.state_count)

    @property
    def canonical_state_bits(self) -> int:
        return _ceil_log2(self.state_count)

    def answer(self, history: History, query: Query) -> Answer:
        state = self.state_of[history]
        index = self.queries.index(query)
        return self.signatures[state][index]


@dataclass(frozen=True)
class HuffmanCode:
    lengths: Mapping[Hashable, int]
    expected_decisions: float
    entropy_lower_bound: float


def huffman_code(probabilities: Mapping[Hashable, float]) -> HuffmanCode:
    """Build a binary prefix code and report the Shannon decision lower bound."""
    if not probabilities:
        raise ValueError("probabilities must not be empty")
    total = sum(probabilities.values())
    if total <= 0:
        raise ValueError("probability mass must be positive")
    probs = {symbol: value / total for symbol, value in probabilities.items() if value > 0}
    if len(probs) == 1:
        only = next(iter(probs))
        return HuffmanCode({only: 0}, 0.0, 0.0)

    heap: list[tuple[float, int, tuple[Hashable, ...]]] = []
    serial = 0
    for symbol, probability in probs.items():
        heappush(heap, (probability, serial, (symbol,)))
        serial += 1
    lengths: dict[Hashable, int] = {symbol: 0 for symbol in probs}
    while len(heap) > 1:
        p1, _, symbols1 = heappop(heap)
        p2, _, symbols2 = heappop(heap)
        for symbol in symbols1 + symbols2:
            lengths[symbol] += 1
        heappush(heap, (p1 + p2, serial, symbols1 + symbols2))
        serial += 1
    entropy = -sum(probability * log2(probability) for probability in probs.values())
    expected = sum(probs[symbol] * lengths[symbol] for symbol in probs)
    return HuffmanCode(lengths, expected, entropy)


@dataclass(frozen=True)
class PredictiveState:
    signature: tuple[tuple[int, int], ...]
    contexts: tuple[bytes, ...]


class QuotientByteModel:
    """Non-neural byte predictor with exact empirical predictive-state merging.

    Contexts with identical reduced next-byte count ratios are represented by
    one state. The model is deliberately finite and auditable; it is not a
    claim of unrestricted language understanding.
    """

    def __init__(self, max_order: int = 8) -> None:
        if max_order < 0:
            raise ValueError("max_order must be non-negative")
        self.max_order = max_order
        self._counts: dict[bytes, Counter[int]] = defaultdict(Counter)
        self._context_to_state: dict[bytes, int] = {}
        self._states: list[PredictiveState] = []

    @staticmethod
    def _reduced_signature(counts: Counter[int]) -> tuple[tuple[int, int], ...]:
        if not counts:
            return ()
        divisor = 0
        for value in counts.values():
            divisor = gcd(divisor, value)
        return tuple(sorted((symbol, count // divisor) for symbol, count in counts.items()))

    def fit(self, data: bytes) -> "QuotientByteModel":
        self._counts.clear()
        for index, symbol in enumerate(data):
            max_len = min(self.max_order, index)
            for length in range(max_len + 1):
                context = data[index - length : index]
                self._counts[context][symbol] += 1
        groups: dict[tuple[tuple[int, int], ...], list[bytes]] = defaultdict(list)
        for context, counts in self._counts.items():
            groups[self._reduced_signature(counts)].append(context)
        self._states = []
        self._context_to_state = {}
        for state_id, (signature, contexts) in enumerate(sorted(groups.items(), key=lambda item: item[0])):
            ordered = tuple(sorted(contexts, key=lambda value: (len(value), value)))
            self._states.append(PredictiveState(signature, ordered))
            for context in ordered:
                self._context_to_state[context] = state_id
        return self

    @property
    def context_count(self) -> int:
        return len(self._counts)

    @property
    def state_count(self) -> int:
        return len(self._states)

    @property
    def working_state_lower_bound_bits(self) -> int:
        return _ceil_log2(self.state_count)

    def _select_context(self, history: bytes) -> bytes:
        for length in range(min(self.max_order, len(history)), -1, -1):
            context = history[-length:] if length else b""
            if context in self._counts:
                return context
        return b""

    def distribution(self, history: bytes) -> dict[int, Fraction]:
        context = self._select_context(history)
        counts = self._counts[context]
        total = sum(counts.values())
        return {symbol: Fraction(count, total) for symbol, count in counts.items()}

    def predict(self, history: bytes) -> int:
        distribution = self.distribution(history)
        if not distribution:
            raise ValueError("model is not fitted")
        return min(distribution, key=lambda symbol: (-distribution[symbol], symbol))

    def generate(self, prompt: bytes, max_new_bytes: int = 64, stop: bytes | None = None) -> bytes:
        output = bytearray(prompt)
        generated = bytearray()
        for _ in range(max_new_bytes):
            symbol = self.predict(bytes(output))
            output.append(symbol)
            generated.append(symbol)
            if stop and generated.endswith(stop):
                break
        return bytes(generated)

    def negative_log2_likelihood(self, data: bytes) -> float:
        if not data:
            return 0.0
        loss = 0.0
        history = bytearray()
        for symbol in data:
            distribution = self.distribution(bytes(history))
            probability = float(distribution.get(symbol, Fraction(1, 1 << 20)))
            loss -= log2(probability)
            history.append(symbol)
        return loss

    def report(self) -> dict[str, int | float]:
        return {
            "max_order": self.max_order,
            "contexts_before_quotient": self.context_count,
            "predictive_states_after_quotient": self.state_count,
            "working_state_lower_bound_bits": self.working_state_lower_bound_bits,
            "context_to_state_reduction": (
                self.context_count / self.state_count if self.state_count else 0.0
            ),
        }
