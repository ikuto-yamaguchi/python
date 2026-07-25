#!/usr/bin/env python3
"""Fail-closed audit for R0.2 entity/dynamics/language-form holdouts.

This is an evaluation contract, not a new model or mechanism. It rejects the
legacy placeholder convention where entity/dynamics holdouts are always false
and every test row is called a language holdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

CANONICAL_SEEDS = (1, 7, 19)
HOLDOUTS = {
    "entity_holdout": "entity_signature",
    "dynamics_holdout": "dynamics_signature",
    "language_holdout": "language_form_signature",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"line {line_number}: expected object")
            rows.append(row)
    if not rows:
        raise ValueError("empty dataset")
    return rows


def dataset_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(rows: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    failures: list[str] = []
    by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_split[str(row.get("split", ""))].append(row)

    if not by_split.get("train") or not by_split.get("test"):
        failures.append("both train and test rows are required")

    observed_seeds = {int(row["seed"]) for row in rows if "seed" in row}
    if observed_seeds != set(CANONICAL_SEEDS):
        failures.append(
            f"canonical seeds required: expected={list(CANONICAL_SEEDS)} observed={sorted(observed_seeds)}"
        )

    train = by_split.get("train", [])
    test = by_split.get("test", [])
    cells: dict[str, Any] = {}

    for condition, signature_field in HOLDOUTS.items():
        selected = [row for row in test if bool(row.get(condition, False))]
        condition_seeds = {int(row["seed"]) for row in selected if "seed" in row}
        signatures = {str(row.get(signature_field, "")) for row in selected}
        signatures.discard("")
        train_signatures = {str(row.get(signature_field, "")) for row in train}
        train_signatures.discard("")
        overlap = sorted(signatures & train_signatures)

        if not selected:
            failures.append(f"{condition}: no held-out test rows")
        if condition_seeds != set(CANONICAL_SEEDS):
            failures.append(
                f"{condition}: missing canonical seed coverage; observed={sorted(condition_seeds)}"
            )
        if any(signature_field not in row or not str(row.get(signature_field, "")) for row in selected):
            failures.append(f"{condition}: missing {signature_field}")
        if overlap:
            failures.append(
                f"{condition}: train/test signature leakage ({len(overlap)} overlaps)"
            )

        cells[condition] = {
            "rows": len(selected),
            "seeds": sorted(condition_seeds),
            "unique_signatures": len(signatures),
            "train_overlap_count": len(overlap),
            "overlap_examples": overlap[:10],
        }

    # Explicitly reject the current placeholder annotation pattern.
    if test and all(not bool(row.get("entity_holdout", False)) for row in test):
        failures.append("placeholder entity_holdout=False for every test row")
    if test and all(not bool(row.get("dynamics_holdout", False)) for row in test):
        failures.append("placeholder dynamics_holdout=False for every test row")
    if test and all(bool(row.get("language_holdout", False)) for row in test):
        failures.append("test split cannot be relabeled wholesale as language-form holdout")

    status = "pass" if not failures else "initial_reproduction_failure"
    return {
        "status": status,
        "dataset": str(path),
        "dataset_sha256": dataset_sha256(path),
        "rows": len(rows),
        "canonical_seeds": list(CANONICAL_SEEDS),
        "cells": cells,
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = audit(load_jsonl(args.data), args.data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
