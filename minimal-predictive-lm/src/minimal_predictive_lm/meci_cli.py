from __future__ import annotations

import argparse
import json

from .meci_chat import MECIChat, load_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="MECI non-neural chat")
    parser.add_argument("training_jsonl")
    parser.add_argument("prompt")
    parser.add_argument("--order", type=int, default=16)
    parser.add_argument("--max-new-bytes", type=int, default=160)
    args = parser.parse_args()
    chat = MECIChat(max_order=args.order).fit(load_jsonl(args.training_jsonl))
    result = {
        "reply": chat.reply(args.prompt, max_new_bytes=args.max_new_bytes),
        "model": chat.model.report(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
