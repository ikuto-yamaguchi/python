from __future__ import annotations

import argparse
import json
from pathlib import Path

from .sparc_abstraction_topic import SPARCHS9Model
from .sparc_hs9_experiment import configured_model


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SPARC-HS9 abstraction, comparison and argument conversation shell"
    )
    parser.add_argument("--model", type=Path, help="load an existing HS9 model")
    parser.add_argument("--save", type=Path, help="save the model when the shell exits")
    parser.add_argument("--prompt", help="run one prompt and exit")
    args = parser.parse_args()

    model = SPARCHS9Model.load(args.model) if args.model else configured_model()
    if args.prompt is not None:
        print(model.reply(args.prompt).text)
        return

    print("SPARC-HS9 abstraction conversation shell")
    print(
        "commands: /read SOURCE PATH, /read-text SOURCE TEXT, /revise SOURCE TEXT, "
        "/stats, /reset, /save PATH, /quit"
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
        if user == "/reset":
            model.base.reset_workspace()
            print("system> bounded working memory cleared")
            continue
        if user == "/stats":
            print(json.dumps(model.report(), ensure_ascii=False, indent=2))
            continue
        if user.startswith("/save "):
            path = Path(user[6:].strip())
            path.parent.mkdir(parents=True, exist_ok=True)
            model.save(path)
            print(f"system> saved: {path}")
            continue
        if user.startswith("/read "):
            parts = user[6:].strip().split(maxsplit=1)
            if len(parts) != 2:
                print("system> usage: /read SOURCE PATH")
                continue
            source, path_text = parts
            path = Path(path_text)
            inserted = model.ingest_document(
                path.read_text(encoding="utf-8"), source_id=source
            )
            print(f"system> learned {len(inserted)} paragraphs from {source}")
            continue
        if user.startswith("/read-text "):
            parts = user[11:].strip().split(maxsplit=1)
            if len(parts) != 2:
                print("system> usage: /read-text SOURCE TEXT")
                continue
            source, text = parts
            inserted = model.ingest_document(text, source_id=source)
            print(f"system> learned {len(inserted)} paragraphs from {source}")
            continue
        if user.startswith("/revise "):
            parts = user[8:].strip().split(maxsplit=1)
            if len(parts) != 2:
                print("system> usage: /revise SOURCE TEXT")
                continue
            source, text = parts
            inserted = model.revise(text, source_id=source)
            print(f"system> revision stored in {len(inserted)} episodes")
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
