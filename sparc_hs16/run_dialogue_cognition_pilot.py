from __future__ import annotations

import json
import time
from pathlib import Path

from sparc_hs16.conversation import ConsistentConversationEngine
from sparc_hs16.dialogue_cognition import ConversationalCognitiveEngine


def run_dialogue(engine, title, turns):
    transcript = []
    latencies = []
    for user in turns:
        started = time.perf_counter()
        reply = engine.respond(user)
        latencies.append((time.perf_counter() - started) * 1000)
        transcript.append({
            "user": user,
            "assistant": reply.text,
            "act": reply.act,
            "confidence": reply.confidence,
        })
    return {"title": title, "turns": transcript}, latencies


def contains(reply, *terms):
    return any(term in reply for term in terms)


def main():
    scenarios = [
        (
            "emotion_and_followup",
            [
                "今日は仕事でかなり疲れたよ。",
                "上司に帰る直前で急な仕事を頼まれてさ。",
                "断ったら機嫌が悪くなりそうで、結局引き受けた。",
                "こういうとき、どうすればいいと思う？",
            ],
        ),
        (
            "memory_and_correction",
            [
                "私の名前は郁斗です。",
                "私はひたちなか市に住んでいます。",
                "私は鶏白湯ラーメンが好きです。",
                "私の目標は軽量な知能モデルを完成させることです。",
                "名前を覚えてる？",
                "どこに住んでるか覚えてる？",
                "好きなものを覚えてる？",
                "目標を覚えてる？",
                "彼女と長野へ行く予定なんだ。",
                "彼女じゃなくて妹だよ。",
                "さっきの旅行の話に戻ろう。",
            ],
        ),
        (
            "topic_switch_and_return",
            [
                "最近ランニングを再開したんだ。",
                "10キロ走ると後半に脚が重くなる。",
                "そういえばAIモデルの研究も進めてる。",
                "メモリ効率がなかなか難しい。",
                "さっきのランニングの話に戻ろう。",
                "あれについてどう思う？",
            ],
        ),
        (
            "ambiguity_and_unknown",
            [
                "それをどうすればいい？",
                "私の誕生日を覚えてる？",
                "今日はうまくいって嬉しい。",
                "でも少し不安でもある。",
            ],
        ),
    ]

    transcripts = []
    latencies = []
    engine = ConversationalCognitiveEngine()
    session_profile_persistence = True
    for index, (title, turns) in enumerate(scenarios):
        if index:
            remembered_name = engine.state.facts.get("名前")
            engine.start_new_session()
            session_profile_persistence &= engine.state.facts.get("名前") == remembered_name
            session_profile_persistence &= engine.state.current_topic is None
        transcript, rows = run_dialogue(engine, title, turns)
        transcripts.append(transcript)
        latencies.extend(rows)

    all_replies = [turn["assistant"] for scenario in transcripts for turn in scenario["turns"]]
    checks = {
        "empathy_on_fatigue": contains(transcripts[0]["turns"][0]["assistant"], "疲れる", "つら"),
        "followup_question_on_emotion": transcripts[0]["turns"][0]["assistant"].endswith("？"),
        "advice_uses_topic": "上司" in transcripts[0]["turns"][3]["assistant"] or "仕事" in transcripts[0]["turns"][3]["assistant"],
        "name_recall": "郁斗" in transcripts[1]["turns"][4]["assistant"],
        "location_recall": "ひたちなか市" in transcripts[1]["turns"][5]["assistant"],
        "preference_recall": "鶏白湯ラーメン" in transcripts[1]["turns"][6]["assistant"],
        "goal_recall": "軽量な知能モデル" in transcripts[1]["turns"][7]["assistant"],
        "correction_acknowledged": "妹" in transcripts[1]["turns"][9]["assistant"] and "彼女" in transcripts[1]["turns"][9]["assistant"],
        "topic_resume": "旅行" in transcripts[1]["turns"][10]["assistant"] or "妹" in transcripts[1]["turns"][10]["assistant"],
        "running_topic_resume": "ランニング" in transcripts[2]["turns"][4]["assistant"],
        "ambiguous_reference_clarified": contains(transcripts[3]["turns"][0]["assistant"], "特定", "一言"),
        "unknown_fact_abstained": contains(transcripts[3]["turns"][1]["assistant"], "まだ", "聞いていない"),
        "positive_affect_response": contains(transcripts[3]["turns"][2]["assistant"], "よかった", "嬉", "うまく"),
        "negative_affect_after_positive": contains(transcripts[3]["turns"][3]["assistant"], "不安"),
        "response_diversity": len(set(all_replies)) / len(all_replies) >= 0.85,
        "session_profile_persistence": session_profile_persistence,
    }

    legacy = ConsistentConversationEngine()
    legacy_handled = 0
    legacy_total = 0
    for _title, turns in scenarios:
        for utterance in turns:
            legacy_total += 1
            legacy_handled += int(legacy.respond(utterance) is not None)

    sorted_latencies = sorted(latencies)
    p95 = sorted_latencies[max(0, int(len(sorted_latencies) * 0.95) - 1)]
    report = {
        "experiment": "SPARC-HS20 discourse-aware natural dialogue prototype",
        "scenario_count": len(scenarios),
        "turn_count": len(all_replies),
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "automatic_score": sum(checks.values()) / len(checks),
        "p95_latency_ms": p95,
        "state_bytes": engine.serialized_bytes(),
        "session_profile_persistence": session_profile_persistence,
        "legacy_engine_handled_turns": legacy_handled,
        "legacy_engine_total_turns": legacy_total,
        "legacy_engine_coverage": legacy_handled / legacy_total,
        "transcripts": transcripts,
        "architecture": {
            "bounded_discourse_graph": True,
            "dialogue_act_policy": True,
            "affect_tracking": True,
            "correction_semantics": True,
            "topic_stack": True,
            "anaphora_resolution": True,
            "long_term_profile_separate_from_working_context": True,
            "transformer_used": False,
            "backpropagation_used": False,
        },
        "human_transcript_review_required": True,
        "claim_boundary": {
            "open_domain_natural_conversation_proven": False,
            "highschool_level_communication_proven": False,
            "general_intelligence_discovered": False,
        },
    }
    Path("dialogue_transcript.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    markdown = ["# SPARC-HS20 実対話記録", ""]
    for scenario in transcripts:
        markdown.extend([f"## {scenario['title']}", ""])
        for turn in scenario["turns"]:
            markdown.extend([
                f"**User:** {turn['user']}",
                "",
                f"**HS20:** {turn['assistant']}",
                "",
            ])
    Path("dialogue_transcript.md").write_text("\n".join(markdown), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
