from __future__ import annotations

import json
import resource
import time
from pathlib import Path

from .meci_agent import MECICognitiveAgent
from .meci_chat import DialogueRecord


def run_experiment(output: str | Path | None = None) -> dict[str, object]:
    start = time.perf_counter()
    agent = MECICognitiveAgent(dimensions=16384).fit(
        [
            DialogueRecord("調子はどう？", "順調です。今日は何を一緒に考えますか？"),
            DialogueRecord("何が得意？", "教わった事実の記憶、簡単な推論、計算を少ない資源で実行できます。"),
            DialogueRecord("困っている", "何に困っているか、もう少し具体的に教えてください。"),
        ]
    )

    transcript: list[dict[str, object]] = []

    def turn(user: str) -> str:
        reply = agent.reply(user)
        transcript.append(
            {
                "user": user,
                "assistant": reply.text,
                "mechanism": reply.mechanism,
                "confidence": reply.confidence,
            }
        )
        return reply.text

    learned_name = turn("私の名前は郁斗です。")
    turn("こんにちは")
    recalled_name = turn("私の名前は何？")

    turn("アキラは高校生です。")
    turn("高校生は学生です。")
    turn("学生は人です。")
    turn("人は生物です。")
    transitive = turn("アキラは生物？")

    turn("富士山の高さは3776メートルです。")
    property_recall = turn("富士山の高さは何？")
    follow_up = turn("それは何？")

    turn("道路が濡れているのは雨が降ったからです。")
    cause = turn("道路が濡れているのはなぜ？")

    arithmetic = turn("18*7-9は？")
    paraphrase = turn("調子どう？")
    unknown = turn("量子重力の完全な理論を説明して")

    artifact = agent.to_bytes()
    restored = MECICognitiveAgent.from_bytes(artifact)
    persisted = restored.reply("私の名前は何？").text

    checks = {
        "online_name_learning": learned_name == "分かりました。覚えておきます。",
        "working_memory_survives_distractor": recalled_name == "ユーザーの名前は郁斗です。",
        "four_hop_transitive_reasoning": (
            transitive.startswith("はい。")
            and "アキラは高校生" in transitive
            and "人は生物" in transitive
        ),
        "novel_property_recall": property_recall == "富士山の高さは3776メートルです。",
        "follow_up_subject_resolution": "富士山" in follow_up,
        "causal_recall": cause == "雨が降ったからです。",
        "symbolic_arithmetic": arithmetic == "117です。",
        "paraphrase_episode_retrieval": paraphrase == "順調です。今日は何を一緒に考えますか？",
        "calibrated_unknown": "まだ" in unknown and "教えて" in unknown,
        "artifact_persistence": persisted == "ユーザーの名前は郁斗です。",
    }
    passed_count = sum(checks.values())
    report = agent.report()
    result: dict[str, object] = {
        "capability_id": "MECI-002-CONVERSATION",
        "target": "minimum-resource Japanese conversational intelligence",
        "neural_network_used": False,
        "transformer_used": False,
        "gradient_training_used": False,
        "free_form_text_input": True,
        "multi_turn_state": True,
        "online_learning": True,
        "transcript": transcript,
        "checks": checks,
        "passed_checks": passed_count,
        "total_checks": len(checks),
        "model": report,
        "artifact_bytes": len(artifact),
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "MECI-002 is a stateful non-neural conversation scaffold. It demonstrates online fact learning, bounded "
            "working memory, sparse episode retrieval, symbolic arithmetic and explicit multi-hop reasoning. It is not "
            "a learned Japanese language intelligence and not yet high-school-level general intelligence. The learned "
            "SACS recurrent core must replace hand-written semantic parsing before this line can satisfy the target."
        ),
    }
    result["passed"] = bool(
        passed_count == len(checks)
        and len(artifact) <= 100_000
        and report["semantic_facts"] >= 7
        and result["peak_process_kib"] <= 200_000
    )
    if output is not None:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        path.with_suffix(".cog").write_bytes(artifact)
    return result


def main() -> None:
    print(json.dumps(run_experiment("results/meci_002_conversation.json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
