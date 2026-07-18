from __future__ import annotations

import argparse
from pathlib import Path

from .mobile_unified_artifact import MobileUnifiedArtifact


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the sub-1GB mobile unified reasoning/dialogue artifact. "
            "The artifact is research-stage and not high-school intelligence."
        )
    )
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--once", help="answer one prompt and exit")
    args = parser.parse_args()
    model = MobileUnifiedArtifact.load(args.artifact)
    resources = model.resource_report()
    if not bool(resources["package_within_limit"]):
        raise SystemExit("artifact violates the decimal 1GB deployment limit")

    def answer(prompt: str) -> None:
        prediction = model.predict(prompt)
        print(prediction.answer)

    if args.once is not None:
        answer(args.once)
        return
    print(
        "Mobile unified research model. /quit で終了。"
        "高校生レベル・弱スマホ実機合格はまだ未達です。"
    )
    while True:
        try:
            prompt = input("you> ").strip()
        except EOFError:
            break
        if prompt in {"/quit", "/exit"}:
            break
        if not prompt:
            continue
        prediction = model.predict(prompt)
        print(f"model[{prediction.mode}]> {prediction.answer}")


if __name__ == "__main__":
    main()
