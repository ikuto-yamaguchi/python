#!/usr/bin/env python3
"""Fail-closed seed/domain/split/condition coverage audit for R0 datasets.

This companion audit consumes the same canonical or SILG-export rows as
``evaluation_contract.py``.  It closes a gap between the dataset validator and
artifact manifest validator: merely observing three distinct seeds globally is
not sufficient when one domain/split/condition cell silently omits a seed.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from evaluation_contract import CANONICAL_SEEDS, EVAL_SPLITS, adapt_dataset, read_jsonl, stable_hash


def audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    adapted = adapt_dataset(rows)
    errors: list[str] = []
    warnings: list[str] = []
    eval_cell_seeds: dict[tuple[str, str, str], set[int]] = defaultdict(set)
    train_cell_seeds: dict[tuple[str, str], set[int]] = defaultdict(set)
    bad_seed_rows: list[str] = []

    for index, row in enumerate(adapted, 1):
        try:
            seed = int(row["seed"])
            domain = str(row["domain"])
            split = str(row["split"]).lower()
            condition = str(row["condition"])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"row {index}: invalid cell index: {exc}")
            continue
        if seed not in CANONICAL_SEEDS:
            bad_seed_rows.append(str(row.get("instance_id", index)))
        if split == "train":
            train_cell_seeds[(domain, split)].add(seed)
        elif split in EVAL_SPLITS:
            eval_cell_seeds[(domain, split, condition)].add(seed)

    if bad_seed_rows:
        errors.append(
            "dataset contains non-canonical seeds; expected exactly "
            f"{sorted(CANONICAL_SEEDS)}; examples={bad_seed_rows[:10]}"
        )
    if not eval_cell_seeds:
        errors.append("no evaluation domain/split/condition cells found")

    cell_audit: list[dict[str, Any]] = []
    for (domain, split, condition), seeds in sorted(eval_cell_seeds.items()):
        missing = sorted(CANONICAL_SEEDS - seeds)
        extra = sorted(seeds - CANONICAL_SEEDS)
        if missing or extra:
            errors.append(
                f"evaluation cell {(domain, split, condition)} has seeds={sorted(seeds)}; "
                f"missing={missing}, extra={extra}"
            )
        cell_audit.append({
            "domain": domain,
            "split": split,
            "condition": condition,
            "seeds": sorted(seeds),
            "missing_seeds": missing,
            "extra_seeds": extra,
            "complete": not missing and not extra,
        })

    train_audit: list[dict[str, Any]] = []
    for (domain, split), seeds in sorted(train_cell_seeds.items()):
        missing = sorted(CANONICAL_SEEDS - seeds)
        if missing:
            warnings.append(f"training cell {(domain, split)} is missing canonical seeds {missing}")
        train_audit.append({
            "domain": domain,
            "split": split,
            "seeds": sorted(seeds),
            "missing_seeds": missing,
        })

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "classification": "qualified_cell_coverage" if not errors else "initial_reproduction_failure",
        "canonical_seeds": sorted(CANONICAL_SEEDS),
        "evaluation_cells": cell_audit,
        "training_cells": train_audit,
        "evaluation_cell_count": len(cell_audit),
        "requires_exact_seed_set_per_eval_cell": True,
        "dataset_sha256": stable_hash(adapted),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit(read_jsonl(args.data))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "valid": False,
            "errors": [str(exc)],
            "classification": "initial_reproduction_failure",
        }
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
