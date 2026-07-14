from __future__ import annotations

import json

from .meci_chat import DialogueRecord, MECIChat, encode_dialogue
from .meci_core import OperationalQuotient, huffman_code


def run_experiment() -> dict[str, object]:
    histories = ("empty", "greeting-a", "greeting-b", "math", "identity-a", "identity-b")
    queries = ("next-byte-class", "reply-program", "action")
    answers = {
        ("empty", "next-byte-class"): "user-marker",
        ("empty", "reply-program"): "wait",
        ("empty", "action"): "listen",
        ("greeting-a", "next-byte-class"): "greeting",
        ("greeting-a", "reply-program"): "greet",
        ("greeting-a", "action"): "answer",
        ("greeting-b", "next-byte-class"): "greeting",
        ("greeting-b", "reply-program"): "greet",
        ("greeting-b", "action"): "answer",
        ("math", "next-byte-class"): "digit",
        ("math", "reply-program"): "calculate",
        ("math", "action"): "answer",
        ("identity-a", "next-byte-class"): "identity",
        ("identity-a", "reply-program"): "name",
        ("identity-a", "action"): "answer",
        ("identity-b", "next-byte-class"): "identity",
        ("identity-b", "reply-program"): "name",
        ("identity-b", "action"): "answer",
    }
    quotient = OperationalQuotient.build(histories, queries, answers)
    transition_code = huffman_code({"remain": 0.75, "switch": 0.1875, "reset": 0.0625})

    dialogues = [
        DialogueRecord("こんにちは", "こんにちは。今日はどうしましたか？"),
        DialogueRecord("こんにちは", "こんにちは。今日はどうしましたか？"),
        DialogueRecord("名前は？", "私はMECIです。"),
        DialogueRecord("名前は？", "私はMECIです。"),
        DialogueRecord("2+2は？", "4です。"),
        DialogueRecord("2+2は？", "4です。"),
    ]
    chat = MECIChat(max_order=32).fit(dialogues)
    corpus = encode_dialogue(dialogues)
    reply = chat.reply("こんにちは")
    report = chat.model.report()

    result: dict[str, object] = {
        "capability_id": "MECI-001",
        "model": "Minimal Executable Causal Intelligence",
        "neural_network_used": False,
        "gradient_training_used": False,
        "dense_parameter_matrix_used": False,
        "theory": {
            "declared_query_count": len(queries),
            "history_count": len(histories),
            "operational_state_count": quotient.state_count,
            "memory_lower_bound_bits": quotient.worst_case_memory_lower_bound_bits,
            "canonical_state_bits": quotient.canonical_state_bits,
            "memory_bound_attained": quotient.worst_case_memory_lower_bound_bits == quotient.canonical_state_bits,
            "transition_entropy_lower_bound": transition_code.entropy_lower_bound,
            "transition_expected_decisions": transition_code.expected_decisions,
            "transition_within_one_decision": transition_code.expected_decisions < transition_code.entropy_lower_bound + 1.0,
        },
        "byte_language_model": {
            **report,
            "training_bytes": len(corpus),
            "training_negative_log2_likelihood": chat.model.negative_log2_likelihood(corpus),
            "sample_prompt": "こんにちは",
            "sample_reply": reply,
            "sample_reply_exact": reply == "こんにちは。今日はどうしましたか？",
        },
        "claim_boundary": (
            "MECI-001 is a non-neural executable language-machine prototype with class-relative memory minimality and entropy-near-optimal state updates. It is not globally optimal over all computable environments, not an LLM-level model, and the joint operational-quotient novelty claim remains unverified against the full literature."
        ),
    }
    theory = result["theory"]
    language = result["byte_language_model"]
    assert isinstance(theory, dict)
    assert isinstance(language, dict)
    result["passed"] = bool(
        theory["memory_bound_attained"]
        and theory["transition_within_one_decision"]
        and language["sample_reply_exact"]
        and language["predictive_states_after_quotient"] <= language["contexts_before_quotient"]
    )
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
