from __future__ import annotations

import argparse
from pathlib import Path

from .sparc_textbook_learner import SparseTextbookLearner


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bounded dialogue shell for the sparse textbook learner."
    )
    parser.add_argument("--model", type=Path, required=True)
    args = parser.parse_args()
    model = SparseTextbookLearner.from_bytes(args.model.read_bytes())

    print("SPARC textbook dialogue")
    print("質問を入力してください。資料追加: :read SOURCE 日本語文")
    print("概念は「日本語」の鉤括弧で示してください。終了: :quit")
    while True:
        try:
            text = input("> ").strip()
        except EOFError:
            break
        if not text:
            continue
        if text in {":quit", ":exit"}:
            break
        if text == ":report":
            print(model.report())
            continue
        if text.startswith(":save "):
            path = Path(text[6:].strip())
            path.write_bytes(model.to_bytes())
            print(f"保存しました: {path}")
            continue
        if text.startswith(":read "):
            rest = text[6:].strip()
            source, separator, sentence = rest.partition(" ")
            if not separator or not sentence:
                print("形式: :read SOURCE 日本語文")
                continue
            accepted, mechanism = model.read_sentence(sentence, source)
            print("資料を反映しました。" if accepted else f"反映しませんでした: {mechanism}")
            continue
        print(model.explain(text))


if __name__ == "__main__":
    main()
