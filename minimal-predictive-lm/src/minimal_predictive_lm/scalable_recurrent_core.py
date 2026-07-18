from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class ModelProfile:
    """Explicit capacity and resource plan for one model scale."""

    name: str
    vocab_buckets: int
    embedding_dim: int
    latent_dim: int
    recurrent_rank: int
    memory_slots: int
    memory_key_dim: int
    memory_value_bytes: int
    parameter_dtype_bytes: int = 2
    embedding_dtype_bytes: int = 1
    memory_dtype_bytes: int = 1
    optimizer_multiplier: float = 3.0

    def persistent_bytes(self) -> int:
        embedding = self.vocab_buckets * self.embedding_dim * self.embedding_dtype_bytes
        input_projection = self.embedding_dim * self.latent_dim * self.parameter_dtype_bytes
        recurrent = 2 * self.latent_dim * self.recurrent_rank * self.parameter_dtype_bytes
        decoder = self.latent_dim * 256 * self.parameter_dtype_bytes
        biases_and_state = (self.latent_dim + 256) * self.parameter_dtype_bytes
        memory = self.memory_slots * (
            self.memory_key_dim * self.memory_dtype_bytes + self.memory_value_bytes
        )
        return int(
            embedding
            + input_projection
            + recurrent
            + decoder
            + biases_and_state
            + memory
        )

    def training_peak_bytes(
        self, sequence_length: int = 1024, batch_size: int = 4
    ) -> int:
        parameters = self.persistent_bytes()
        optimizer = int(parameters * self.optimizer_multiplier)
        activations = batch_size * sequence_length * self.latent_dim * 4
        return parameters + optimizer + activations


CI_PROFILE = ModelProfile(
    name="ci-smoke-not-a-high-school-candidate",
    vocab_buckets=4096,
    embedding_dim=32,
    latent_dim=96,
    recurrent_rank=16,
    memory_slots=128,
    memory_key_dim=32,
    memory_value_bytes=64,
    parameter_dtype_bytes=4,
    embedding_dtype_bytes=4,
    memory_dtype_bytes=4,
    optimizer_multiplier=1.0,
)

LOCAL_4060_PROFILE = ModelProfile(
    name="local-rtx4060-first-serious-candidate",
    vocab_buckets=262_144,
    embedding_dim=256,
    latent_dim=4_096,
    recurrent_rank=256,
    memory_slots=131_072,
    memory_key_dim=256,
    memory_value_bytes=512,
    parameter_dtype_bytes=2,
    embedding_dtype_bytes=1,
    memory_dtype_bytes=1,
    optimizer_multiplier=6.0,
)

SCALE_PROFILE = ModelProfile(
    name="scale-after-local-transfer",
    vocab_buckets=1_048_576,
    embedding_dim=384,
    latent_dim=8_192,
    recurrent_rank=512,
    memory_slots=262_144,
    memory_key_dim=384,
    memory_value_bytes=768,
    parameter_dtype_bytes=2,
    embedding_dtype_bytes=1,
    memory_dtype_bytes=1,
    optimizer_multiplier=6.0,
)


@dataclass(frozen=True)
class TrainingReport:
    examples: int
    bytes_seen: int
    nll_before: float
    nll_after: float
    updates: int


class SparseEpisodicMemory:
    """Task-name-free associative memory over hashed UTF-8 byte n-grams."""

    def __init__(self, key_dim: int, max_slots: int) -> None:
        if key_dim <= 0 or max_slots <= 0:
            raise ValueError("key_dim and max_slots must be positive")
        self.key_dim = key_dim
        self.max_slots = max_slots
        self._keys: list[np.ndarray] = []
        self._values: list[bytes] = []

    @staticmethod
    def _ngrams(data: bytes) -> Iterable[bytes]:
        padded = b"\x02" + data + b"\x03"
        for width in (1, 2, 3, 4):
            for start in range(max(0, len(padded) - width + 1)):
                yield padded[start : start + width]

    def encode(self, text: str) -> np.ndarray:
        vector = np.zeros(self.key_dim, dtype=np.float32)
        for gram in self._ngrams(text.encode("utf-8")):
            digest = hashlib.blake2b(
                gram, digest_size=8, person=b"mpm-mem"
            ).digest()
            raw = int.from_bytes(digest, "little")
            index = raw % self.key_dim
            vector[index] += 1.0 if raw & (1 << 63) else -1.0
        norm = float(np.linalg.norm(vector))
        if norm:
            vector /= norm
        return vector

    def remember(self, prompt: str, response: str) -> None:
        key = self.encode(prompt)
        value = response.encode("utf-8")
        if len(self._keys) >= self.max_slots:
            self._keys.pop(0)
            self._values.pop(0)
        self._keys.append(key)
        self._values.append(value)

    def recall(self, prompt: str, minimum_similarity: float = 0.82) -> str | None:
        if not self._keys:
            return None
        query = self.encode(prompt)
        similarities = np.asarray(
            [float(key @ query) for key in self._keys], dtype=np.float32
        )
        index = int(similarities.argmax())
        if float(similarities[index]) < minimum_similarity:
            return None
        return self._values[index].decode("utf-8")

    @property
    def slots(self) -> int:
        return len(self._keys)

    @property
    def persistent_bytes(self) -> int:
        return sum(
            key.nbytes + len(value)
            for key, value in zip(self._keys, self._values)
        )


class MultiScaleRecurrentCore:
    """Trainable non-Transformer sequence baseline with external memory.

    The CI profile validates mechanics only. It is deliberately prohibited from being
    presented as a high-school-intelligence candidate. Serious runs must select an
    explicit larger profile and are promoted only by the frozen integrated gates.
    """

    def __init__(self, profile: ModelProfile = CI_PROFILE, seed: int = 0) -> None:
        self.profile = profile
        self.rng = np.random.default_rng(seed)
        scale = 1.0 / math.sqrt(profile.embedding_dim)
        self.embeddings = self.rng.normal(
            0.0,
            scale,
            size=(profile.vocab_buckets, profile.embedding_dim),
        ).astype(np.float32)
        self.input_projection = self.rng.normal(
            0.0,
            1.0 / math.sqrt(profile.embedding_dim),
            size=(profile.embedding_dim, profile.latent_dim),
        ).astype(np.float32)
        self.recurrent_left = self.rng.normal(
            0.0,
            1.0 / math.sqrt(profile.latent_dim),
            size=(profile.latent_dim, profile.recurrent_rank),
        ).astype(np.float32)
        self.recurrent_right = self.rng.normal(
            0.0,
            1.0 / math.sqrt(profile.recurrent_rank),
            size=(profile.recurrent_rank, profile.latent_dim),
        ).astype(np.float32)
        self.decoder = np.zeros((profile.latent_dim, 256), dtype=np.float32)
        self.decoder_bias = np.zeros(256, dtype=np.float32)
        self.memory = SparseEpisodicMemory(
            profile.memory_key_dim, profile.memory_slots
        )
        self._decay = self._build_decay(profile.latent_dim)

    @staticmethod
    def _build_decay(latent_dim: int) -> np.ndarray:
        timescales = np.asarray((0.0, 0.5, 0.9, 0.99), dtype=np.float32)
        return np.resize(timescales, latent_dim)

    def _bucket(self, previous: int, current: int) -> int:
        mixed = ((previous + 1) * 257 + current + 17) * 0x9E3779B1
        return mixed % self.profile.vocab_buckets

    def _step(
        self, state: np.ndarray, previous: int, current: int
    ) -> np.ndarray:
        embedding = self.embeddings[self._bucket(previous, current)]
        proposal = np.tanh(
            embedding @ self.input_projection
            + (state @ self.recurrent_left) @ self.recurrent_right
        )
        return self._decay * state + (1.0 - self._decay) * proposal

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        shifted = logits - float(logits.max())
        exp = np.exp(shifted)
        return exp / float(exp.sum())

    def sequence_nll(self, texts: Sequence[str]) -> float:
        losses: list[float] = []
        for text in texts:
            data = text.encode("utf-8")
            if len(data) < 2:
                continue
            state = np.zeros(self.profile.latent_dim, dtype=np.float32)
            previous = 2
            for current, target in zip(data[:-1], data[1:]):
                state = self._step(state, previous, current)
                probabilities = self._softmax(
                    state @ self.decoder + self.decoder_bias
                )
                losses.append(
                    -math.log(max(float(probabilities[target]), 1e-9))
                )
                previous = current
        return float(np.mean(losses)) if losses else 0.0

    def fit_texts(
        self,
        texts: Sequence[str],
        *,
        epochs: int = 3,
        learning_rate: float = 0.08,
        l2: float = 1e-5,
    ) -> TrainingReport:
        """Train one shared next-byte readout over mixed raw text streams."""

        before = self.sequence_nll(texts)
        updates = 0
        bytes_seen = 0
        for _ in range(epochs):
            order = self.rng.permutation(len(texts))
            for row in order:
                data = texts[int(row)].encode("utf-8")
                bytes_seen += len(data)
                if len(data) < 2:
                    continue
                state = np.zeros(self.profile.latent_dim, dtype=np.float32)
                previous = 2
                for current, target in zip(data[:-1], data[1:]):
                    state = self._step(state, previous, current)
                    probabilities = self._softmax(
                        state @ self.decoder + self.decoder_bias
                    )
                    gradient = probabilities
                    gradient[target] -= 1.0
                    self.decoder -= learning_rate * (
                        np.outer(state, gradient) + l2 * self.decoder
                    )
                    self.decoder_bias -= learning_rate * gradient
                    previous = current
                    updates += 1
        after = self.sequence_nll(texts)
        return TrainingReport(
            len(texts), bytes_seen, before, after, updates
        )

    def remember(self, prompt: str, response: str) -> None:
        self.memory.remember(prompt, response)

    def answer(
        self, prompt: str, minimum_similarity: float = 0.82
    ) -> str | None:
        return self.memory.recall(prompt, minimum_similarity)

    def resource_report(self) -> dict[str, object]:
        array_bytes = sum(
            array.nbytes
            for array in (
                self.embeddings,
                self.input_projection,
                self.recurrent_left,
                self.recurrent_right,
                self.decoder,
                self.decoder_bias,
                self._decay,
            )
        )
        return {
            "profile": asdict(self.profile),
            "allocated_array_bytes": array_bytes,
            "episodic_memory_bytes": self.memory.persistent_bytes,
            "actual_persistent_bytes": (
                array_bytes + self.memory.persistent_bytes
            ),
            "planned_quantized_persistent_bytes": (
                self.profile.persistent_bytes()
            ),
            "planned_training_peak_bytes_1024x4": (
                self.profile.training_peak_bytes()
            ),
            "transformer_used": False,
            "dense_attention_used": False,
            "task_names_supplied": False,
            "highschool_level_passed": False,
        }
