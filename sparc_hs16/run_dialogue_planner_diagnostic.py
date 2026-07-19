from __future__ import annotations

import json

from sparc_hs16.dialogue_planner import PlannedConversationalEngine


def snapshot(engine, user):
    reply = engine.respond(user)
    return {
        "user": user,
        "reply": reply.text,
        "act": reply.act,
        "evidence": list(reply.evidence),
        "topic": engine.state.current_topic,
        "candidates": [
            {
                "text": candidate.text,
                "strategy": candidate.strategy,
                "score": candidate.score,
                "reasons": list(candidate.reasons),
            }
            for candidate in engine.last_candidates
        ],
    }


def main():
    report = {}

    engine = PlannedConversationalEngine()
    report["multiple"] = snapshot(engine, "今日は仕事でかなり疲れたよ。")

    engine = PlannedConversationalEngine()
    report["advice"] = [
        snapshot(engine, "上司に帰る直前で急な仕事を頼まれた。"),
        snapshot(engine, "断ったら機嫌が悪くなりそうで、結局引き受けた。"),
        snapshot(engine, "こういうとき、どうすればいいと思う？"),
    ]

    engine = PlannedConversationalEngine()
    report["running"] = [
        snapshot(engine, "最近ランニングを再開したんだ。"),
        snapshot(engine, "10キロ走ると後半に脚が重くなる。"),
        snapshot(engine, "原因は何だと思う？"),
    ]

    engine = PlannedConversationalEngine()
    report["repeat"] = [
        snapshot(engine, "ゲームの操作が分かりづらいと言われた。"),
        snapshot(engine, "ゲームの操作が分かりづらいと言われた。"),
    ]

    engine = PlannedConversationalEngine()
    profile = [
        snapshot(engine, "私の名前は郁斗です。"),
        snapshot(engine, "最近ランニングを再開したんだ。"),
    ]
    engine.start_new_session()
    profile.append({"after_reset": {"facts": dict(engine.state.facts), "topic": engine.state.current_topic}})
    profile.append(snapshot(engine, "名前を覚えてる？"))
    report["profile"] = profile

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
