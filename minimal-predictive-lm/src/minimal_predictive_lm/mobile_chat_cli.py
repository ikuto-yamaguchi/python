from __future__ import annotations

import argparse
import json
from pathlib import Path

from .mobile_sparse_core import CI_MOBILE_PROFILE, MobilePagedSparseCore


DEMO_DIALOGUES = (
    ("こんにちは", "こんにちは。何について考えましょうか？"),
    (
        "君は高校生レベル？",
        "いいえ。現在は研究中で、高校生レベルの評価にはまだ合格していません。",
    ),
    ("モデルサイズの上限は？", "全モデル一式で10億バイト以下が絶対条件です。"),
)


def load_jsonl(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        rows.append((str(item["prompt"]), str(item["response"])))
    return rows


def build_core(teach: Path | None) -> MobilePagedSparseCore:
    core = MobilePagedSparseCore(CI_MOBILE_PROFILE, seed=11)
    for prompt, response in DEMO_DIALOGUES:
        core.remember(prompt, response)
    if teach is not None:
        for prompt, response in load_jsonl(teach):
            core.remember(prompt, response)
    return core


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Executable mobile sparse chat path; not yet high-school intelligence."
    )
    parser.add_argument("--teach", type=Path, help="JSONL prompt/response memory")
    parser.add_argument("--once", help="Answer one prompt and exit")
    args = parser.parse_args()
    core = build_core(args.teach)
    if args.once is not None:
        print(core.generate(args.once))
        return
    print("Mobile sparse chat research shell. /quit で終了。高校生レベルは未達です。")
    while True:
        try:
            prompt = input("you> ").strip()
        except EOFError:
            break
        if prompt in {"/quit", "/exit"}:
            break
        if not prompt:
            continue
        print("model> " + core.generate(prompt))


if __name__ == "__main__":
    main()
