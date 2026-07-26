#!/usr/bin/env python3
"""Fail-closed Unicode-normalized train/evaluation utterance overlap audit for R0."""
from __future__ import annotations

import argparse
import json
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

EVAL_SPLITS = {"test", "eval", "validation", "valid"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: each row must be an object")
            rows.append(value)
    return rows


def normalize_utterance(value: Any) -> str:
    """Canonicalize token sequences and Unicode text without semantic guessing."""
    if isinstance(value, (list, tuple)):
        return "tokens:" + ",".join(str(int(token)) for token in value)
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    return "".join(
        character
        for character in text
        if not character.isspace() and unicodedata.category(character) not in {"Cf", "Cc"}
    )


def audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    by_split: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    for row_number, row in enumerate(rows, 1):
        split = str(row.get("split", "")).strip().lower()
        if not split:
            errors.append(f"row {row_number}: split must be non-empty")
            continue
        utterance = row.get("utterance", row.get("text_tokens"))
        if utterance is None:
            errors.append(f"row {row_number}: utterance/text_tokens is required")
            continue
        normalized = normalize_utterance(utterance)
        if not normalized or normalized == "tokens:":
            warnings.append(f"row {row_number}: normalized utterance is empty")
        by_split[split][normalized].append(str(row.get("instance_id", f"row-{row_number}")))

    train = set(by_split.get("train", {}))
    overlap: dict[str, Any] = {}
    for split in sorted(set(by_split) - {"train"}):
        shared = sorted(train & set(by_split[split]))
        examples = [
            {
                "normalized": normalized,
                "train_instance_ids": by_split["train"][normalized][:5],
                "eval_instance_ids": by_split[split][normalized][:5],
            }
            for normalized in shared[:5]
        ]
        overlap[split] = {"count": len(shared), "examples": examples}
        if split in EVAL_SPLITS and shared:
            errors.append(f"Unicode-normalized utterance leakage train->{split}: {len(shared)} utterances")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": sorted(set(warnings)),
        "classification": "qualified" if not errors else "initial_reproduction_failure",
        "normalization": "NFKC + casefold + remove whitespace/control-format characters",
        "utterance_overlap": overlap,
        "rows": len(rows),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit(read_jsonl(args.dataset))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "valid": False,
            "errors": [str(exc)],
            "classification": "initial_reproduction_failure",
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
