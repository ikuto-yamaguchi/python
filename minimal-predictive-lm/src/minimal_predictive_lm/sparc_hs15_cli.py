from __future__ import annotations

import argparse
import json
from pathlib import Path

from .sparc_perspective_state import SPARCHS15Model
from .sparc_hs15_experiment import configured_model


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SPARC-HS15 perspective-state conversation shell"
    )
    parser.add_argument("--model", type=Path, help="load an existing HS15 model")
    parser.add_argument("--save", type=Path, help="save the model when the shell exits")
    parser.add_argument("--prompt", help="run one prompt and exit")
    args = parser.parse_args()

    model = SPARCHS15Model.load(args.model) if args.model else configured_model()
    if args.prompt:
        print(model.reply(args.prompt).text)
        return

    print("SPARC-HS15 perspective shell")
    print("/event SOURCE => SENTENCE, /focus, /stats, /save PATH, /quit")
    while True:
        try:
            text = input("you> ").strip()
        except EOFError:
            break
        if not text:
            continue
        if text == "/quit":
            break
        if text == "/focus":
            print(json.dumps(list(model.perspective.focus), ensure_ascii=False))
            continue
        if text == "/stats":
            print(json.dumps(model.report(), ensure_ascii=False, indent=2))
            continue
        if text.startswith("/save "):
            path = Path(text[6:].strip())
            model.save(path)
            print(f"saved: {path}")
            continue
        if text.startswith("/event ") and "=>" in text:
            header, sentence = text[7:].split("=>", 1)
            record = model.perspective.apply_event(
                sentence.strip(), source_id=header.strip()
            )
            if record is None:
                print("system> この出来事の表面形はまだ学習されていません。")
            else:
                print(
                    "system> "
                    f"{record.object_name}の{record.attribute}を"
                    f"{record.previous_value}から{record.new_value}へ更新しました。"
                )
            continue
        reply = model.reply(text)
        print(f"model> {reply.text}")

    if args.save:
        model.save(args.save)


if __name__ == "__main__":
    main()
