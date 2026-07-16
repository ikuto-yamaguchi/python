from __future__ import annotations

import argparse
import json
from pathlib import Path

from .sparc_hs12_experiment_v2 import configured_model
from .sparc_relational_plans import SPARCHS12Model


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SPARC-HS12 learned relational-plan conversation shell"
    )
    parser.add_argument("--model", type=Path, help="load an existing HS12 model")
    parser.add_argument("--save", type=Path, help="save the model when the shell exits")
    parser.add_argument("--prompt", help="run one prompt and exit")
    args = parser.parse_args()

    model = SPARCHS12Model.load(args.model) if args.model else configured_model()
    if args.prompt is not None:
        print(model.reply(args.prompt).text)
        return

    print("SPARC-HS12 relational-plan conversation shell")
    print(
        "commands: /fact SOURCE TEXT, /revise SOURCE TEXT, /teach-path PATH, "
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
            print(f"system> stored {len(inserted)} relation episodes")
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
        if user.startswith("/teach-path "):
            path = Path(user[12:].strip())
            rows = json.loads(path.read_text(encoding="utf-8"))
            plan = model.teach_relational_plan(
                [(str(question), str(answer)) for question, answer in rows]
            )
            print(
                "system> learned relation path: "
                + " -> ".join(plan.relations)
                + f"; support={plan.support}"
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
