from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from .scalable_recurrent_core import (
    CI_PROFILE,
    ModelProfile,
    MultiScaleRecurrentCore,
    TrainingReport,
)


class AdaptiveMultiScaleRecurrentCore(MultiScaleRecurrentCore):
    """Jointly adapts embeddings, recurrent factors, and the byte decoder.

    The update is a bounded local recurrent gradient rather than full unrolled BPTT.
    It supplies an executable shared-learning baseline while keeping training memory
    small enough for the first local experiments. Full truncated BPTT is admitted only
    if it improves frozen multi-domain transfer enough to justify its resource cost.
    """

    def __init__(
        self, profile: ModelProfile = CI_PROFILE, seed: int = 0
    ) -> None:
        super().__init__(profile=profile, seed=seed)

    def fit_texts(
        self,
        texts: Sequence[str],
        *,
        epochs: int = 3,
        learning_rate: float = 0.08,
        feature_learning_rate: float = 0.002,
        l2: float = 1e-5,
        gradient_clip: float = 1.0,
    ) -> TrainingReport:
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
                state = np.zeros(
                    self.profile.latent_dim, dtype=np.float32
                )
                previous = 2
                for current, target in zip(data[:-1], data[1:]):
                    prior_state = state
                    bucket = self._bucket(previous, current)
                    embedding = self.embeddings[bucket].copy()
                    recurrent_hidden = prior_state @ self.recurrent_left
                    proposal = np.tanh(
                        embedding @ self.input_projection
                        + recurrent_hidden @ self.recurrent_right
                    )
                    state = (
                        self._decay * prior_state
                        + (1.0 - self._decay) * proposal
                    )
                    probabilities = self._softmax(
                        state @ self.decoder + self.decoder_bias
                    )
                    output_gradient = probabilities
                    output_gradient[target] -= 1.0

                    state_gradient = self.decoder @ output_gradient
                    proposal_gradient = (
                        state_gradient * (1.0 - self._decay)
                    )
                    preactivation_gradient = (
                        proposal_gradient * (1.0 - proposal**2)
                    )
                    norm = float(
                        np.linalg.norm(preactivation_gradient)
                    )
                    if norm > gradient_clip:
                        preactivation_gradient *= gradient_clip / norm

                    input_projection = self.input_projection.copy()
                    recurrent_right = self.recurrent_right.copy()
                    embedding_gradient = (
                        input_projection @ preactivation_gradient
                    )
                    input_gradient = np.outer(
                        embedding, preactivation_gradient
                    )
                    right_gradient = np.outer(
                        recurrent_hidden, preactivation_gradient
                    )
                    hidden_gradient = (
                        recurrent_right @ preactivation_gradient
                    )
                    left_gradient = np.outer(
                        prior_state, hidden_gradient
                    )

                    self.decoder -= learning_rate * (
                        np.outer(state, output_gradient)
                        + l2 * self.decoder
                    )
                    self.decoder_bias -= (
                        learning_rate * output_gradient
                    )
                    self.embeddings[bucket] -= (
                        feature_learning_rate * embedding_gradient
                    )
                    self.input_projection -= feature_learning_rate * (
                        input_gradient + l2 * self.input_projection
                    )
                    self.recurrent_right -= feature_learning_rate * (
                        right_gradient + l2 * self.recurrent_right
                    )
                    self.recurrent_left -= feature_learning_rate * (
                        left_gradient + l2 * self.recurrent_left
                    )
                    previous = current
                    updates += 1
        after = self.sequence_nll(texts)
        if not math.isfinite(after):
            raise FloatingPointError(
                "adaptive recurrent training produced a non-finite loss"
            )
        return TrainingReport(
            examples=len(texts),
            bytes_seen=bytes_seen,
            nll_before=before,
            nll_after=after,
            updates=updates,
        )
