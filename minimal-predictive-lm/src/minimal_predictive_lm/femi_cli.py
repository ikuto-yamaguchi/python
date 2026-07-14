from __future__ import annotations

import argparse
import json

from .femi import FEMIChat, load_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="FEMI non-neural factorized chat")
    parser.add_argument("training_jsonl")
    parser.add_argument("prompt")
    args = parser.parse_args()
    chat = FEMIChat().fit(load_jsonl(args.training_jsonl))
    answer, activated = chat.reply_with_cost(args.prompt)
    print(
        json.dumps(
            {"reply": answer, "activated_factors": activated},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
