from __future__ import annotations

import argparse
from pathlib import Path

from .cic_artifact import CICArtifact


def answer(model: CICArtifact, question: str) -> str:
    prediction, mechanism, checked = model.predict(question)
    if prediction is None:
        return "まだこの質問を実行できる機構を獲得していません。"
    return f"答えは {prediction} です。［機構 {mechanism} / 候補確認 {checked}］"


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive CIC arithmetic chat")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("question", nargs="?")
    args = parser.parse_args()
    model = CICArtifact.load(args.artifact)
    if args.question:
        print(answer(model, args.question))
        return
    print("CIC arithmetic chat。終了は /quit")
    while True:
        try:
            question = input("あなた> ").strip()
        except EOFError:
            break
        if question in {"/quit", "/exit"}:
            break
        if question:
            print("CIC>", answer(model, question))


if __name__ == "__main__":
    main()
