from __future__ import annotations

import argparse
from pathlib import Path

from .sparc_relational_world import ACTUAL, RelationalWorldLearner


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded SPARC relational-world dialogue shell")
    parser.add_argument("--model", type=Path, required=True)
    args = parser.parse_args()
    model = RelationalWorldLearner.from_bytes(args.model.read_bytes())
    print("SPARC relational-world shell. /state, /reset, /quit")
    while True:
        try:
            text = input("> ").strip()
        except EOFError:
            break
        if not text:
            continue
        if text == "/quit":
            break
        if text == "/reset":
            model.state.clear()
            model.focus_subject = None
            print("会話中の世界状態を消去しました。")
            continue
        if text == "/state":
            if not model.state:
                print("状態は空です。")
                continue
            for key, value in sorted(model.state.items()):
                scope = "実際" if key.scope == ACTUAL else f"{key.scope}の認識"
                print(f"{scope}: {key.subject} / {key.relation} = {value}")
            continue
        print(model.process(text).answer)


if __name__ == "__main__":
    main()
