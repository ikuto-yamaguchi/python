from __future__ import annotations

import argparse
import json
from pathlib import Path

from .meci_agent import MECICognitiveAgent
from .meci_chat import load_jsonl


def _build_agent(training_jsonl: str | None, artifact: str | None) -> MECICognitiveAgent:
    if artifact and Path(artifact).exists():
        return MECICognitiveAgent.load(artifact)
    agent = MECICognitiveAgent()
    if training_jsonl:
        agent.fit(load_jsonl(training_jsonl))
    return agent


def main() -> None:
    parser = argparse.ArgumentParser(description="MECI cognitive non-neural conversation agent")
    parser.add_argument("--training-jsonl", default=None)
    parser.add_argument("--artifact", default="meci_agent.cog")
    parser.add_argument("--prompt", default=None, help="single-turn mode")
    parser.add_argument("--json", action="store_true", help="print mechanism metadata")
    args = parser.parse_args()

    agent = _build_agent(args.training_jsonl, args.artifact)

    def answer(text: str) -> None:
        reply = agent.reply(text)
        if args.json:
            print(
                json.dumps(
                    {
                        "reply": reply.text,
                        "mechanism": reply.mechanism,
                        "confidence": reply.confidence,
                        "supporting_facts": [fact.__dict__ for fact in reply.supporting_facts],
                        "model": agent.report(),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(reply.text)

    if args.prompt is not None:
        answer(args.prompt)
        agent.save(args.artifact)
        return

    print("MECI cognitive chat。終了は /exit、保存は /save、状態表示は /report")
    while True:
        try:
            text = input("あなた> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text == "/exit":
            break
        if text == "/save":
            agent.save(args.artifact)
            print(f"保存しました: {args.artifact}")
            continue
        if text == "/report":
            print(json.dumps(agent.report(), ensure_ascii=False, indent=2))
            continue
        answer(text)

    agent.save(args.artifact)


if __name__ == "__main__":
    main()
