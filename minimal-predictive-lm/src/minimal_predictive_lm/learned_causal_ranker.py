from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Callable, Sequence
import zlib

from .cic_choice_data import ChoiceExample, choice_features
from .cic_choice_model import QuantizedChoiceMechanism, _dot, train_choice_mechanism


@dataclass(frozen=True)
class CausalRankerConfig:
    name: str
    dimensions: int
    hash_replicas: int
    epochs: int
    aggressiveness: float
    top_weights: int


@dataclass(frozen=True)
class CausalRankerPrediction:
    output: str
    margin: float
    yes_score: float
    no_score: float


@dataclass(frozen=True)
class CausalRankerTrainingReport:
    train_rows: int
    validation_rows: int
    selected_config: str
    selected_policy: str
    selected_threshold: float
    validation_accuracy: float
    candidate_metrics: dict[str, dict[str, float]]
    final_nonzero_weights: int
    serialized_bytes: int


CONFIGS = (
    CausalRankerConfig("causal-64k-r2-e4", 65_536, 2, 4, 0.25, 16_384),
    CausalRankerConfig("causal-128k-r2-e6", 131_072, 2, 6, 0.20, 24_576),
    CausalRankerConfig("causal-262k-r4-e8", 262_144, 4, 8, 0.16, 32_768),
)
POLICIES = (
    ("learned_always", 0.0),
    ("learned_margin", 0.20),
    ("learned_margin", 0.50),
    ("learned_margin", 1.00),
    ("symbolic_first", 0.0),
)


def causal_choice_rows(document: dict[str, object], stop: int) -> list[ChoiceExample]:
    raw_rows = document.get("examples")
    if not isinstance(raw_rows, list):
        raise ValueError("causal document has no examples")
    result: list[ChoiceExample] = []
    for raw in raw_rows[:stop]:
        if not isinstance(raw, dict):
            continue
        prompt = str(raw.get("input", ""))
        target = str(raw.get("target", "")).strip()
        if target == "(A)":
            answer_index = 0
        elif target == "(B)":
            answer_index = 1
        else:
            continue
        stem = prompt.split("\nOptions:", 1)[0].strip()
        result.append(ChoiceExample(prompt, stem, ("Yes", "No"), answer_index))
    return result


@dataclass(frozen=True)
class QuantizedCausalRanker:
    mechanism: QuantizedChoiceMechanism
    policy: str
    threshold: float
    metadata: dict[str, object]

    def _score(self, stem: str, option: str, position: int) -> float:
        features = choice_features(
            stem,
            option,
            position,
            dimensions=self.mechanism.dimensions,
            hash_replicas=self.mechanism.hash_replicas,
            relation_scope=self.mechanism.relation_scope,
        )
        return self.mechanism.scale * _dot(self.mechanism.weights, features)

    def predict(self, prompt: str) -> CausalRankerPrediction:
        stem = prompt.split("\nOptions:", 1)[0].strip()
        yes = self._score(stem, "Yes", 0)
        no = self._score(stem, "No", 1)
        output = "Yes" if yes >= no else "No"
        return CausalRankerPrediction(output, abs(yes - no), yes, no)

    @property
    def description_bits(self) -> int:
        return len(self.to_bytes()) * 8

    def to_bytes(self) -> bytes:
        payload = {
            "format": "quantized-causal-ranker-v1",
            "policy": self.policy,
            "threshold": self.threshold,
            "metadata": self.metadata,
            "mechanism": {
                "dimensions": self.mechanism.dimensions,
                "scale": self.mechanism.scale,
                "weights": {str(k): v for k, v in self.mechanism.weights.items()},
                "hash_replicas": self.mechanism.hash_replicas,
                "relation_scope": self.mechanism.relation_scope,
            },
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "QuantizedCausalRanker":
        payload = json.loads(zlib.decompress(data))
        mechanism = payload["mechanism"]
        return cls(
            QuantizedChoiceMechanism(
                dimensions=int(mechanism["dimensions"]),
                scale=float(mechanism["scale"]),
                weights={int(k): int(v) for k, v in mechanism["weights"].items()},
                hash_replicas=int(mechanism["hash_replicas"]),
                relation_scope=str(mechanism["relation_scope"]),
            ),
            str(payload["policy"]),
            float(payload["threshold"]),
            dict(payload.get("metadata", {})),
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "QuantizedCausalRanker":
        return cls.from_bytes(Path(path).read_bytes())


def _fit(rows: Sequence[ChoiceExample], config: CausalRankerConfig) -> QuantizedChoiceMechanism:
    raw = train_choice_mechanism(
        rows,
        epochs=config.epochs,
        dimensions=config.dimensions,
        aggressiveness=config.aggressiveness,
        hash_replicas=config.hash_replicas,
        relation_scope="full",
        seed=17,
    )
    return QuantizedChoiceMechanism.from_raw(raw, top_weights=config.top_weights, quantization_limit=63)


def _combine(
    policy: str,
    threshold: float,
    learned: CausalRankerPrediction,
    symbolic: str | None,
) -> str:
    if policy == "learned_always":
        return learned.output
    if policy == "symbolic_first":
        return symbolic or learned.output
    if policy == "learned_margin":
        return learned.output if learned.margin >= threshold else (symbolic or learned.output)
    raise ValueError(f"unknown causal policy: {policy}")


def train_causal_ranker(
    document: dict[str, object],
    symbolic_factory: Callable[[], object],
    *,
    train_stop: int = 120,
    development_stop: int = 142,
) -> tuple[QuantizedCausalRanker, CausalRankerTrainingReport]:
    rows = causal_choice_rows(document, development_stop)
    if len(rows) != development_stop:
        raise ValueError("causal development rows changed")
    train_rows = rows[:train_stop]
    validation_rows = rows[train_stop:development_stop]
    metrics: dict[str, dict[str, float]] = {}
    best: tuple[float, float, int, str, float, CausalRankerConfig] | None = None

    for config in CONFIGS:
        mechanism = _fit(train_rows, config)
        candidate = QuantizedCausalRanker(mechanism, "learned_always", 0.0, {})
        symbolic_engine = symbolic_factory()
        cached: list[tuple[CausalRankerPrediction, str | None, int]] = []
        for row in validation_rows:
            learned = candidate.predict(row.raw_question)
            symbolic_prediction = symbolic_engine.answer(row.raw_question).output
            cached.append((learned, symbolic_prediction, row.answer_index))
        for policy, threshold in POLICIES:
            correct = 0
            for learned, symbolic, answer_index in cached:
                output = _combine(policy, threshold, learned, symbolic)
                correct += int((output == "Yes") == (answer_index == 0))
            accuracy = correct / len(cached) if cached else 0.0
            key = f"{config.name}:{policy}:{threshold:.2f}"
            metrics[key] = {
                "accuracy": accuracy,
                "correct": float(correct),
                "rows": float(len(cached)),
                "weights": float(len(mechanism.weights)),
            }
            candidate_key = (
                accuracy,
                -threshold,
                -len(mechanism.weights),
                policy,
                threshold,
                config,
            )
            if best is None or candidate_key > best:
                best = candidate_key

    if best is None:
        raise RuntimeError("no causal ranker candidate")
    accuracy, _neg_threshold, _neg_weights, policy, threshold, config = best
    final_mechanism = _fit(rows, config)
    model = QuantizedCausalRanker(
        final_mechanism,
        policy,
        threshold,
        {
            "selected_config": asdict(config),
            "selection_train_rows": train_stop,
            "selection_validation_rows": development_stop - train_stop,
            "final_training_rows": development_stop,
            "final_tail_targets_used": 0,
            "strict_unseen_claim_allowed": False,
        },
    )
    report = CausalRankerTrainingReport(
        train_rows=train_stop,
        validation_rows=development_stop - train_stop,
        selected_config=config.name,
        selected_policy=policy,
        selected_threshold=threshold,
        validation_accuracy=accuracy,
        candidate_metrics=metrics,
        final_nonzero_weights=len(final_mechanism.weights),
        serialized_bytes=len(model.to_bytes()),
    )
    return model, report


def combine_causal_prediction(
    model: QuantizedCausalRanker,
    prompt: str,
    symbolic: str | None,
) -> str:
    learned = model.predict(prompt)
    return _combine(model.policy, model.threshold, learned, symbolic)
