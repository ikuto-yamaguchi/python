from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .cic_artifact import CICArtifact, artifact_accuracy
from .cic_choice_data import load_choice_dataset, stable_choice_split
from .cic_choice_model import (
    QuantizedChoiceMechanism,
    choice_accuracy,
    choose_choice_epochs,
    choose_legacy_choice_epochs,
    train_choice_mechanism,
    train_legacy_choice_mechanism,
)
from .cic_mixed_artifact import MixedCICArtifact
from .cic_training import (
    choose_epochs,
    compile_candidates,
    load_mawps,
    stable_outer_split,
    train_raw_model,
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
    choice_rows: int
    choice_train_rows: int
    choice_test_rows: int
    choice_correct: int
    choice_work: float
    choice_epochs: int
    choice_validation: dict[int, float]
    majority_correct: int
    choice_nonzero_weights: int
    legacy_correct: int
    legacy_epochs: int
    legacy_validation: dict[int, float]


def train_mixed(
    mawps_path: str | Path,
    commonsense_path: str | Path,
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

    choice_rows = load_choice_dataset(commonsense_path)
    choice_train, choice_test = stable_choice_split(choice_rows)

    legacy_epochs, legacy_validation = choose_legacy_choice_epochs(choice_train)
    legacy_raw = train_legacy_choice_mechanism(choice_train, epochs=legacy_epochs)
    legacy_correct, _legacy_total, _legacy_work = choice_accuracy(
        legacy_raw, choice_test
    )

    choice_epochs, choice_validation = choose_choice_epochs(choice_train)
    choice_raw = train_choice_mechanism(choice_train, epochs=choice_epochs)
    choice = QuantizedChoiceMechanism.from_raw(choice_raw)
    choice_correct, _choice_total, choice_work = choice_accuracy(choice, choice_test)
    majority_index = Counter(row.answer_index for row in choice_train).most_common(1)[0][0]
    majority_correct = sum(row.answer_index == majority_index for row in choice_test)

    artifact = MixedCICArtifact(
        arithmetic,
        choice,
        {"capability_id": "CIC-004-MARGIN"},
    )
    return MixedTrainingResult(
        artifact,
        math_correct,
        math_total,
        math_work,
        len(arithmetic.mechanisms),
        math_epochs,
        math_validation,
        expansions,
        len(choice_rows),
        len(choice_train),
        len(choice_test),
        choice_correct,
        choice_work,
        choice_epochs,
        choice_validation,
        majority_correct,
        len(choice.weights),
        legacy_correct,
        legacy_epochs,
        legacy_validation,
    )
