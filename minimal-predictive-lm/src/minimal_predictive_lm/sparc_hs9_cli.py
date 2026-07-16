from __future__ import annotations

import argparse
import json
from pathlib import Path

from .sparc_discourse_compact import SPARCHS9CompactModel
from .sparc_hs9_compact_experiment import configured_model


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SPARC-HS9 compact sparse discourse conversation shell"
    )
    parser.add_argument("--model", type=Path, help="load an existing HS9 model")
    parser.add_argument("--save", type=Path, help="save when the shell exits")
    parser.add_argument("--prompt", help="run one prompt and exit")
    args = parser.parse_args()

    model = (
        SPARCHS9CompactModel.load(args.model)
        if args.model
        else configured_model()
    )
    if args.prompt is not None:
        print(model.reply(args.prompt).text)
        return

    print("SPARC-HS9 compact discourse conversation shell")
    print(
        "commands: /article SOURCE TITLE PATH, /article-text SOURCE TITLE TEXT, "
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
        if user.startswith("/article "):
            parts = user[9:].strip().split(maxsplit=2)
            if len(parts) != 3:
                print("system> usage: /article SOURCE TITLE PATH")
                continue
            source, title, path_text = parts
            path = Path(path_text)
            document_id = model.ingest_discourse(
                path.read_text(encoding="utf-8"),
                source_id=source,
                title=title,
            )
            print(f"system> discourse document {document_id} learned")
            continue
        if user.startswith("/article-text "):
            parts = user[14:].strip().split(maxsplit=2)
            if len(parts) != 3:
                print("system> usage: /article-text SOURCE TITLE TEXT")
                continue
            source, title, text = parts
            document_id = model.ingest_discourse(text, source_id=source, title=title)
            print(f"system> discourse document {document_id} learned")
            continue

        reply = model.reply(user)
        print(f"sparc> {reply.text}")
        print(
            f"  [{reply.mechanism}; confidence={reply.confidence:.3f}; "
            f"candidates={reply.candidates_inspected}; "
            f"active={reply.active_bits}; ops≈{reply.estimated_sparse_operations}]"
        )

    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        model.save(args.save)
        print(f"system> saved: {args.save}")


if __name__ == "__main__":
    main()
