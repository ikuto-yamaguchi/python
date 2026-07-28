#!/usr/bin/env python3
"""Fail-closed audit for Unicode/case aliases in R0 cell identities.

Domain and condition labels define the domain×seed×split×condition cells used by
coverage, shuffle assignment, summaries, and paired tests.  Treating visually or
semantically identical labels as distinct cells can hide missing coverage or move
shuffle donors across an apparent boundary.  This auditor rejects such aliases.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

CLASSIFICATION = "initial_reproduction_failure"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: row must be an object")
            rows.append(value)
    return rows


def canonical_cell_label(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    return "".join(
        ch for ch in text
        if not ch.isspace() and unicodedata.category(ch) not in {"Cf", "Cc"}
    )


def canonical_condition(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    parts = [
        canonical_cell_label(part)
        for part in re.split(r"[+,|\s]+", text)
        if canonical_cell_label(part)
    ]
    return "+".join(sorted(set(parts)))


def audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    findings: list[dict[str, Any]] = []
    observed: dict[str, dict[str, set[str]]] = {
        "domain": defaultdict(set),
        "condition": defaultdict(set),
    }

    for index, row in enumerate(rows, 1):
        for field, normalizer in (
            ("domain", canonical_cell_label),
            ("condition", canonical_condition),
        ):
            if field not in row:
                errors.append(f"row {index}: missing {field}")
                continue
            raw = str(row[field])
            canonical = normalizer(raw)
            if not canonical:
                errors.append(f"row {index}: {field} is empty after normalization")
                continue
            observed[field][canonical].add(raw)

    for field in ("domain", "condition"):
        for canonical, raw_values in sorted(observed[field].items()):
            if len(raw_values) <= 1:
                continue
            finding = {
                "field": field,
                "canonical": canonical,
                "raw_values": sorted(raw_values),
            }
            findings.append(finding)
            errors.append(
                f"{field} canonical collision for {canonical!r}: {sorted(raw_values)!r}"
            )

    return {
        "valid": not errors,
        "errors": errors,
        "classification": "qualified" if not errors else CLASSIFICATION,
        "normalized_cell_identity_required": True,
        "normalization": {
            "domain": "NFKC + casefold + remove whitespace/control-format characters",
            "condition": "domain normalization + split on +,|/whitespace + sort/deduplicate tokens",
        },
        "findings": findings,
        "canonical_domains": sorted(observed["domain"]),
        "canonical_conditions": sorted(observed["condition"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(read_jsonl(args.dataset))
    text = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
