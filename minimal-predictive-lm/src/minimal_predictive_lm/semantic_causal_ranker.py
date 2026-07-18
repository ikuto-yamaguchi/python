from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import random
import re
from typing import Sequence
import zlib

import numpy as np

from .generic_causal_judgement_v3 import GenericCausalJudgementV3
from .learned_causal_ranker import causal_choice_rows


@dataclass(frozen=True)
class SemanticPrediction:
    output: str
    margin: float
    score: float


@dataclass(frozen=True)
class SemanticTrainingReport:
    train_rows: int
    validation_rows: int
    selected_dimensions: int
    selected_epochs: int
    selected_policy: str
    selected_threshold: float
    validation_accuracy: float
    candidate_metrics: dict[str, dict[str, float]]
    nonzero_weights: int
    serialized_bytes: int


def _hash(token: str, dimensions: int) -> tuple[int, int]:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8, person=b"causal-v1").digest()
    raw = int.from_bytes(digest, "little")
    return raw % dimensions, 1 if raw >> 63 else -1


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())


class CausalSemanticEncoder:
    """Extract task-name-free event, norm, intent, and counterfactual features."""

    def __init__(self) -> None:
        self.engine = GenericCausalJudgementV3()

    @staticmethod
    def _add(tokens: list[str], name: str, value: object = True) -> None:
        tokens.append(f"{name}={value}")

    def tokens(self, prompt: str) -> tuple[str, ...]:
        split = self.engine._split(prompt)
        if split is None:
            return ("BIAS", "UNPARSED")
        story, question = split
        candidate = self.engine._candidate(question)
        actor = self.engine._actor(question)
        actor_norm = self.engine._actor_norm(story, question)
        other_abnormal = self.engine._other_abnormal_actor(story, question)
        omission = self.engine._omission(question)
        intentional = "intentionally" in question or "intend" in question
        has_or = bool(
            re.search(r"\bif [^.]{0,35}\beither\b|\bif anyone\b|\bat least one\b|\bif one person\b", story)
        )
        has_and = bool(
            re.search(r"\bif [^.]{0,35}\bboth\b|\bif two\b|\bif three\b|\bif more than one\b|\bif and only if\b|\bboth together\b", story)
        )
        tokens: list[str] = ["BIAS"]
        for name, value in (
            ("QUERY_INTENT", intentional),
            ("QUERY_CAUSE", "cause" in question or "because" in question),
            ("RULE_AND", has_and),
            ("RULE_OR", has_or),
            ("OMISSION", omission),
            ("OTHER_ABNORMAL", other_abnormal),
            ("ACTOR_NORM", actor_norm),
            ("ACCIDENT", self.engine._contains_any(story, self.engine._ACCIDENT)),
            ("FOREKNOWLEDGE", self.engine._contains_any(story, self.engine._FOREKNOWLEDGE)),
            ("REGRET", self.engine._contains_any(story, self.engine._REGRET)),
            ("ABNORMAL_ANY", self.engine._contains_any(story, self.engine._ABNORMAL)),
            ("NORMAL_ANY", self.engine._contains_any(story, self.engine._NORMAL)),
            ("REMOTE", any(term in candidate for term in self.engine._REMOTE_BACKGROUND)),
            ("IMMEDIATE_FATAL", self.engine._contains_any(story, self.engine._IMMEDIATE_FATAL)),
            ("ALREADY_ACTIVE", "already" in story),
            ("IMMEDIATE", "immediately" in story or "right after" in story),
            ("LATER", "later" in story or "on the way" in story),
            ("UNLIKELY", "unlikely" in story and "very likely" not in story),
            ("LIKELY", "likely" in story and "unlikely" not in story),
            ("RESPONSIBILITY", "responsibility" in story or "responsible" in story),
            ("MAINTENANCE", "oil" in story or "maintain" in story),
            ("HARM_OUTCOME", any(word in candidate for word in ("harm", "kill", "death", "injure", "damage", "hurt"))),
            ("BENEFIT_OUTCOME", any(word in candidate for word in ("help", "benefit", "fulfill", "improve", "save"))),
            ("DIRECT_INTENT", any(term in story for term in self.engine._DIRECT_INTENT)),
        ):
            self._add(tokens, name, value)

        clauses = self.engine._clauses(story)
        actor_clauses = [clause for clause in clauses if actor and actor in clause]
        self._add(tokens, "ACTOR_MENTION_COUNT", min(4, len(actor_clauses)))
        self._add(tokens, "CLAUSE_COUNT", min(12, len(clauses)))
        self._add(tokens, "CANDIDATE_LENGTH", min(12, len(_words(candidate))))

        # Question wording and the actor-centred local context provide learned lexical
        # grounding without memorizing whole narratives.
        question_words = _words(question)
        local_words = _words(" ".join(actor_clauses[-3:]))
        for word in question_words[-14:]:
            tokens.append("QW:" + word)
        for left, right in zip(question_words[-14:], question_words[-13:]):
            tokens.append("QB:" + left + ":" + right)
        for word in local_words[-24:]:
            if len(word) >= 3:
                tokens.append("AW:" + word)

        # Pairwise semantic interactions let a tiny linear learner represent rules such
        # as AND + abnormal actor, harmful + foreknowledge, or omission + responsibility.
        semantic = [token for token in tokens if not token.startswith(("QW:", "QB:", "AW:"))]
        for i, left in enumerate(semantic):
            for right in semantic[i + 1 :]:
                tokens.append("X:" + left + "&" + right)
        return tuple(tokens)

    def vector(self, prompt: str, dimensions: int) -> dict[int, float]:
        values: Counter[int] = Counter()
        for token in self.tokens(prompt):
            index, sign = _hash(token, dimensions)
            values[index] += sign
        return {index: float(max(-6, min(6, value))) for index, value in values.items()}


@dataclass(frozen=True)
class QuantizedSemanticCausalRanker:
    dimensions: int
    scale: float
    weights: dict[int, int]
    policy: str
    threshold: float
    metadata: dict[str, object]

    def score(self, prompt: str) -> float:
        features = CausalSemanticEncoder().vector(prompt, self.dimensions)
        return self.scale * sum(self.weights.get(index, 0) * value for index, value in features.items())

    def predict(self, prompt: str) -> SemanticPrediction:
        score = self.score(prompt)
        return SemanticPrediction("Yes" if score >= 0 else "No", abs(score), score)

    @property
    def description_bits(self) -> int:
        return len(self.to_bytes()) * 8

    def to_bytes(self) -> bytes:
        raw = json.dumps(
            {
                "format": "semantic-causal-ranker-v1",
                "dimensions": self.dimensions,
                "scale": self.scale,
                "weights": {str(k): v for k, v in self.weights.items()},
                "policy": self.policy,
                "threshold": self.threshold,
                "metadata": self.metadata,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "QuantizedSemanticCausalRanker":
        row = json.loads(zlib.decompress(data))
        return cls(
            int(row["dimensions"]),
            float(row["scale"]),
            {int(k): int(v) for k, v in row["weights"].items()},
            str(row["policy"]),
            float(row["threshold"]),
            dict(row.get("metadata", {})),
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "QuantizedSemanticCausalRanker":
        return cls.from_bytes(Path(path).read_bytes())


def _train_float(prompts: Sequence[str], labels: Sequence[int], dimensions: int, epochs: int) -> np.ndarray:
    encoder = CausalSemanticEncoder()
    cached = [encoder.vector(prompt, dimensions) for prompt in prompts]
    weights = np.zeros(dimensions, dtype=np.float32)
    totals = np.zeros(dimensions, dtype=np.float64)
    timestamps = np.zeros(dimensions, dtype=np.int64)
    generator = random.Random(29)
    step = 0
    for _epoch in range(epochs):
        order = list(range(len(prompts)))
        generator.shuffle(order)
        for row in order:
            step += 1
            features = cached[row]
            indices = np.fromiter(features.keys(), dtype=np.int32)
            values = np.fromiter(features.values(), dtype=np.float32)
            target = 1.0 if labels[row] == 0 else -1.0
            score = float(weights[indices] @ values) if len(indices) else 0.0
            margin = target * score
            if margin >= 1.0:
                continue
            norm = float(values @ values) + 1e-9
            rate = min(0.25, (1.0 - margin) / norm)
            totals[indices] += (step - timestamps[indices]) * weights[indices]
            timestamps[indices] = step
            weights[indices] += rate * target * values
    if step:
        totals += (step + 1 - timestamps) * weights
        return (totals / (step + 1)).astype(np.float32)
    return weights


def _quantize(weights: np.ndarray, top_weights: int = 8192) -> tuple[float, dict[int, int]]:
    nonzero = np.flatnonzero(np.abs(weights) > 1e-8)
    ordered = nonzero[np.argsort(np.abs(weights[nonzero]))[::-1]][:top_weights]
    maximum = float(np.abs(weights[ordered]).max()) if len(ordered) else 0.0
    scale = maximum / 63.0 if maximum else 1.0
    quantized = {
        int(index): int(round(float(weights[index]) / scale))
        for index in ordered
        if int(round(float(weights[index]) / scale)) != 0
    }
    return scale, quantized


def _combine(policy: str, threshold: float, learned: SemanticPrediction, symbolic: str | None) -> str:
    if policy == "learned_always":
        return learned.output
    if policy == "symbolic_first":
        return symbolic or learned.output
    if policy == "learned_margin":
        return learned.output if learned.margin >= threshold else (symbolic or learned.output)
    raise ValueError(policy)


def train_semantic_causal_ranker(
    document: dict[str, object],
    *,
    train_stop: int = 120,
    development_stop: int = 142,
) -> tuple[QuantizedSemanticCausalRanker, SemanticTrainingReport]:
    rows = causal_choice_rows(document, development_stop)
    if len(rows) != development_stop:
        raise ValueError("semantic causal development rows changed")
    symbolic = GenericCausalJudgementV3()
    configs = ((4096, 4), (8192, 6), (16384, 8))
    policies = (
        ("learned_always", 0.0),
        ("learned_margin", 0.25),
        ("learned_margin", 0.75),
        ("learned_margin", 1.50),
        ("symbolic_first", 0.0),
    )
    metrics: dict[str, dict[str, float]] = {}
    selected: tuple[float, int, int, str, float] | None = None
    train = rows[:train_stop]
    validation = rows[train_stop:development_stop]
    for dimensions, epochs in configs:
        weights = _train_float(
            [row.raw_question for row in train],
            [row.answer_index for row in train],
            dimensions,
            epochs,
        )
        scale, quantized = _quantize(weights)
        candidate = QuantizedSemanticCausalRanker(dimensions, scale, quantized, "learned_always", 0.0, {})
        cached = [
            (candidate.predict(row.raw_question), symbolic.answer(row.raw_question).output, row.answer_index)
            for row in validation
        ]
        for policy, threshold in policies:
            correct = sum(
                int((_combine(policy, threshold, learned, symbolic_output) == "Yes") == (gold == 0))
                for learned, symbolic_output, gold in cached
            )
            accuracy = correct / len(cached)
            name = f"d{dimensions}-e{epochs}:{policy}:{threshold:.2f}"
            metrics[name] = {"accuracy": accuracy, "correct": correct, "rows": len(cached), "weights": len(quantized)}
            key = (accuracy, -len(quantized), -dimensions, policy, -threshold)
            if selected is None or key > (selected[0], -selected[1], -selected[2], selected[3], -selected[4]):
                selected = (accuracy, len(quantized), dimensions, policy, threshold)
    if selected is None:
        raise RuntimeError("no semantic causal candidate")
    accuracy, _weight_count, dimensions, policy, threshold = selected
    epochs = next(epoch for dim, epoch in configs if dim == dimensions)
    final_weights = _train_float(
        [row.raw_question for row in rows],
        [row.answer_index for row in rows],
        dimensions,
        epochs,
    )
    scale, quantized = _quantize(final_weights)
    model = QuantizedSemanticCausalRanker(
        dimensions,
        scale,
        quantized,
        policy,
        threshold,
        {
            "selection_train_rows": train_stop,
            "selection_validation_rows": development_stop - train_stop,
            "final_training_rows": development_stop,
            "tail_targets_used": 0,
            "semantic_encoder": "event-norm-intent-counterfactual-v1",
        },
    )
    report = SemanticTrainingReport(
        train_stop,
        development_stop - train_stop,
        dimensions,
        epochs,
        policy,
        threshold,
        accuracy,
        metrics,
        len(quantized),
        len(model.to_bytes()),
    )
    return model, report


def combine_semantic_prediction(
    model: QuantizedSemanticCausalRanker, prompt: str, symbolic: str | None
) -> str:
    return _combine(model.policy, model.threshold, model.predict(prompt), symbolic)
