from __future__ import annotations

import argparse
import json
from pathlib import Path

from .sparc_hs4_experiment import configured_model
from .sparc_raw_induction import RawCurriculumModel
from .sparc_reasoning import ReasoningResult


def main() -> None:
    parser = argparse.ArgumentParser(description="SPARC-HS4 raw Japanese curriculum model")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--prompt")
    parser.add_argument("--save", type=Path)
    args = parser.parse_args()

    model = RawCurriculumModel.load(args.model) if args.model else configured_model()
    if args.prompt is not None:
        print(model.reply(args.prompt).text)
        return

    print("SPARC-HS4 raw-curriculum conversation shell")
    print("commands: /ingest FILE, /qa question => answer, /stats, /save PATH, /quit")
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
        if user.startswith("/ingest "):
            path = Path(user[8:].strip())
            sentences = [
                line.strip()
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            model.fit_raw(sentences)
            report = model.miner.report
            print(
                f"system> ingested {report.sentences} sentences; "
                f"schemas={report.schemas}; facts={report.facts}"
            )
            continue
        if user.startswith("/qa "):
            lesson = user[4:]
            if "=>" not in lesson:
                print("system> usage: /qa question => answer")
                continue
            question, answer = (part.strip() for part in lesson.split("=>", 1))
            print(
                "system> aligned"
                if model.align_qa(question, answer)
                else "system> alignment failed"
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
            print(f"  [{reply.mechanism}; confidence={reply.confidence:.3f}]")

    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        model.save(args.save)
        print(f"system> saved: {args.save}")


if __name__ == "__main__":
    main()
