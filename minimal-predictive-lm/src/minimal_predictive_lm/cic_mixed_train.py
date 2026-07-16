from __future__ import annotations

import gc
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from .cic_artifact import CICArtifact, artifact_accuracy
from .cic_choice_data import load_choice_dataset, stable_choice_split
from .cic_choice_model import (
    QuantizedChoiceMechanism,
    choice_accuracy,
    train_choice_mechanism,
)
from .cic_mixed_artifact import MixedCICArtifact
from .cic_training import (
    choose_epochs,
    compile_candidates,
    load_mawps,
    stable_outer_split,
    train_raw_model,
)


@dataclass(frozen=True)
class ChoiceConfig:
    name: str
    dimensions: int
    hash_replicas: int
    epochs: int
    aggressiveness: float
    top_weights: int
    quantization_limit: int = 63

    @property
    def training_key(self) -> tuple[int, int, int, float]:
        return (
            self.dimensions,
            self.hash_replicas,
            self.epochs,
            self.aggressiveness,
        )


BASELINE_CONFIG = ChoiceConfig(
    "cic_005_single_64k_8k",
    dimensions=65536,
    hash_replicas=1,
    epochs=3,
    aggressiveness=0.25,
    top_weights=8192,
)

DUAL_HASH_CONFIGS = (
    BASELINE_CONFIG,
    ChoiceConfig(
        "cic_006_dual_128k_8k",
        dimensions=131072,
        hash_replicas=2,
        epochs=3,
        aggressiveness=0.25,
        top_weights=8192,
    ),
    ChoiceConfig(
        "cic_006_dual_128k_12k",
        dimensions=131072,
        hash_replicas=2,
        epochs=3,
        aggressiveness=0.25,
        top_weights=12288,
    ),
    ChoiceConfig(
        "cic_006_dual_128k_16k",
        dimensions=131072,
        hash_replicas=2,
        epochs=3,
        aggressiveness=0.25,
        top_weights=16384,
    ),
    ChoiceConfig(
        "cic_006_dual_soft_128k_16k",
        dimensions=131072,
        hash_replicas=2,
        epochs=4,
        aggressiveness=0.10,
        top_weights=16384,
    ),
)


@dataclass
class MixedTrainingResult:
    artifact: MixedCICArtifact
    math_correct: int
    math_total: int
    math_work: float
    math_mechanisms: int
    math_epochs: int
    math_validation: dict[int, float]
    math_expansions: int
    choice_train_rows: int
    choice_test_rows: int
    choice_correct: int
    choice_work: float
    majority_correct: int
    choice_nonzero_weights: int
    cic_005_correct: int
    selected_config_name: str
    selected_config: dict[str, object]
    candidate_configs: dict[str, dict[str, object]]
    inner_dual_hash_validation: dict[str, float]


def _fit_quantized(rows, config: ChoiceConfig) -> QuantizedChoiceMechanism:
    raw = train_choice_mechanism(
        rows,
        epochs=config.epochs,
        dimensions=config.dimensions,
        aggressiveness=config.aggressiveness,
        hash_replicas=config.hash_replicas,
    )
    return QuantizedChoiceMechanism.from_raw(
        raw,
        quantization_limit=config.quantization_limit,
        top_weights=config.top_weights,
    )


def _select_dual_hash(choice_train) -> tuple[ChoiceConfig, dict[str, float]]:
    inner_train, inner_validation = stable_choice_split(
        choice_train,
        test_threshold=1500,
        namespace="dual-hash-selection:",
    )
    grouped: dict[tuple[int, int, int, float], list[ChoiceConfig]] = defaultdict(list)
    for config in DUAL_HASH_CONFIGS:
        grouped[config.training_key].append(config)

    scores: dict[str, float] = {}
    for (
        dimensions,
        hash_replicas,
        epochs,
        aggressiveness,
    ), configs in grouped.items():
        raw = train_choice_mechanism(
            inner_train,
            epochs=epochs,
            dimensions=dimensions,
            aggressiveness=aggressiveness,
            hash_replicas=hash_replicas,
        )
        for config in configs:
            quantized = QuantizedChoiceMechanism.from_raw(
                raw,
                quantization_limit=config.quantization_limit,
                top_weights=config.top_weights,
            )
            correct, total, _work = choice_accuracy(quantized, inner_validation)
            scores[config.name] = correct / total if total else 0.0
        del raw
        gc.collect()

    selected = max(
        DUAL_HASH_CONFIGS,
        key=lambda config: (
            scores[config.name],
            -config.top_weights,
            -config.hash_replicas,
            -config.dimensions,
            -config.epochs,
        ),
    )
    return selected, scores


def train_mixed(
    mawps_path: str | Path,
    commonsense_train_path: str | Path,
    commonsense_test_path: str | Path | None = None,
) -> MixedTrainingResult:
    math_rows = load_mawps(mawps_path)
    math_train_raw, math_test_raw = stable_outer_split(math_rows)
    math_train, expansions = compile_candidates(math_train_raw)
    math_epochs, math_validation = choose_epochs(math_train)
    math_model = train_raw_model(math_train, epochs=math_epochs)
    arithmetic = CICArtifact.from_raw(
        math_model,
        top_weights=512,
        quantization_limit=7,
        metadata={"variant": "compact", "selected_epochs": math_epochs},
    )
    math_correct, math_total, math_work = artifact_accuracy(arithmetic, math_test_raw)

    choice_train = load_choice_dataset(commonsense_train_path)
    if commonsense_test_path is None:
        choice_train, choice_test = stable_choice_split(choice_train)
    else:
        choice_test = load_choice_dataset(commonsense_test_path)

    selected_config, validation_scores = _select_dual_hash(choice_train)

    cic_005 = _fit_quantized(choice_train, BASELINE_CONFIG)
    cic_005_correct, _baseline_total, _baseline_work = choice_accuracy(
        cic_005,
        choice_test,
    )

    if selected_config == BASELINE_CONFIG:
        choice = cic_005
    else:
        choice = _fit_quantized(choice_train, selected_config)
    choice_correct, _choice_total, choice_work = choice_accuracy(choice, choice_test)

    majority_index = Counter(row.answer_index for row in choice_train).most_common(1)[0][0]
    majority_correct = sum(row.answer_index == majority_index for row in choice_test)

    artifact = MixedCICArtifact(
        arithmetic,
        choice,
        {
            "capability_id": "CIC-006-DUALHASH",
            "selected_config": asdict(selected_config),
            "selection_scope": "official_train_inner_split_only",
        },
    )
    return MixedTrainingResult(
        artifact=artifact,
        math_correct=math_correct,
        math_total=math_total,
        math_work=math_work,
        math_mechanisms=len(arithmetic.mechanisms),
        math_epochs=math_epochs,
        math_validation=math_validation,
        math_expansions=expansions,
        choice_train_rows=len(choice_train),
        choice_test_rows=len(choice_test),
        choice_correct=choice_correct,
        choice_work=choice_work,
        majority_correct=majority_correct,
        choice_nonzero_weights=len(choice.weights),
        cic_005_correct=cic_005_correct,
        selected_config_name=selected_config.name,
        selected_config=asdict(selected_config),
        candidate_configs={config.name: asdict(config) for config in DUAL_HASH_CONFIGS},
        inner_dual_hash_validation=validation_scores,
    )
