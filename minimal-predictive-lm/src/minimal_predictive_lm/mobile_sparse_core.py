from __future__ import annotations

from collections import OrderedDict
from dataclasses import asdict, dataclass
import math
import time
from typing import Sequence

import numpy as np


MAX_MODEL_PACKAGE_BYTES = 1_000_000_000


@dataclass(frozen=True)
class MobileHardLimits:
    """Non-negotiable deployment limits for the high-school target."""

    model_package_bytes_max: int = MAX_MODEL_PACKAGE_BYTES
    peak_rss_bytes_max: int = 384_000_000
    active_weight_bytes_per_step_max: int = 4_000_000
    macs_per_byte_step_max: int = 2_000_000
    first_byte_latency_ms_max: float = 300.0
    sustained_byte_steps_per_second_min: float = 60.0


@dataclass(frozen=True)
class MobileSparseProfile:
    name: str
    vocab_buckets: int
    embedding_dim: int
    coarse_groups: int
    blocks_per_group: int
    block_dim: int
    recurrent_rank: int
    active_groups: int
    active_blocks_per_group: int
    state_cache_blocks: int
    memory_slots: int
    memory_key_dim: int
    memory_value_bytes: int
    weight_bytes: int = 1
    state_bytes: int = 2

    @property
    def total_blocks(self) -> int:
        return self.coarse_groups * self.blocks_per_group

    @property
    def bytes_per_block(self) -> int:
        input_weights = self.embedding_dim * self.block_dim * self.weight_bytes
        recurrent = 2 * self.block_dim * self.recurrent_rank * self.weight_bytes
        decoder = self.block_dim * 256 * self.weight_bytes
        bias = 256 * self.weight_bytes
        return input_weights + recurrent + decoder + bias

    def package_bytes(self) -> int:
        embedding = self.vocab_buckets * self.embedding_dim * self.weight_bytes
        coarse_router = self.embedding_dim * self.coarse_groups * self.weight_bytes
        fine_router = (
            self.coarse_groups
            * self.embedding_dim
            * self.blocks_per_group
            * self.weight_bytes
        )
        blocks = self.total_blocks * self.bytes_per_block
        memory = self.memory_slots * (
            self.memory_key_dim * self.weight_bytes + self.memory_value_bytes
        )
        metadata = 64 * 1024
        return embedding + coarse_router + fine_router + blocks + memory + metadata

    def active_weight_bytes_per_step(self) -> int:
        routing = self.embedding_dim * (
            self.coarse_groups
            + self.active_groups * self.blocks_per_group
        ) * self.weight_bytes
        active_blocks = (
            self.active_groups * self.active_blocks_per_group * self.bytes_per_block
        )
        return routing + active_blocks

    def macs_per_byte_step(self) -> int:
        routing = self.embedding_dim * (
            self.coarse_groups
            + self.active_groups * self.blocks_per_group
        )
        per_block = (
            self.embedding_dim * self.block_dim
            + 2 * self.block_dim * self.recurrent_rank
            + self.block_dim * 256
        )
        return routing + (
            self.active_groups * self.active_blocks_per_group * per_block
        )

    def recurrent_state_bytes(self) -> int:
        return self.state_cache_blocks * self.block_dim * self.state_bytes

    def static_gate(self, limits: MobileHardLimits = MobileHardLimits()) -> dict[str, object]:
        package = self.package_bytes()
        active = self.active_weight_bytes_per_step()
        macs = self.macs_per_byte_step()
        checks = {
            "package_at_most_1gb": package <= limits.model_package_bytes_max,
            "active_weight_budget": active <= limits.active_weight_bytes_per_step_max,
            "compute_budget": macs <= limits.macs_per_byte_step_max,
            "active_blocks_are_sparse": (
                self.active_groups * self.active_blocks_per_group
                < self.total_blocks // 100
            ),
        }
        return {
            "profile": asdict(self),
            "package_bytes": package,
            "active_weight_bytes_per_step": active,
            "macs_per_byte_step": macs,
            "recurrent_state_bytes": self.recurrent_state_bytes(),
            "checks": checks,
            "passed": all(checks.values()),
        }


CI_MOBILE_PROFILE = MobileSparseProfile(
    name="ci-mobile-mechanics-only",
    vocab_buckets=2048,
    embedding_dim=24,
    coarse_groups=4,
    blocks_per_group=4,
    block_dim=32,
    recurrent_rank=8,
    active_groups=1,
    active_blocks_per_group=2,
    state_cache_blocks=8,
    memory_slots=32,
    memory_key_dim=16,
    memory_value_bytes=48,
    weight_bytes=4,
    state_bytes=4,
)


MOBILE_1GB_PROFILE = MobileSparseProfile(
    name="mobile-high-school-candidate-hard-cap",
    vocab_buckets=65_536,
    embedding_dim=128,
    coarse_groups=128,
    blocks_per_group=64,
    block_dim=256,
    recurrent_rank=16,
    active_groups=1,
    active_blocks_per_group=2,
    state_cache_blocks=64,
    memory_slots=65_536,
    memory_key_dim=64,
    memory_value_bytes=256,
    weight_bytes=1,
    state_bytes=2,
)


@dataclass(frozen=True)
class MobileTrainingReport:
    examples: int
    byte_updates: int
    nll_before: float
    nll_after: float


class CompactResponseMemory:
    """Task-name-free response memory for the executable chat path."""

    def __init__(self, key_dim: int, max_slots: int) -> None:
        self.key_dim = key_dim
        self.max_slots = max_slots
        self._keys: list[np.ndarray] = []
        self._values: list[str] = []

    def _encode(self, text: str) -> np.ndarray:
        vector = np.zeros(self.key_dim, dtype=np.float32)
        data = text.encode("utf-8")
        for index, byte in enumerate(data):
            slot = ((byte + 1) * 257 + index * 17) % self.key_dim
            vector[slot] += 1.0 if ((byte + index) & 1) else -1.0
        norm = float(np.linalg.norm(vector))
        if norm:
            vector /= norm
        return vector

    def remember(self, prompt: str, response: str) -> None:
        if len(self._keys) >= self.max_slots:
            self._keys.pop(0)
            self._values.pop(0)
        self._keys.append(self._encode(prompt))
        self._values.append(response)

    def recall(self, prompt: str, minimum_similarity: float = 0.86) -> str | None:
        if not self._keys:
            return None
        query = self._encode(prompt)
        scores = np.asarray([float(key @ query) for key in self._keys])
        best = int(scores.argmax())
        if float(scores[best]) < minimum_similarity:
            return None
        return self._values[best]


class MobilePagedSparseCore:
    """Hierarchically routed recurrent blocks with bounded active compute.

    Only selected blocks are touched for each byte. The serious checkpoint is intended
    to be an mmap-backed int8 package. This NumPy class is a trainable mechanics and
    correctness reference, not the final Android runtime.
    """

    def __init__(self, profile: MobileSparseProfile = CI_MOBILE_PROFILE, seed: int = 0) -> None:
        self.profile = profile
        self.rng = np.random.default_rng(seed)
        scale = 1.0 / math.sqrt(profile.embedding_dim)
        self.embeddings = self.rng.normal(
            0.0, scale, size=(profile.vocab_buckets, profile.embedding_dim)
        ).astype(np.float32)
        self.coarse_router = self.rng.normal(
            0.0, scale, size=(profile.embedding_dim, profile.coarse_groups)
        ).astype(np.float32)
        self.fine_router = self.rng.normal(
            0.0,
            scale,
            size=(profile.coarse_groups, profile.embedding_dim, profile.blocks_per_group),
        ).astype(np.float32)
        self.block_input = self.rng.normal(
            0.0,
            scale,
            size=(
                profile.coarse_groups,
                profile.blocks_per_group,
                profile.embedding_dim,
                profile.block_dim,
            ),
        ).astype(np.float32)
        self.block_left = self.rng.normal(
            0.0,
            1.0 / math.sqrt(profile.block_dim),
            size=(
                profile.coarse_groups,
                profile.blocks_per_group,
                profile.block_dim,
                profile.recurrent_rank,
            ),
        ).astype(np.float32)
        self.block_right = self.rng.normal(
            0.0,
            1.0 / math.sqrt(profile.recurrent_rank),
            size=(
                profile.coarse_groups,
                profile.blocks_per_group,
                profile.recurrent_rank,
                profile.block_dim,
            ),
        ).astype(np.float32)
        self.block_decoder = np.zeros(
            (
                profile.coarse_groups,
                profile.blocks_per_group,
                profile.block_dim,
                256,
            ),
            dtype=np.float32,
        )
        self.block_bias = np.zeros(
            (profile.coarse_groups, profile.blocks_per_group, 256), dtype=np.float32
        )
        self._states: OrderedDict[tuple[int, int], np.ndarray] = OrderedDict()
        self.memory = CompactResponseMemory(
            profile.memory_key_dim, min(profile.memory_slots, 4096)
        )

    def reset_state(self) -> None:
        self._states.clear()

    def _bucket(self, previous: int, current: int) -> int:
        return (((previous + 3) * 65537) ^ ((current + 11) * 257)) % self.profile.vocab_buckets

    def _route(self, embedding: np.ndarray) -> tuple[tuple[int, int], ...]:
        coarse_scores = embedding @ self.coarse_router
        group_indices = np.argpartition(
            coarse_scores, -self.profile.active_groups
        )[-self.profile.active_groups :]
        selected: list[tuple[int, int]] = []
        for raw_group in group_indices:
            group = int(raw_group)
            fine_scores = embedding @ self.fine_router[group]
            block_indices = np.argpartition(
                fine_scores, -self.profile.active_blocks_per_group
            )[-self.profile.active_blocks_per_group :]
            selected.extend((group, int(block)) for block in block_indices)
        selected.sort()
        return tuple(selected)

    def _state_for(self, key: tuple[int, int]) -> np.ndarray:
        state = self._states.pop(key, None)
        if state is None:
            state = np.zeros(self.profile.block_dim, dtype=np.float32)
        self._states[key] = state
        while len(self._states) > self.profile.state_cache_blocks:
            self._states.popitem(last=False)
        return state

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        shifted = logits - float(logits.max())
        exp = np.exp(shifted)
        return exp / float(exp.sum())

    def _step(
        self, previous: int, current: int
    ) -> tuple[np.ndarray, tuple[tuple[int, int], ...], list[np.ndarray]]:
        embedding = self.embeddings[self._bucket(previous, current)]
        routes = self._route(embedding)
        logits = np.zeros(256, dtype=np.float32)
        states: list[np.ndarray] = []
        for group, block in routes:
            prior = self._state_for((group, block))
            proposal = np.tanh(
                embedding @ self.block_input[group, block]
                + (prior @ self.block_left[group, block]) @ self.block_right[group, block]
            )
            state = 0.85 * prior + 0.15 * proposal
            self._states[(group, block)] = state
            states.append(state)
            logits += state @ self.block_decoder[group, block]
            logits += self.block_bias[group, block]
        logits /= max(1, len(routes))
        return logits, routes, states

    def sequence_nll(self, texts: Sequence[str]) -> float:
        losses: list[float] = []
        for text in texts:
            data = text.encode("utf-8")
            if len(data) < 2:
                continue
            self.reset_state()
            previous = 2
            for current, target in zip(data[:-1], data[1:]):
                logits, _routes, _states = self._step(previous, current)
                probabilities = self._softmax(logits)
                losses.append(-math.log(max(float(probabilities[target]), 1e-9)))
                previous = current
        return float(np.mean(losses)) if losses else 0.0

    def fit_texts(
        self,
        texts: Sequence[str],
        *,
        epochs: int = 4,
        learning_rate: float = 0.08,
        feature_learning_rate: float = 0.001,
    ) -> MobileTrainingReport:
        before = self.sequence_nll(texts)
        updates = 0
        for _ in range(epochs):
            for row in self.rng.permutation(len(texts)):
                data = texts[int(row)].encode("utf-8")
                if len(data) < 2:
                    continue
                self.reset_state()
                previous = 2
                for current, target in zip(data[:-1], data[1:]):
                    bucket = self._bucket(previous, current)
                    embedding = self.embeddings[bucket].copy()
                    logits, routes, states = self._step(previous, current)
                    probabilities = self._softmax(logits)
                    gradient = probabilities
                    gradient[target] -= 1.0
                    route_scale = 1.0 / max(1, len(routes))
                    embedding_gradient = np.zeros_like(embedding)
                    for (group, block), state in zip(routes, states):
                        decoder_before = self.block_decoder[group, block].copy()
                        state_gradient = decoder_before @ (gradient * route_scale)
                        self.block_decoder[group, block] -= learning_rate * np.outer(
                            state, gradient * route_scale
                        )
                        self.block_bias[group, block] -= learning_rate * gradient * route_scale
                        local = state_gradient * (1.0 - state**2) * 0.15
                        embedding_gradient += self.block_input[group, block] @ local
                        self.block_input[group, block] -= feature_learning_rate * np.outer(
                            embedding, local
                        )
                    self.embeddings[bucket] -= feature_learning_rate * embedding_gradient
                    previous = current
                    updates += 1
        after = self.sequence_nll(texts)
        return MobileTrainingReport(len(texts), updates, before, after)

    def remember(self, prompt: str, response: str) -> None:
        self.memory.remember(prompt, response)

    def generate(self, prompt: str, max_bytes: int = 160) -> str:
        recalled = self.memory.recall(prompt)
        if recalled is not None:
            return recalled
        data = prompt.encode("utf-8")
        self.reset_state()
        previous = 2
        current = 2
        for byte in data:
            previous, current = current, byte
            self._step(previous, current)
        output = bytearray()
        for _ in range(max_bytes):
            logits, _routes, _states = self._step(previous, current)
            next_byte = int(logits.argmax())
            if next_byte in (0, 3) or next_byte == ord("\n"):
                break
            output.append(next_byte)
            previous, current = current, next_byte
        return output.decode("utf-8", errors="ignore") or "（まだ十分に学習されていません）"

    def host_reference_benchmark(self, steps: int = 300) -> dict[str, float]:
        self.reset_state()
        previous, current = 2, ord("a")
        started = time.perf_counter()
        for _ in range(steps):
            logits, _routes, _states = self._step(previous, current)
            next_byte = int(logits.argmax())
            previous, current = current, next_byte
        elapsed = time.perf_counter() - started
        return {
            "steps": float(steps),
            "seconds": elapsed,
            "byte_steps_per_second": steps / max(elapsed, 1e-9),
            "mean_step_ms": 1000.0 * elapsed / max(1, steps),
        }

    def report(self) -> dict[str, object]:
        return {
            "profile": self.profile.static_gate(),
            "allocated_reference_bytes": sum(
                array.nbytes
                for array in (
                    self.embeddings,
                    self.coarse_router,
                    self.fine_router,
                    self.block_input,
                    self.block_left,
                    self.block_right,
                    self.block_decoder,
                    self.block_bias,
                )
            ),
            "active_state_cache_blocks": len(self._states),
            "transformer_used": False,
            "dense_attention_used": False,
            "highschool_level_passed": False,
            "mobile_device_gate_passed": False,
        }
