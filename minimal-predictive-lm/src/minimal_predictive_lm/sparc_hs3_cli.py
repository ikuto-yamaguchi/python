from __future__ import annotations

import argparse
import json
from pathlib import Path

from .sparc_hs3_experiment import configured_model
from .sparc_reasoning import ReasoningResult
from .sparc_schema import SPARCHS3Model


def main() -> None:
    parser = argparse.ArgumentParser(description="SPARC-HS3 learned-schema Japanese model")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--prompt")
    parser.add_argument("--save", type=Path)
    args = parser.parse_args()

    model = SPARCHS3Model.load(args.model) if args.model else configured_model()
    if args.prompt is not None:
        print(model.reply(args.prompt).text)
        return

    print("SPARC-HS3 learned-schema conversation shell")
    print("commands: /stats, /save PATH, /quit")
    while True:
        try:
            user = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        if user == "/quit":
            break
        if user == "/stats":
            print(json.dumps(model.report(), ensure_ascii=False, indent=2))
            continue
        if user.startswith("/save "):
            path = Path(user[6:].strip())
            path.parent.mkdir(parents=True, exist_ok=True)
            model.save(path)
            print(f"system> saved: {path}")
            continue
        reply = model.reply(user)
        print(f"sparc> {reply.text}")
        if isinstance(reply, ReasoningResult):
            print(
                f"  [{reply.mechanism}; confidence={reply.confidence:.3f}; "
                f"nodes={reply.nodes_activated}; edges={reply.edges_inspected}; hops={len(reply.path)}; "
                f"schemas={model.schemas.last_candidates_inspected}; anchor_reads={model.schemas.last_anchor_reads}]"
            )
        else:
            print(f"  [{reply.mechanism}; confidence={reply.confidence:.3f}]")

    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        model.save(args.save)
        print(f"system> saved: {args.save}")


if __name__ == "__main__":
    main()
