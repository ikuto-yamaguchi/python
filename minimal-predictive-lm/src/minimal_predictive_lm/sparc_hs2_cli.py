from __future__ import annotations

import argparse
import json
from pathlib import Path

from .sparc_curriculum import seed_sessions
from .sparc_hs2 import SPARCHS2Model
from .sparc_language import SCALE_PROFILES
from .sparc_reasoning import REASONING_PROFILES, ReasoningResult


def _new_model(language_profile: str, reasoning_profile: str) -> SPARCHS2Model:
    records = [row for session in seed_sessions() for row in session]
    return SPARCHS2Model(language_profile, reasoning_profile).fit_dialogues(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="SPARC-HS2 sparse Japanese reasoning model")
    parser.add_argument("--model", type=Path, help="load an existing HS2 .model.zlib artifact")
    parser.add_argument("--language-profile", choices=sorted(SCALE_PROFILES), default="ci")
    parser.add_argument("--reasoning-profile", choices=sorted(REASONING_PROFILES), default="ci")
    parser.add_argument("--prompt", help="run one prompt and exit")
    parser.add_argument("--save", type=Path, help="save the model after the session")
    args = parser.parse_args()

    model = (
        SPARCHS2Model.load(args.model)
        if args.model
        else _new_model(args.language_profile, args.reasoning_profile)
    )
    if args.prompt is not None:
        print(model.reply(args.prompt).text)
        return

    print("SPARC-HS2 relational conversation shell")
    print("Teach facts as ordinary Japanese sentences.")
    print("commands: /teach question => answer, /stats, /save PATH, /quit")
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
        if user.startswith("/teach "):
            lesson = user[7:]
            if "=>" not in lesson:
                print("system> usage: /teach question => answer")
                continue
            question, answer = (part.strip() for part in lesson.split("=>", 1))
            print(f"system> {model.learn(question, answer)}")
            continue
        reply = model.reply(user)
        print(f"sparc> {reply.text}")
        if isinstance(reply, ReasoningResult):
            print(
                f"  [{reply.mechanism}; confidence={reply.confidence:.3f}; "
                f"nodes={reply.nodes_activated}; edges={reply.edges_inspected}; hops={len(reply.path)}]"
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
