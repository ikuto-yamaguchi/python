#!/usr/bin/env python3
"""Idempotently suppress score statistics whenever any score contract error exists."""
from __future__ import annotations

from pathlib import Path

TARGET = Path(__file__).with_name("evaluation_contract.py")


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count == 0 and new in text:
        return text
    if count != 1:
        raise RuntimeError(f"expected exactly one core fragment, found {count}: {old[:100]!r}")
    return text.replace(old, new, 1)


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "    if not dataset_audit.get(\"valid\", False):\n        cells = []\n        summary = defaultdict(dict)\n        gaps = {}\n",
        "    if errors:\n        cells = []\n        summary = defaultdict(dict)\n        gaps = {}\n",
    )
    text = replace_once(
        text,
        '"invalid_dataset_statistics_forbidden": True, "prediction_rows": len(preds),',
        '"invalid_dataset_statistics_forbidden": True, "invalid_score_statistics_forbidden": True, "statistics_emitted": not errors, "prediction_rows": len(preds),',
    )
    TARGET.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
