from __future__ import annotations

from minimal_predictive_lm.curriculum_memory_gate import (
    GateObservation,
    QuantizedCurriculumGate,
    cross_validate_gate,
    train_gate,
)


def _row(index: int, memory_should_win: bool) -> GateObservation:
    answer = 1 if memory_should_win else 0
    # Memory confidence is intentionally the transferable signal; no prompt or
    # subject text is available to the gate.
    memory_scores = (-2.0, 2.0) if memory_should_win else (-0.1, 0.1)
    return GateObservation(
        example_id=f"example-{index}",
        base_scores=(1.0, 0.0),
        memory_scores=memory_scores,
        active_postings=100 + index % 7,
        stem_length=40 + index % 5,
        option_lengths=(4, 4),
        answer_index=answer,
    )


def test_gate_learns_when_memory_confidence_is_reliable() -> None:
    rows = [_row(index, index % 3 == 0) for index in range(150)]
    report = cross_validate_gate(rows, folds=5)
    assert report["gated_gain_over_base"] > 0
    assert sum(fold["gated_gain_over_base"] >= 0 for fold in report["fold_reports"]) >= 3
    assert report["subject_name_feature_used"] is False
    assert report["prompt_text_feature_used"] is False


def test_quantized_gate_round_trip_preserves_decisions() -> None:
    rows = [_row(index, index % 4 == 0) for index in range(120)]
    model = train_gate(rows, metadata={"official_exam_targets_used": 0})
    restored = QuantizedCurriculumGate.from_bytes(model.to_bytes())
    assert len(model.to_bytes()) < 16 * 1024
    assert restored.metadata["official_exam_targets_used"] == 0
    assert [restored.choose_index(row) for row in rows] == [
        model.choose_index(row) for row in rows
    ]
