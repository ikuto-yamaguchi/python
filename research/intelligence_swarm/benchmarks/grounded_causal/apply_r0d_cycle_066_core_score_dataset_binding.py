#!/usr/bin/env python3
"""Idempotently bind score() to validate_dataset() and suppress invalid statistics."""
from __future__ import annotations

from pathlib import Path

TARGET = Path(__file__).with_name("evaluation_contract.py")


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count == 0 and new in text:
        return text
    if count != 1:
        raise RuntimeError(f"expected exactly one core fragment, found {count}: {old[:80]!r}")
    return text.replace(old, new, 1)


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "def score(data: list[dict[str, Any]], preds: list[dict[str, Any]]) -> dict[str, Any]:\n    adapted = adapt_dataset(data)\n",
        "def score(data: list[dict[str, Any]], preds: list[dict[str, Any]]) -> dict[str, Any]:\n    dataset_audit = validate_dataset(data)\n    adapted = adapt_dataset(data)\n",
    )
    text = replace_once(
        text,
        "    errors, seen = [], set(); method_ids, grouped, snapshots, outcomes = defaultdict(set), defaultdict(list), defaultdict(set), defaultdict(dict)\n",
        "    errors, seen = list(dataset_audit.get(\"errors\", [])), set(); method_ids, grouped, snapshots, outcomes = defaultdict(set), defaultdict(list), defaultdict(set), defaultdict(dict)\n",
    )
    text = replace_once(
        text,
        "    return {\"valid\": not errors, \"errors\": errors, \"classification\": \"qualified\" if not errors else \"initial_reproduction_failure\",",
        "    if not dataset_audit.get(\"valid\", False):\n        cells = []\n        summary = defaultdict(dict)\n        gaps = {}\n    return {\"valid\": not errors, \"errors\": errors, \"classification\": \"qualified\" if not errors else \"initial_reproduction_failure\", \"dataset_contract_binding\": True, \"dataset_contract_valid\": bool(dataset_audit.get(\"valid\", False)), \"dataset_contract_errors\": list(dataset_audit.get(\"errors\", [])), \"invalid_dataset_statistics_forbidden\": True,",
    )
    TARGET.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
