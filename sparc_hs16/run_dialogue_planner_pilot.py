from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from sparc_hs16.dialogue_cognition import ConversationalCognitiveEngine
from sparc_hs16.dialogue_planner import PlannedConversationalEngine


SCENARIOS = (
    (
        "workplace_conflict",
        (
            "今日は仕事でかなり疲れたよ。",
            "上司に帰る直前で急な仕事を頼まれてさ。",
            "断ったら機嫌が悪くなりそうで、結局引き受けた。",
            "こういうとき、どうすればいいと思う？",
            "それなら角が立ちにくそう。次に頼まれたら試してみる。",
        ),
    ),
    (
        "running_causal_reasoning",
        (
            "最近ランニングを再開したんだ。",
            "10キロ走ると後半に脚が重くなる。",
            "息は平気だけど、脚だけ動かなくなる感じ。",
            "原因は何だと思う？",
            "前半を少し落として試してみようかな。",
        ),
    ),
    (
        "research_tradeoff",
        (
            "軽量な知能モデルの研究を続けている。",
            "64MBで合成問題は解けたけど、自然会話はまだ弱い。",
            "容量を増やすだけでは会話能力は伸びない気がする。",
            "表現学習と会話プランニングのどちらを先に改善すべきだと思う？",
            "理由も含めて順番を決めたい。",
        ),
    ),
    (
        "mixed_game_feedback",
        (
            "昨日、友達に作ったゲームを遊んでもらった。",
            "面白いとは言ってくれたけど、操作が分かりづらいとも言われた。",
            "面白さを伸ばすか、操作を直すかで迷っている。",
            "君ならどっちを優先する？",
        ),
    ),
    (
        "profile_session_and_ambiguity",
        (
            "私の名前は郁斗です。",
            "私はひたちなか市に住んでいます。",
            "私は鶏白湯ラーメンが好きです。",
            "彼女と長野へ行く予定なんだ。",
            "彼女じゃなくて妹だよ。",
            "名前を覚えてる？",
            "さっきの旅行の話に戻ろう。",
        ),
    ),
)


def run(engine, include_candidates: bool) -> tuple[list[dict], list[float]]:
    transcripts: list[dict] = []
    latencies: list[float] = []
    for scenario_index, (title, turns) in enumerate(SCENARIOS):
        if scenario_index:
            engine.start_new_session()
        rows = []
        for user in turns:
            started = time.perf_counter()
            reply = engine.respond(user)
            latencies.append((time.perf_counter() - started) * 1_000)
            row = {
                "user": user,
                "assistant": reply.text,
                "act": reply.act,
                "evidence": list(reply.evidence),
            }
            if include_candidates:
                row["candidates"] = [
                    {
                        "text": candidate.text,
                        "strategy": candidate.strategy,
                        "score": candidate.score,
                        "reasons": list(candidate.reasons),
                    }
                    for candidate in engine.last_candidates
                ]
            rows.append(row)
        transcripts.append({"title": title, "turns": rows})
    return transcripts, latencies


def all_replies(transcripts: list[dict]) -> list[str]:
    return [turn["assistant"] for scenario in transcripts for turn in scenario["turns"]]


def generic_rate(replies: list[str]) -> float:
    generic = ("なるほど", "もう少し詳しく", "その後はどうなった", "簡単に割り切れない")
    return sum(any(fragment in reply for fragment in generic) for reply in replies) / len(replies)


def average_length(replies: list[str]) -> float:
    return statistics.mean(len(reply) for reply in replies)


def main() -> None:
    hs20 = ConversationalCognitiveEngine()
    hs21 = PlannedConversationalEngine()
    hs20_transcripts, hs20_latencies = run(hs20, False)
    hs21_transcripts, hs21_latencies = run(hs21, True)

    hs20_replies = all_replies(hs20_transcripts)
    hs21_replies = all_replies(hs21_transcripts)
    work = hs21_transcripts[0]["turns"]
    running = hs21_transcripts[1]["turns"]
    research = hs21_transcripts[2]["turns"]
    game = hs21_transcripts[3]["turns"]
    profile = hs21_transcripts[4]["turns"]

    selected_are_top_scored = all(
        not turn.get("candidates")
        or turn["assistant"] == max(turn["candidates"], key=lambda row: row["score"])["text"]
        for scenario in hs21_transcripts
        for turn in scenario["turns"]
    )
    candidate_counts = [
        len(turn.get("candidates", []))
        for scenario in hs21_transcripts
        for turn in scenario["turns"]
    ]
    checks = {
        "work_timing_grounded": "帰る直前" in work[1]["assistant"] or "予定" in work[1]["assistant"],
        "work_conflict_understood": any(term in work[2]["assistant"] for term in ("断り", "機嫌", "引き受け")),
        "work_advice_actionable": any(term in work[3]["assistant"] for term in ("優先", "選択肢", "相手に決め", "事実・制約・希望")),
        "running_response_uses_dimensions": any(term in running[3]["assistant"] for term in ("ペース", "呼吸", "脚", "補給")),
        "research_response_uses_tradeoff": any(term in research[3]["assistant"] for term in ("精度", "計算量", "メモリ", "汎化", "失敗したとき")),
        "game_choice_is_direct": any(term in game[3]["assistant"] for term in ("分かりやすさ", "操作", "最初は", "優先")),
        "correction_retained": "妹" in profile[4]["assistant"] and "彼女" in profile[4]["assistant"],
        "name_recalled": "郁斗" in profile[5]["assistant"],
        "topic_resumed": "旅行" in profile[6]["assistant"] or "妹" in profile[6]["assistant"],
        "selected_candidate_is_top_score": selected_are_top_scored,
        "multiple_candidates_generated": statistics.mean(candidate_counts) >= 2.0,
        "no_exact_duplicate_replies": len(set(hs21_replies)) == len(hs21_replies),
        "generic_rate_improved": generic_rate(hs21_replies) < generic_rate(hs20_replies),
        "response_depth_increased": average_length(hs21_replies) > average_length(hs20_replies) + 8.0,
        "bounded_state": hs21.serialized_bytes() < 100_000,
    }

    sorted_latencies = sorted(hs21_latencies)
    p95 = sorted_latencies[max(0, int(len(sorted_latencies) * 0.95) - 1)]
    report = {
        "experiment": "SPARC-HS21 candidate-generating self-critical dialogue planner",
        "scenario_count": len(SCENARIOS),
        "turn_count": len(hs21_replies),
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "automatic_score": sum(checks.values()) / len(checks),
        "hs20_generic_rate": generic_rate(hs20_replies),
        "hs21_generic_rate": generic_rate(hs21_replies),
        "hs20_average_reply_chars": average_length(hs20_replies),
        "hs21_average_reply_chars": average_length(hs21_replies),
        "average_candidate_count": statistics.mean(candidate_counts),
        "p95_latency_ms": p95,
        "state_and_candidates_bytes": hs21.serialized_bytes(),
        "hs20_transcripts": hs20_transcripts,
        "hs21_transcripts": hs21_transcripts,
        "architecture": {
            "discourse_graph": True,
            "utterance_frame_parser": True,
            "counterfactual_conflict_frame": True,
            "multi_candidate_generation": True,
            "relevance_specificity_affect_critic": True,
            "repetition_and_echo_penalty": True,
            "selected_candidate_audit_trail": True,
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
    Path("dialogue_planner_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    markdown = [
        "# SPARC-HS21 実対話・候補採点記録",
        "",
        f"- HS20 generic rate: {report['hs20_generic_rate']:.3f}",
        f"- HS21 generic rate: {report['hs21_generic_rate']:.3f}",
        f"- HS20 average chars: {report['hs20_average_reply_chars']:.2f}",
        f"- HS21 average chars: {report['hs21_average_reply_chars']:.2f}",
        "",
    ]
    for scenario in hs21_transcripts:
        markdown.extend((f"## {scenario['title']}", ""))
        for turn in scenario["turns"]:
            markdown.extend((f"**User:** {turn['user']}", "", f"**HS21:** {turn['assistant']}", ""))
            markdown.append("候補:")
            for candidate in turn["candidates"]:
                marker = "✓" if candidate["text"] == turn["assistant"] else "-"
                markdown.append(
                    f"{marker} `{candidate['score']:.3f}` {candidate['strategy']}: {candidate['text']}"
                )
            markdown.append("")
    Path("dialogue_planner_transcript.md").write_text("\n".join(markdown), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
