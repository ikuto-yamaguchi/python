from __future__ import annotations

import argparse
from pathlib import Path

from .cic_mixed_artifact import MixedCICArtifact


def render(model: MixedCICArtifact, text: str) -> str:
    row = model.predict(text)
    if row.mode == "choice":
        return f"{row.answer}［機構 {row.mechanism} / 候補確認 {row.work}］"
    if row.mode == "arithmetic":
        return f"答えは {row.answer} です。［機構 {row.mechanism} / 候補確認 {row.work}］"
    return row.answer


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive mixed CIC chat")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("question", nargs="?")
    args = parser.parse_args()
    model = MixedCICArtifact.load(args.artifact)
    if args.question:
        print(render(model, args.question))
        return
    print("CIC mixed chat。終了は /quit")
    while True:
        try:
            question = input("あなた> ").strip()
        except EOFError:
            break
        if question in {"/quit", "/exit"}:
            break
        if question:
            print("CIC>", render(model, question))


if __name__ == "__main__":
    main()
