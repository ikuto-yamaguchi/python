from __future__ import annotations

import argparse
from pathlib import Path

from .sparc_narrative_world import NarrativeWorldLearner


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded narrative-world dialogue shell")
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    model = NarrativeWorldLearner.from_bytes(Path(args.model).read_bytes())
    model.reset_session()
    print("文章で初期状態や出来事を入力してください。終了は /exit、状態消去は /reset です。")
    while True:
        try:
            text = input("> ").strip()
        except EOFError:
            break
        if not text:
            continue
        if text == "/exit":
            break
        if text == "/reset":
            model.reset_session()
            print("内部状態を消去しました。")
            continue
        print(model.respond(text))


if __name__ == "__main__":
    main()
