from __future__ import annotations

import argparse
import json
from pathlib import Path

from .sparc_curriculum import seed_sessions
from .sparc_language import SCALE_PROFILES, SPARCLanguageModel


def _new_model(profile: str) -> SPARCLanguageModel:
    return SPARCLanguageModel(profile).fit_sessions(seed_sessions())


def main() -> None:
    parser = argparse.ArgumentParser(description="SPARC-HS1 sparse Japanese conversational model")
    parser.add_argument("--model", type=Path, help="load an existing .model.zlib artifact")
    parser.add_argument("--profile", choices=sorted(SCALE_PROFILES), default="ci")
    parser.add_argument("--prompt", help="run one prompt and exit")
    parser.add_argument("--save", type=Path, help="save the model after the session")
    args = parser.parse_args()

    model = SPARCLanguageModel.load(args.model) if args.model else _new_model(args.profile)
    if args.prompt is not None:
        print(model.reply(args.prompt).text)
        return

    print("SPARC-HS1 conversation shell")
    print("commands: /teach question => answer, /stats, /reset, /save PATH, /quit")
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
            model.reset()
            print("system> working memory cleared")
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
        if user.startswith("/teach "):
            lesson = user[7:]
            if "=>" not in lesson:
                print("system> usage: /teach question => answer")
                continue
            question, answer = (part.strip() for part in lesson.split("=>", 1))
            model.learn(question, answer)
            print("system> learned")
            continue
        reply = model.reply(user)
        print(f"sparc> {reply.text}")
        print(f"  [{reply.mechanism}; confidence={reply.confidence:.3f}; candidates={reply.candidates_inspected}; ops≈{reply.estimated_sparse_operations}]")

    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        model.save(args.save)
        print(f"system> saved: {args.save}")


if __name__ == "__main__":
    main()
