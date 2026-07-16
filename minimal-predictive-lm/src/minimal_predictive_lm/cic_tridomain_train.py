from __future__ import annotations

import gc
import hashlib
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

from .cic_artifact import CICArtifact, artifact_accuracy
from .cic_choice_data import ChoiceExample, load_choice_dataset, stable_choice_split
from .cic_choice_model import (
    QuantizedChoiceMechanism,
    choice_accuracy,
    train_choice_mechanism,
)
from .cic_jsts_data import JSTSRecord, load_jsts_dataset, stable_jsts_split
from .cic_mixed_artifact import MixedCICArtifact
from .cic_training import (
    choose_epochs,
    compile_candidates,
    load_mawps,
    stable_outer_split,
    train_raw_model,
)

CIC007_COMMONSENSE_CORRECT = 343
CIC007_COMMONSENSE_TOTAL = 1119
CIC007_JNLI_CORRECT = 1736
CIC007_JNLI_TOTAL = 2434


@dataclass(frozen=True)
class TriDomainConfig:
    name: str
    top_weights: int
    dimensions: int = 131072
    hash_replicas: int = 2
    epochs: int = 3
    aggressiveness: float = 0.20
    quantization_limit: int = 63
    relation_scope: str = "adaptive"

    @property
    def training_key(self) -> tuple[int, int, int, float, str]:
        return (
            self.dimensions,
            self.hash_replicas,
            self.epochs,
            self.aggressiveness,
            self.relation_scope,
        )


TRIDOMAIN_CONFIGS = (
    TriDomainConfig("cic_008_adaptive_16k", 16384),
    TriDomainConfig("cic_008_adaptive_20k", 20480),
    TriDomainConfig("cic_008_adaptive_24k", 24576),
    TriDomainConfig("cic_008_adaptive_256k_24k", 24576, dimensions=262144),
)


@dataclass
class TriDomainTrainingResult:
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
    jsts_train_rows: int
    jsts_test_rows: int
    joint_train_rows: int
    commonsense_correct: int
    commonsense_work: float
    jnli_correct: int
    jnli_work: float
    jsts_metrics: dict[str, float]
    jsts_baseline_metrics: dict[str, float]
    commonsense_majority_correct: int
    jnli_majority_correct: int
    choice_nonzero_weights: int
    selected_config_name: str
    selected_config: dict[str, object]
    candidate_configs: dict[str, dict[str, object]]
    inner_validation: dict[str, dict[str, float]]


def _stable_sample_choices(
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


def _stable_sample_jsts(
    rows: Sequence[JSTSRecord],
    limit: int,
    namespace: str,
) -> list[JSTSRecord]:
    if len(rows) <= limit:
        return list(rows)
    return sorted(
        rows,
        key=lambda row: hashlib.sha256(
            (namespace + row.choice.raw_question).encode("utf-8")
        ).digest(),
    )[:limit]


def _balanced_interleave_three(
    commonsense: Sequence[ChoiceExample],
    jnli: Sequence[ChoiceExample],
    jsts: Sequence[JSTSRecord],
    *,
    namespace: str,
    max_per_domain: int = 8000,
) -> list[ChoiceExample]:
    count = min(len(commonsense), len(jnli), len(jsts), max_per_domain)
    cs = _stable_sample_choices(commonsense, count, namespace + ":cs:")
    nli = _stable_sample_choices(jnli, count, namespace + ":nli:")
    sts = _stable_sample_jsts(jsts, count, namespace + ":sts:")
    result: list[ChoiceExample] = []
    for index in range(count):
        result.extend((cs[index], nli[index], sts[index].choice))
    return result


def _majority_correct(rows: Sequence[ChoiceExample]) -> int:
    if not rows:
        return 0
    majority = Counter(row.answer_index for row in rows).most_common(1)[0][0]
    return sum(row.answer_index == majority for row in rows)


def _pearson(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 2 or np.std(left) == 0.0 or np.std(right) == 0.0:
        return 0.0
    return float(np.corrcoef(left, right)[0, 1])


def jsts_metrics(
    model: QuantizedChoiceMechanism,
    rows: Sequence[JSTSRecord],
) -> dict[str, float]:
    targets: list[float] = []
    predictions: list[float] = []
    exact_bins = 0
    for row in rows:
        index, _checked = model.predict(row.choice.stem, row.choice.options)
        prediction = float(row.choice.options[index])
        predictions.append(prediction)
        targets.append(row.target)
        exact_bins += int(index == row.choice.answer_index)
    target_array = np.asarray(targets, dtype=np.float64)
    prediction_array = np.asarray(predictions, dtype=np.float64)
    return {
        "mae": float(np.mean(np.abs(target_array - prediction_array))) if len(rows) else 0.0,
        "rmse": float(np.sqrt(np.mean((target_array - prediction_array) ** 2))) if len(rows) else 0.0,
        "pearson": _pearson(target_array, prediction_array),
        "halfstep_accuracy": exact_bins / len(rows) if rows else 0.0,
    }


def jsts_mean_baseline(
    train_rows: Sequence[JSTSRecord],
    test_rows: Sequence[JSTSRecord],
) -> dict[str, float]:
    mean = float(np.mean([row.target for row in train_rows])) if train_rows else 0.0
    targets = np.asarray([row.target for row in test_rows], dtype=np.float64)
    predictions = np.full(len(test_rows), mean, dtype=np.float64)
    return {
        "mean_prediction": mean,
        "mae": float(np.mean(np.abs(targets - predictions))) if len(test_rows) else 0.0,
        "rmse": float(np.sqrt(np.mean((targets - predictions) ** 2))) if len(test_rows) else 0.0,
        "pearson": 0.0,
    }


def _fit_quantized(
    rows: Sequence[ChoiceExample],
    config: TriDomainConfig,
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


def _select_config(
    commonsense_train: Sequence[ChoiceExample],
    jnli_train: Sequence[ChoiceExample],
    jsts_train: Sequence[JSTSRecord],
) -> tuple[TriDomainConfig, dict[str, dict[str, float]]]:
    cs_inner_train, cs_inner_valid = stable_choice_split(
        commonsense_train,
        test_threshold=1500,
        namespace="tridomain-cs-inner:",
    )
    nli_inner_train, nli_inner_valid = stable_choice_split(
        jnli_train,
        test_threshold=1500,
        namespace="tridomain-nli-inner:",
    )
    sts_inner_train, sts_inner_valid = stable_jsts_split(
        jsts_train,
        test_threshold=1500,
        namespace="tridomain-sts-inner:",
    )
    joint_inner = _balanced_interleave_three(
        cs_inner_train,
        nli_inner_train,
        sts_inner_train,
        namespace="tridomain-inner-balance",
    )
    cs_majority = _majority_correct(cs_inner_valid) / len(cs_inner_valid)
    nli_majority = _majority_correct(nli_inner_valid) / len(nli_inner_valid)
    sts_baseline = jsts_mean_baseline(sts_inner_train, sts_inner_valid)

    grouped: dict[
        tuple[int, int, int, float, str], list[TriDomainConfig]
    ] = defaultdict(list)
    for config in TRIDOMAIN_CONFIGS:
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
            joint_inner,
            epochs=epochs,
            dimensions=dimensions,
            aggressiveness=aggressiveness,
            hash_replicas=hash_replicas,
            relation_scope=relation_scope,
        )
        for config in configs:
            model = QuantizedChoiceMechanism.from_raw(
                raw,
                quantization_limit=config.quantization_limit,
                top_weights=config.top_weights,
            )
            cs_correct, cs_total, _ = choice_accuracy(model, cs_inner_valid)
            nli_correct, nli_total, _ = choice_accuracy(model, nli_inner_valid)
            sts = jsts_metrics(model, sts_inner_valid)
            cs_accuracy = cs_correct / cs_total if cs_total else 0.0
            nli_accuracy = nli_correct / nli_total if nli_total else 0.0
            cs_normalized = (cs_accuracy - cs_majority) / max(1e-9, 1.0 - cs_majority)
            nli_normalized = (nli_accuracy - nli_majority) / max(1e-9, 1.0 - nli_majority)
            sts_mae_gain = (float(sts_baseline["mae"]) - sts["mae"]) / max(1e-9, float(sts_baseline["mae"]))
            sts_score = (max(-1.0, sts["pearson"]) + sts_mae_gain) / 2.0
            metrics[config.name] = {
                "commonsense_accuracy": cs_accuracy,
                "jnli_accuracy": nli_accuracy,
                "jsts_mae": sts["mae"],
                "jsts_pearson": sts["pearson"],
                "jsts_mean_baseline_mae": float(sts_baseline["mae"]),
                "commonsense_normalized_gain": cs_normalized,
                "jnli_normalized_gain": nli_normalized,
                "jsts_normalized_score": sts_score,
                "macro_normalized_score": (cs_normalized + nli_normalized + sts_score) / 3.0,
                "minimum_normalized_score": min(cs_normalized, nli_normalized, sts_score),
            }
        del raw
        gc.collect()

    selected = max(
        TRIDOMAIN_CONFIGS,
        key=lambda config: (
            metrics[config.name]["macro_normalized_score"],
            metrics[config.name]["minimum_normalized_score"],
            -config.top_weights,
            -config.dimensions,
        ),
    )
    return selected, metrics


def train_tridomain(
    mawps_path: str | Path,
    commonsense_train_path: str | Path,
    commonsense_test_path: str | Path,
    jnli_train_path: str | Path,
    jnli_test_path: str | Path,
    jsts_train_path: str | Path,
    jsts_test_path: str | Path,
) -> TriDomainTrainingResult:
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
    jsts_train = load_jsts_dataset(jsts_train_path)
    jsts_test = load_jsts_dataset(jsts_test_path)
    if len(commonsense_test) != CIC007_COMMONSENSE_TOTAL:
        raise ValueError("JCommonsenseQA validation no longer matches CIC-007")
    if len(jnli_test) != CIC007_JNLI_TOTAL:
        raise ValueError("JNLI validation no longer matches CIC-007")

    selected_config, inner_validation = _select_config(
        commonsense_train,
        jnli_train,
        jsts_train,
    )
    joint_train = _balanced_interleave_three(
        commonsense_train,
        jnli_train,
        jsts_train,
        namespace="tridomain-full-balance",
    )
    model = _fit_quantized(joint_train, selected_config)
    commonsense_correct, _cs_total, commonsense_work = choice_accuracy(
        model,
        commonsense_test,
    )
    jnli_correct, _nli_total, jnli_work = choice_accuracy(model, jnli_test)
    sts_metrics = jsts_metrics(model, jsts_test)
    sts_baseline = jsts_mean_baseline(jsts_train, jsts_test)

    artifact = MixedCICArtifact(
        arithmetic,
        model,
        {
            "capability_id": "CIC-008-TRIDOMAIN",
            "selected_config": asdict(selected_config),
            "domains": ["jcommonsenseqa", "jnli", "jsts-halfstep"],
            "selection_scope": "per-domain official-train inner splits only",
            "frozen_cic_007_reference": {
                "jcommonsenseqa": {
                    "correct": CIC007_COMMONSENSE_CORRECT,
                    "total": CIC007_COMMONSENSE_TOTAL,
                },
                "jnli": {
                    "correct": CIC007_JNLI_CORRECT,
                    "total": CIC007_JNLI_TOTAL,
                },
            },
        },
    )
    return TriDomainTrainingResult(
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
        jsts_train_rows=len(jsts_train),
        jsts_test_rows=len(jsts_test),
        joint_train_rows=len(joint_train),
        commonsense_correct=commonsense_correct,
        commonsense_work=commonsense_work,
        jnli_correct=jnli_correct,
        jnli_work=jnli_work,
        jsts_metrics=sts_metrics,
        jsts_baseline_metrics=sts_baseline,
        commonsense_majority_correct=_majority_correct(commonsense_test),
        jnli_majority_correct=_majority_correct(jnli_test),
        choice_nonzero_weights=len(model.weights),
        selected_config_name=selected_config.name,
        selected_config=asdict(selected_config),
        candidate_configs={config.name: asdict(config) for config in TRIDOMAIN_CONFIGS},
        inner_validation=inner_validation,
    )
