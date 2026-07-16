from __future__ import annotations

import argparse
import json
from pathlib import Path

from .sparc_hs5_experiment import configured_model
from .sparc_programs import SPARCHS5Model
from .sparc_reasoning import ReasoningResult


def main() -> None:
    parser = argparse.ArgumentParser(description="SPARC-HS5 shared curriculum model")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--prompt")
    parser.add_argument("--save", type=Path)
    args = parser.parse_args()

    model = SPARCHS5Model.load(args.model) if args.model else configured_model()
    if args.prompt is not None:
        print(model.reply(args.prompt).text)
        return

    print("SPARC-HS5 shared curriculum conversation shell")
    print("commands: /teach-math FILE.json, /stats, /save PATH, /quit")
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
        if user.startswith("/teach-math "):
            path = Path(user[12:].strip())
            rows = json.loads(path.read_text(encoding="utf-8"))
            examples = [(str(row["problem"]), row["answer"]) for row in rows]
            learned = model.teach_math(examples)
            print(
                f"system> learned program={learned.program_name}; "
                f"examples={learned.examples}; competitors={learned.competing_programs}"
            )
            continue
        reply = model.reply(user)
        print(f"sparc> {reply.text}")
        if isinstance(reply, ReasoningResult):
            print(
                f"  [{reply.mechanism}; confidence={reply.confidence:.3f}; "
                f"nodes={reply.nodes_activated}; edges={reply.edges_inspected}; "
                f"hops={len(reply.path)}]"
            )
        else:
            print(
                f"  [{reply.mechanism}; confidence={reply.confidence:.3f}; "
                f"candidates={reply.candidates_inspected}; ops≈{reply.estimated_sparse_operations}]"
            )

    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        model.save(args.save)
        print(f"system> saved: {args.save}")


if __name__ == "__main__":
    main()
