from __future__ import annotations

import argparse
from pathlib import Path

from .sparc_open_textbook_learner import OpenTextbookLearner


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded dialogue shell for SPARC open textbook experiment.")
    parser.add_argument("--model", type=Path, required=True)
    args = parser.parse_args()
    model = OpenTextbookLearner.from_bytes(args.model.read_bytes())
    print("SPARC open-textbook shell")
    print("質問はそのまま入力してください。事実は『資料ID<TAB>本文』で追加できます。")
    print("終了は /quit、状態は /report、保存は /save パス です。")
    turn = 0
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break
        if not line:
            continue
        if line == "/quit":
            break
        if line == "/report":
            print(model.report())
            continue
        if line.startswith("/save "):
            path = Path(line[6:].strip())
            path.write_bytes(model.to_bytes())
            print(f"保存しました: {path}")
            continue
        if "\t" in line:
            source_id, sentence = line.split("\t", 1)
            accepted, mechanism = model.read_sentence(sentence.strip(), source_id.strip())
            print("資料を知識グラフへ反映しました。" if accepted else f"反映を控えました: {mechanism}")
            continue
        if line.endswith(("?", "？", "。")):
            print(model.explain(line))
            continue
        turn += 1
        accepted, mechanism = model.read_sentence(line, f"対話資料{turn}")
        print("内容を知識グラフへ反映しました。" if accepted else f"内容を一意に解釈できないため、反映を控えました: {mechanism}")


if __name__ == "__main__":
    main()
