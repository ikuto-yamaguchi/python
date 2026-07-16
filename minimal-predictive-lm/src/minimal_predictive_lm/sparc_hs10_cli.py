from __future__ import annotations

import argparse
import json
from pathlib import Path

from .sparc_hs10_experiment import configured_model
from .sparc_role_induction_v2 import SPARCHS10ModelV2


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SPARC-HS10 learned discourse-role conversation shell"
    )
    parser.add_argument("--model", type=Path, help="load an existing HS10 model")
    parser.add_argument("--save", type=Path, help="save the model when the shell exits")
    parser.add_argument("--prompt", help="run one prompt and exit")
    args = parser.parse_args()

    model = SPARCHS10ModelV2.load(args.model) if args.model else configured_model()
    if args.prompt is not None:
        print(model.reply(args.prompt).text)
        return

    print("SPARC-HS10 learned discourse-role conversation shell")
    print(
        "commands: /fit-role PATH, /read-role SOURCE TITLE PATH, /stats, "
        "/save PATH, /quit"
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
        if user.startswith("/fit-role "):
            path = Path(user[10:].strip())
            documents = [
                block.strip()
                for block in path.read_text(encoding="utf-8").split("\n\n")
                if block.strip()
            ]
            learned = model.fit_role_documents(documents)
            print(f"system> learned weak role structure from {learned} documents")
            continue
        if user.startswith("/read-role "):
            parts = user[11:].strip().split(maxsplit=2)
            if len(parts) != 3:
                print("system> usage: /read-role SOURCE TITLE PATH")
                continue
            source, title, path_text = parts
            document_id = model.ingest_learned_discourse(
                Path(path_text).read_text(encoding="utf-8"),
                source_id=source,
                title=title,
            )
            print(f"system> learned discourse document {document_id}: {title}")
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
