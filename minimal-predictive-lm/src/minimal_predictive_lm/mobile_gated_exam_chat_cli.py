from __future__ import annotations

import argparse
import json

from .mobile_gated_exam_artifact import MobileGatedExamArtifact


def _render(artifact: MobileGatedExamArtifact, text: str, *, debug: bool) -> str:
    prediction = artifact.predict(text)
    if not debug:
        return prediction.answer
    return json.dumps(
        {
            "answer": prediction.answer,
            "mode": prediction.mode,
            "confidence": prediction.confidence,
            "memory_probability": prediction.memory_probability,
            "work": prediction.work,
            "evidence_titles": prediction.evidence_titles,
        },
        ensure_ascii=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact")
    parser.add_argument("--once")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    artifact = MobileGatedExamArtifact.load(args.artifact)
    if args.once is not None:
        print(_render(artifact, args.once, debug=args.debug))
        return

    print("大学入試研究モデル。終了するには /exit を入力してください。")
    while True:
        try:
            text = input("あなた> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if text in {"/exit", "/quit"}:
            return
        if not text:
            continue
        print("モデル> " + _render(artifact, text, debug=args.debug))


if __name__ == "__main__":
    main()
