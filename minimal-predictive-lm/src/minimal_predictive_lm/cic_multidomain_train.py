from __future__ import annotations

import gc
import hashlib
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from .cic_artifact import CICArtifact, artifact_accuracy
from .cic_choice_data import ChoiceExample, load_choice_dataset, stable_choice_split
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

CIC006_VALIDATION_ROWS = 1119
CIC006_VALIDATION_CORRECT = 313


@dataclass(frozen=True)
class MultiDomainConfig:
    name: str
    relation_scope: str
    top_weights: int
    dimensions: int = 131072
    hash_replicas: int = 2
    epochs: int = 3
    aggressiveness: float = 0.25
    quantization_limit: int = 63

    @property
    def training_key(self) -> tuple[int, int, int, float, str]:
        return (
            self.dimensions,
            self.hash_replicas,
            self.epochs,
            self.aggressiveness,
            self.relation_scope,
        )


MULTIDOMAIN_CONFIGS = (
    MultiDomainConfig("cic_007_joint_tail_12k", "tail", 12288),
    MultiDomainConfig(
        "cic_007_joint_adaptive_12k",
        "adaptive",
        12288,
        aggressiveness=0.20,
    ),
    MultiDomainConfig(
        "cic_007_joint_adaptive_16k",
        "adaptive",
        16384,
        aggressiveness=0.20,
    ),
    MultiDomainConfig(
        "cic_007_joint_adaptive_256k_16k",
        "adaptive",
        16384,
        dimensions=262144,
        aggressiveness=0.20,
    ),
)


@dataclass
class MultiDomainTrainingResult:
    artifact: MixedCICArtifact
    math_correct: int
    math_total: int
    math_work: float
    math_mechanisms: int
    math_epochs: int
    math_validation: dict[int, float]
    math_expansions: int
    commonsense_train_rows: int
    commonsense_test_rows: int
    jnli_train_rows: int
    jnli_test_rows: int
    joint_train_rows: int
    commonsense_correct: int
    commonsense_work: float
    jnli_correct: int
    jnli_work: float
    commonsense_majority_correct: int
    jnli_majority_correct: int
    cic_006_commonsense_correct: int
    choice_nonzero_weights: int
    selected_config_name: str
    selected_config: dict[str, object]
    candidate_configs: dict[str, dict[str, object]]
    inner_validation: dict[str, dict[str, float]]


def _stable_sample(
    rows: Sequence[ChoiceExample],
    limit: int,
    namespace: str,
) -> list[ChoiceExample]:
    if len(rows) <= limit:
        return list(rows)
    return sorted(
        rows,
        key=lambda row: hashlib.sha256(
            (namespace + row.raw_question).encode("utf-8")
        ).digest(),
    )[:limit]


def _balanced_interleave(
    first: Sequence[ChoiceExample],
    second: Sequence[ChoiceExample],
    *,
    namespace: str,
    max_per_domain: int = 9000,
) -> list[ChoiceExample]:
    count = min(len(first), len(second), max_per_domain)
    left = _stable_sample(first, count, namespace + ":left:")
    right = _stable_sample(second, count, namespace + ":right:")
    result: list[ChoiceExample] = []
    for index in range(count):
        result.append(left[index])
        result.append(right[index])
    return result


def _majority_correct(rows: Sequence[ChoiceExample]) -> int:
    if not rows:
        return 0
    majority = Counter(row.answer_index for row in rows).most_common(1)[0][0]
    return sum(row.answer_index == majority for row in rows)


def _fit_quantized(
    rows: Sequence[ChoiceExample],
    config: MultiDomainConfig,
) -> QuantizedChoiceMechanism:
    raw = train_choice_mechanism(
        rows,
        epochs=config.epochs,
        dimensions=config.dimensions,
        aggressiveness=config.aggressiveness,
        hash_replicas=config.hash_replicas,
        relation_scope=config.relation_scope,
    )
    return QuantizedChoiceMechanism.from_raw(
        raw,
        quantization_limit=config.quantization_limit,
        top_weights=config.top_weights,
    )


def _select_multidomain_config(
    commonsense_train: Sequence[ChoiceExample],
    jnli_train: Sequence[ChoiceExample],
) -> tuple[MultiDomainConfig, dict[str, dict[str, float]]]:
    cs_inner_train, cs_inner_valid = stable_choice_split(
        commonsense_train,
        test_threshold=1500,
        namespace="multidomain-cs-inner:",
    )
    nli_inner_train, nli_inner_valid = stable_choice_split(
        jnli_train,
        test_threshold=1500,
        namespace="multidomain-nli-inner:",
    )
    joint_inner_train = _balanced_interleave(
        cs_inner_train,
        nli_inner_train,
        namespace="multidomain-inner-balance",
    )
    cs_majority = _majority_correct(cs_inner_valid) / len(cs_inner_valid)
    nli_majority = _majority_correct(nli_inner_valid) / len(nli_inner_valid)

    grouped: dict[
        tuple[int, int, int, float, str], list[MultiDomainConfig]
    ] = defaultdict(list)
    for config in MULTIDOMAIN_CONFIGS:
        grouped[config.training_key].append(config)

    metrics: dict[str, dict[str, float]] = {}
    for (
        dimensions,
        hash_replicas,
        epochs,
        aggressiveness,
        relation_scope,
    ), configs in grouped.items():
        raw = train_choice_mechanism(
            joint_inner_train,
            epochs=epochs,
            dimensions=dimensions,
            aggressiveness=aggressiveness,
            hash_replicas=hash_replicas,
            relation_scope=relation_scope,
        )
        for config in configs:
            quantized = QuantizedChoiceMechanism.from_raw(
                raw,
                quantization_limit=config.quantization_limit,
                top_weights=config.top_weights,
            )
            cs_correct, cs_total, _ = choice_accuracy(quantized, cs_inner_valid)
            nli_correct, nli_total, _ = choice_accuracy(quantized, nli_inner_valid)
            cs_accuracy = cs_correct / cs_total if cs_total else 0.0
            nli_accuracy = nli_correct / nli_total if nli_total else 0.0
            cs_gain = cs_accuracy - cs_majority
            nli_gain = nli_accuracy - nli_majority
            metrics[config.name] = {
                "commonsense_accuracy": cs_accuracy,
                "jnli_accuracy": nli_accuracy,
                "commonsense_gain_over_majority": cs_gain,
                "jnli_gain_over_majority": nli_gain,
                "macro_gain_over_majority": (cs_gain + nli_gain) / 2.0,
                "minimum_gain_over_majority": min(cs_gain, nli_gain),
            }
        del raw
        gc.collect()

    selected = max(
        MULTIDOMAIN_CONFIGS,
        key=lambda config: (
            metrics[config.name]["macro_gain_over_majority"],
            metrics[config.name]["minimum_gain_over_majority"],
            -config.top_weights,
            -config.dimensions,
        ),
    )
    return selected, metrics


def train_multidomain(
    mawps_path: str | Path,
    commonsense_train_path: str | Path,
    commonsense_test_path: str | Path,
    jnli_train_path: str | Path,
    jnli_test_path: str | Path,
) -> MultiDomainTrainingResult:
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

    commonsense_train = load_choice_dataset(commonsense_train_path)
    commonsense_test = load_choice_dataset(commonsense_test_path)
    jnli_train = load_choice_dataset(jnli_train_path)
    jnli_test = load_choice_dataset(jnli_test_path)
    if len(commonsense_test) != CIC006_VALIDATION_ROWS:
        raise ValueError("JCommonsenseQA validation no longer matches frozen CIC-006 result")

    selected_config, inner_validation = _select_multidomain_config(
        commonsense_train,
        jnli_train,
    )
    joint_train = _balanced_interleave(
        commonsense_train,
        jnli_train,
        namespace="multidomain-full-balance",
    )
    joint_model = _fit_quantized(joint_train, selected_config)
    commonsense_correct, _cs_total, commonsense_work = choice_accuracy(
        joint_model,
        commonsense_test,
    )
    jnli_correct, _nli_total, jnli_work = choice_accuracy(joint_model, jnli_test)

    artifact = MixedCICArtifact(
        arithmetic,
        joint_model,
        {
            "capability_id": "CIC-007-MULTIDOMAIN",
            "selected_config": asdict(selected_config),
            "domains": ["jcommonsenseqa", "jnli"],
            "selection_scope": "per-domain official-train inner splits only",
            "frozen_cic_006_reference": {
                "correct": CIC006_VALIDATION_CORRECT,
                "total": CIC006_VALIDATION_ROWS,
            },
        },
    )
    return MultiDomainTrainingResult(
        artifact=artifact,
        math_correct=math_correct,
        math_total=math_total,
        math_work=math_work,
        math_mechanisms=len(arithmetic.mechanisms),
        math_epochs=math_epochs,
        math_validation=math_validation,
        math_expansions=expansions,
        commonsense_train_rows=len(commonsense_train),
        commonsense_test_rows=len(commonsense_test),
        jnli_train_rows=len(jnli_train),
        jnli_test_rows=len(jnli_test),
        joint_train_rows=len(joint_train),
        commonsense_correct=commonsense_correct,
        commonsense_work=commonsense_work,
        jnli_correct=jnli_correct,
        jnli_work=jnli_work,
        commonsense_majority_correct=_majority_correct(commonsense_test),
        jnli_majority_correct=_majority_correct(jnli_test),
        cic_006_commonsense_correct=CIC006_VALIDATION_CORRECT,
        choice_nonzero_weights=len(joint_model.weights),
        selected_config_name=selected_config.name,
        selected_config=asdict(selected_config),
        candidate_configs={
            config.name: asdict(config) for config in MULTIDOMAIN_CONFIGS
        },
        inner_validation=inner_validation,
    )
