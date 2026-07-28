#!/usr/bin/env python3
"""Fail-closed audit for split-label aliases across R0 dataset/resource evidence."""
from __future__ import annotations

import argparse
import json
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

TRAIN_SPLITS = {"train"}
EVAL_SPLITS = {"test", "eval", "validation", "valid"}
ALLOWED_SPLITS = TRAIN_SPLITS | EVAL_SPLITS


def canonical_split(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    return "".join(
        ch for ch in text
        if not ch.isspace() and unicodedata.category(ch) not in {"Cf", "Cc"}
    )


def _load_json_or_jsonl(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        rows = []
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: each JSONL row must be an object")
            rows.append(value)
        return rows


def audit_split_rows(rows: list[dict[str, Any]], *, evaluation_only: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    raw_by_canonical: dict[str, set[str]] = defaultdict(set)
    findings: list[dict[str, Any]] = []
    allowed = EVAL_SPLITS if evaluation_only else ALLOWED_SPLITS

    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            errors.append(f"row {index}: must be an object")
            continue
        if "split" not in row:
            errors.append(f"row {index}: split is required")
            continue
        raw = str(row["split"])
        canonical = canonical_split(raw)
        raw_by_canonical[canonical].add(raw)
        finding = {"row": index, "raw_split": raw, "canonical_split": canonical}
        findings.append(finding)
        if not canonical:
            errors.append(f"row {index}: split must be non-empty after canonicalization")
        elif canonical not in allowed:
            errors.append(
                f"row {index}: unregistered canonical split={canonical!r}; allowed={sorted(allowed)}"
            )
        if raw != canonical:
            errors.append(
                f"row {index}: split must use exact canonical spelling {canonical!r}, found {raw!r}"
            )

    collisions = {
        canonical: sorted(raw_values)
        for canonical, raw_values in raw_by_canonical.items()
        if canonical and len(raw_values) > 1
    }
    if collisions:
        errors.append(f"split labels collide after canonicalization: {collisions}")

    return {
        "valid": not errors,
        "errors": errors,
        "classification": "reproduced" if not errors else "initial_reproduction_failure",
        "canonical_split_identity_required": True,
        "exact_canonical_split_spelling_required": True,
        "split_identity_normalization": "NFKC + casefold + remove whitespace/control-format characters",
        "allowed_splits": sorted(allowed),
        "split_label_collisions": collisions,
        "findings": findings,
    }


def audit_payload(payload: Any, *, evaluation_only: bool = False) -> dict[str, Any]:
    if isinstance(payload, dict) and "runs" in payload:
        runs = payload.get("runs")
        if not isinstance(runs, list) or not runs:
            return {
                "valid": False,
                "errors": ["manifest.runs must be a non-empty list"],
                "classification": "initial_reproduction_failure",
            }
        return audit_split_rows(runs, evaluation_only=True)
    if not isinstance(payload, list):
        return {
            "valid": False,
            "errors": ["input must be JSONL rows, a JSON array, or a manifest with runs"],
            "classification": "initial_reproduction_failure",
        }
    return audit_split_rows(payload, evaluation_only=evaluation_only)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--evaluation-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = audit_payload(_load_json_or_jsonl(args.input), evaluation_only=args.evaluation_only)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "valid": False,
            "errors": [str(exc)],
            "classification": "initial_reproduction_failure",
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
