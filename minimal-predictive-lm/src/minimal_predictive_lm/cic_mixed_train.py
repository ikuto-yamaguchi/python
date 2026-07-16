from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .cic_artifact import CICArtifact, artifact_accuracy
from .cic_choice_data import load_choice_dataset, stable_choice_split
from .cic_choice_model import (
    QuantizedChoiceMechanism,
    choice_accuracy,
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
    choice_validation: dict[str, float]
    majority_correct: int
    choice_nonzero_weights: int
    legacy_correct: int
    margin_correct: int
    legacy_epochs: int
    selected_learner: str


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

    choice_rows = load_choice_dataset(commonsense_train_path)
    if commonsense_test_path is None:
        choice_train, choice_test = stable_choice_split(choice_rows)
    else:
        choice_train = choice_rows
        choice_test = load_choice_dataset(commonsense_test_path)

    # The two learners use the same compact executable feature map. Only the
    # update rule differs. Learner selection happens on an inner split of the
    # official training data; the official validation set remains untouched.
    inner_train, inner_validation = stable_choice_split(
        choice_train, test_threshold=1500, namespace="learner-selection:"
    )
    legacy_epochs = 4
    margin_epochs = 3
    legacy_probe = train_legacy_choice_mechanism(
        inner_train, epochs=legacy_epochs
    )
    margin_probe = train_choice_mechanism(
        inner_train, epochs=margin_epochs
    )
    legacy_inner_correct, inner_total, _ = choice_accuracy(
        legacy_probe, inner_validation
    )
    margin_inner_correct, _inner_total, _ = choice_accuracy(
        margin_probe, inner_validation
    )
    validation_scores = {
        "cic_003_mistake_perceptron": (
            legacy_inner_correct / inner_total if inner_total else 0.0
        ),
        "cic_004_averaged_margin": (
            margin_inner_correct / inner_total if inner_total else 0.0
        ),
    }
    selected_learner = max(validation_scores, key=validation_scores.get)

    legacy_raw = train_legacy_choice_mechanism(
        choice_train, epochs=legacy_epochs
    )
    legacy = QuantizedChoiceMechanism.from_raw(
        legacy_raw, quantization_limit=31, top_weights=4096
    )
    legacy_correct, _legacy_total, _legacy_work = choice_accuracy(
        legacy, choice_test
    )

    margin_raw = train_choice_mechanism(
        choice_train, epochs=margin_epochs
    )
    margin = QuantizedChoiceMechanism.from_raw(
        margin_raw, quantization_limit=63, top_weights=8192
    )
    margin_correct, _margin_total, _margin_work = choice_accuracy(
        margin, choice_test
    )

    choice = margin if selected_learner == "cic_004_averaged_margin" else legacy
    choice_correct, _choice_total, choice_work = choice_accuracy(choice, choice_test)
    majority_index = Counter(row.answer_index for row in choice_train).most_common(1)[0][0]
    majority_correct = sum(row.answer_index == majority_index for row in choice_test)

    artifact = MixedCICArtifact(
        arithmetic,
        choice,
        {
            "capability_id": "CIC-004-JGLUE",
            "selected_learner": selected_learner,
        },
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
        margin_epochs if selected_learner == "cic_004_averaged_margin" else legacy_epochs,
        validation_scores,
        majority_correct,
        len(choice.weights),
        legacy_correct,
        margin_correct,
        legacy_epochs,
        selected_learner,
    )
