from __future__ import annotations

import argparse
import json
from pathlib import Path

from .sparc_goal_rules import SPARCHS13Model
from .sparc_hs13_experiment import configured_model


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SPARC-HS13 goal-directed learned-rule conversation shell"
    )
    parser.add_argument("--model", type=Path, help="load an existing HS13 model")
    parser.add_argument("--save", type=Path, help="save the model when the shell exits")
    parser.add_argument("--prompt", help="run one prompt and exit")
    args = parser.parse_args()

    model = SPARCHS13Model.load(args.model) if args.model else configured_model()
    if args.prompt is not None:
        print(model.reply(args.prompt).text)
        return

    print("SPARC-HS13 goal-directed rule conversation shell")
    print(
        "commands: /fact SOURCE TEXT, /revise SOURCE TEXT, /teach-rule PATH, "
        "/stats, /save PATH, /quit"
    )
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
        if user.startswith("/fact "):
            parts = user[6:].strip().split(maxsplit=1)
            if len(parts) != 2:
                print("system> usage: /fact SOURCE TEXT")
                continue
            source, text = parts
            inserted = model.ingest_fact(text, source_id=source)
            print(f"system> stored {len(inserted)} rule-evidence episodes")
            continue
        if user.startswith("/revise "):
            parts = user[8:].strip().split(maxsplit=1)
            if len(parts) != 2:
                print("system> usage: /revise SOURCE TEXT")
                continue
            source, text = parts
            inserted = model.ingest_fact(text, source_id=source, revision=True)
            print(f"system> stored {len(inserted)} revision episodes")
            continue
        if user.startswith("/teach-rule "):
            path = Path(user[12:].strip())
            rows = json.loads(path.read_text(encoding="utf-8"))
            rule = model.teach_rule(
                [(str(question), str(answer)) for question, answer in rows]
            )
            print(
                f"system> learned rule: {rule.head_relation}(x,z) <- "
                + " -> ".join(rule.body_relations)
                + f"; support={rule.support}"
            )
            continue

        reply = model.reply(user)
        print(f"sparc> {reply.text}")
        print(
            f"  [{reply.mechanism}; confidence={reply.confidence:.3f}; "
            f"candidates={reply.candidates_inspected}; active={reply.active_bits}; "
            f"ops≈{reply.estimated_sparse_operations}]"
        )

    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        model.save(args.save)
        print(f"system> saved: {args.save}")


if __name__ == "__main__":
    main()
