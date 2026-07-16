from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


def _normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector.copy()


@dataclass(frozen=True)
class SACSReport:
    blocks: int
    top_k: int
    key_dim: int
    value_dim: int
    state_bytes: int
    router_bytes: int
    total_bytes: int
    read_multiply_adds: int
    write_multiply_adds: int


class SelectiveAssociativeState:
    """Fixed-size block-sparse fast-weight associative memory.

    The model stores no per-token KV cache. A key selects only top-k blocks.
    Each selected block performs a delta correction: erase the currently read
    association and write the new target with independent gates. The state size
    and per-step work are independent of conversation length.
    """

    def __init__(
        self,
        *,
        key_dim: int = 64,
        value_dim: int = 32,
        blocks: int = 16,
        top_k: int = 2,
        decays: Sequence[float] | None = None,
        seed: int = 0,
        dtype: np.dtype = np.float32,
    ) -> None:
        if key_dim <= 0 or value_dim <= 0 or blocks <= 0:
            raise ValueError("dimensions and blocks must be positive")
        if not 1 <= top_k <= blocks:
            raise ValueError("top_k must be between one and blocks")
        self.key_dim = key_dim
        self.value_dim = value_dim
        self.blocks = blocks
        self.top_k = top_k
        self.dtype = np.dtype(dtype)
        generator = np.random.default_rng(seed)
        router = generator.standard_normal((blocks, key_dim)).astype(self.dtype)
        router /= np.linalg.norm(router, axis=1, keepdims=True) + 1e-12
        self.router = router
        self.memory = np.zeros((blocks, value_dim, key_dim), dtype=self.dtype)
        self.usage = np.zeros(blocks, dtype=np.float32)
        if decays is None:
            # Log-spaced retention gives short, medium and long timescales.
            decays = np.geomspace(0.90, 0.9999, blocks)
        if len(decays) != blocks:
            raise ValueError("decays must match blocks")
        self.decays = np.asarray(decays, dtype=np.float32)

    def reset(self) -> None:
        self.memory.fill(0)
        self.usage.fill(0)

    def route(self, key: np.ndarray) -> np.ndarray:
        key = _normalize(np.asarray(key, dtype=self.dtype))
        scores = np.abs(self.router @ key)
        selected = np.argpartition(scores, -self.top_k)[-self.top_k :]
        return selected[np.argsort(scores[selected])[::-1]]

    def read(self, key: np.ndarray) -> np.ndarray:
        key = _normalize(np.asarray(key, dtype=self.dtype))
        selected = self.route(key)
        scores = np.abs(self.router[selected] @ key)
        weights = scores / (float(scores.sum()) + 1e-12)
        outputs = np.einsum("bvk,k->bv", self.memory[selected], key)
        return np.einsum("b,bv->v", weights, outputs).astype(self.dtype)

    def write(
        self,
        key: np.ndarray,
        value: np.ndarray,
        *,
        erase_gate: float = 1.0,
        write_gate: float = 1.0,
    ) -> None:
        key = _normalize(np.asarray(key, dtype=self.dtype))
        value = np.asarray(value, dtype=self.dtype)
        if value.shape != (self.value_dim,):
            raise ValueError(f"value must have shape {(self.value_dim,)}")
        selected = self.route(key)
        scores = np.abs(self.router[selected] @ key)
        routing = scores / (float(scores.sum()) + 1e-12)
        for local_index, block_index in enumerate(selected):
            block = self.memory[block_index]
            prediction = block @ key
            # Independent erase and write terms. Setting both to one is the
            # classical delta rule; separating them allows future learned gates.
            block *= self.decays[block_index]
            block -= (
                float(erase_gate)
                * routing[local_index]
                * np.outer(prediction, key)
            )
            block += (
                float(write_gate)
                * routing[local_index]
                * np.outer(value, key)
            )
            self.usage[block_index] += 1.0

    def update(
        self,
        key: np.ndarray,
        target: np.ndarray,
        *,
        learning_rate: float = 1.0,
    ) -> float:
        prediction = self.read(key)
        error = np.asarray(target, dtype=self.dtype) - prediction
        corrected_target = prediction + float(learning_rate) * error
        self.write(key, corrected_target)
        return float(np.mean(error * error))

    def report(self) -> SACSReport:
        state_bytes = int(self.memory.nbytes + self.usage.nbytes + self.decays.nbytes)
        router_bytes = int(self.router.nbytes)
        # A matrix-vector product is counted as one multiply and one add per
        # element. Routing is included in both read and write paths.
        route_ops = 2 * self.blocks * self.key_dim
        read_ops = route_ops + 2 * self.top_k * self.value_dim * self.key_dim
        write_ops = (
            route_ops
            + 2 * self.top_k * self.value_dim * self.key_dim
            + 4 * self.top_k * self.value_dim * self.key_dim
        )
        return SACSReport(
            blocks=self.blocks,
            top_k=self.top_k,
            key_dim=self.key_dim,
            value_dim=self.value_dim,
            state_bytes=state_bytes,
            router_bytes=router_bytes,
            total_bytes=state_bytes + router_bytes,
            read_multiply_adds=read_ops,
            write_multiply_adds=write_ops,
        )


class FullHistoryAttentionMemory:
    """Reference content-addressed cache whose memory grows with history."""

    def __init__(self, key_dim: int, value_dim: int) -> None:
        self.key_dim = key_dim
        self.value_dim = value_dim
        self.keys: list[np.ndarray] = []
        self.values: list[np.ndarray] = []

    def write(self, key: np.ndarray, value: np.ndarray) -> None:
        self.keys.append(_normalize(np.asarray(key, dtype=np.float32)))
        self.values.append(np.asarray(value, dtype=np.float32).copy())

    def read(self, key: np.ndarray) -> np.ndarray:
        if not self.keys:
            return np.zeros(self.value_dim, dtype=np.float32)
        query = _normalize(np.asarray(key, dtype=np.float32))
        keys = np.stack(self.keys)
        scores = keys @ query
        index = int(np.argmax(scores))
        return self.values[index].copy()

    @property
    def total_bytes(self) -> int:
        return len(self.keys) * 4 * (self.key_dim + self.value_dim)

    @property
    def read_multiply_adds(self) -> int:
        return 2 * len(self.keys) * self.key_dim


class SingleVectorRecurrentMemory:
    """Equal-cost sanity baseline that compresses all values into one vector."""

    def __init__(self, value_dim: int, decay: float = 0.99) -> None:
        self.value_dim = value_dim
        self.decay = decay
        self.state = np.zeros(value_dim, dtype=np.float32)

    def write(self, _key: np.ndarray, value: np.ndarray) -> None:
        self.state *= self.decay
        self.state += np.asarray(value, dtype=np.float32)

    def read(self, _key: np.ndarray) -> np.ndarray:
        return self.state.copy()

    @property
    def total_bytes(self) -> int:
        return int(self.state.nbytes)
