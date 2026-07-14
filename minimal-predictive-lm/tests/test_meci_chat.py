from __future__ import annotations

from minimal_predictive_lm.meci_chat import DialogueRecord, MECIChat
from minimal_predictive_lm.meci_experiment import run_experiment


def test_chat_surface_generates_trained_reply() -> None:
    chat = MECIChat(max_order=32).fit([
        DialogueRecord("こんにちは", "こんにちは。今日はどうしましたか？"),
        DialogueRecord("こんにちは", "こんにちは。今日はどうしましたか？"),
    ])
    assert chat.reply("こんにちは") == "こんにちは。今日はどうしましたか？"


def test_experiment_is_non_neural_and_passes() -> None:
    result = run_experiment()
    assert result["passed"] is True
    assert result["neural_network_used"] is False
    assert result["gradient_training_used"] is False
    assert result["dense_parameter_matrix_used"] is False
    assert result["theory"]["memory_bound_attained"] is True
    assert result["theory"]["transition_within_one_decision"] is True
