from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

from .cic_choice_data import ChoiceExample
from .generic_causal_judgement_v3 import GenericCausalJudgementV3
from . import semantic_causal_ranker as base
from .sparc_hs18_learned_gate_v2 import normalized_causal_choice_rows
from .synthetic_causal_curriculum import build_synthetic_causal_curriculum


@dataclass(frozen=True)
class CurriculumSemanticTrainingReport:
    development_train_rows: int
    development_validation_rows: int
    synthetic_train_rows: int
    synthetic_holdout_rows: int
    selected_dimensions: int
    selected_epochs: int
    selected_policy: str
    selected_threshold: float
    development_validation_accuracy: float
    synthetic_holdout_accuracy: float
    macro_validation_accuracy: float
    candidate_metrics: dict[str, dict[str, float]]
    final_training_rows: int
    nonzero_weights: int
    serialized_bytes: int


def _evaluate(
    model: base.QuantizedSemanticCausalRanker,
    rows: Sequence[ChoiceExample],
    policy: str,
    threshold: float,
    symbolic: GenericCausalJudgementV3,
) -> tuple[int, float]:
    correct = 0
    for row in rows:
        learned = model.predict(row.raw_question)
        symbolic_output = symbolic.answer(row.raw_question).output
        output = base._combine(policy, threshold, learned, symbolic_output)
        correct += int((output == "Yes") == (row.answer_index == 0))
    return correct, correct / len(rows) if rows else 0.0


def _fit(
    rows: Sequence[ChoiceExample], dimensions: int, epochs: int
) -> base.QuantizedSemanticCausalRanker:
    weights = base._train_float(
        [row.raw_question for row in rows],
        [row.answer_index for row in rows],
        dimensions,
        epochs,
    )
    scale, quantized = base._quantize(weights)
    return base.QuantizedSemanticCausalRanker(
        dimensions, scale, quantized, "learned_always", 0.0, {}
    )


def train_curriculum_semantic_ranker(
    document: dict[str, object],
    *,
    development_train_stop: int = 120,
    development_stop: int = 142,
) -> tuple[base.QuantizedSemanticCausalRanker, CurriculumSemanticTrainingReport]:
    development = normalized_causal_choice_rows(document, development_stop)
    curriculum = build_synthetic_causal_curriculum()
    development_train = development[:development_train_stop]
    development_validation = development[development_train_stop:development_stop]
    selection_train = list(development_train) + list(curriculum.train)
    symbolic = GenericCausalJudgementV3()
    configs = ((4096, 4), (8192, 6), (16384, 8))
    policies = (
        ("learned_always", 0.0),
        ("learned_margin", 0.15),
        ("learned_margin", 0.40),
        ("learned_margin", 0.80),
        ("learned_margin", 1.50),
        ("symbolic_first", 0.0),
    )
    metrics: dict[str, dict[str, float]] = {}
    selected_key: tuple[float, float, float, int, int, str, float] | None = None
    selected_spec: tuple[int, int, str, float] | None = None

    for dimensions, epochs in configs:
        candidate = _fit(selection_train, dimensions, epochs)
        for policy, threshold in policies:
            dev_correct, dev_accuracy = _evaluate(
                candidate, development_validation, policy, threshold, symbolic
            )
            synth_correct, synth_accuracy = _evaluate(
                candidate, curriculum.holdout, policy, threshold, symbolic
            )
            macro = (dev_accuracy + synth_accuracy) / 2.0
            name = f"d{dimensions}-e{epochs}:{policy}:{threshold:.2f}"
            metrics[name] = {
                "development_accuracy": dev_accuracy,
                "development_correct": float(dev_correct),
                "synthetic_holdout_accuracy": synth_accuracy,
                "synthetic_holdout_correct": float(synth_correct),
                "macro_accuracy": macro,
                "weights": float(len(candidate.weights)),
            }
            key = (
                macro,
                min(dev_accuracy, synth_accuracy),
                dev_accuracy,
                -len(candidate.weights),
                -dimensions,
                policy,
                -threshold,
            )
            if selected_key is None or key > selected_key:
                selected_key = key
                selected_spec = (dimensions, epochs, policy, threshold)

    if selected_key is None or selected_spec is None:
        raise RuntimeError("no curriculum semantic causal candidate")
    dimensions, epochs, policy, threshold = selected_spec
    final_rows = list(development) + list(curriculum.train) + list(curriculum.holdout)
    model = _fit(final_rows, dimensions, epochs)
    model = base.QuantizedSemanticCausalRanker(
        model.dimensions,
        model.scale,
        model.weights,
        policy,
        threshold,
        {
            "development_train_rows": development_train_stop,
            "development_validation_rows": development_stop - development_train_stop,
            "synthetic_train_rows": len(curriculum.train),
            "synthetic_holdout_rows": len(curriculum.holdout),
            "final_training_rows": len(final_rows),
            "tail_targets_used": 0,
            "semantic_encoder": "event-norm-intent-counterfactual-v1",
            "synthetic_generator": "procedural-causal-worlds-v1",
        },
    )
    selected_metric = metrics[
        f"d{dimensions}-e{epochs}:{policy}:{threshold:.2f}"
    ]
    report = CurriculumSemanticTrainingReport(
        development_train_stop,
        development_stop - development_train_stop,
        len(curriculum.train),
        len(curriculum.holdout),
        dimensions,
        epochs,
        policy,
        threshold,
        selected_metric["development_accuracy"],
        selected_metric["synthetic_holdout_accuracy"],
        selected_metric["macro_accuracy"],
        metrics,
        len(final_rows),
        len(model.weights),
        len(model.to_bytes()),
    )
    return model, report
