#!/usr/bin/env python3
"""Fail-closed entity/dynamics holdout audit at domain/split/condition granularity.

The main evaluation contract historically aggregated signatures by split.  A test
split containing both in-distribution and held-out instances could therefore
produce either a false failure or conceal which condition leaked.  This audit
compares every declared holdout cell only with training signatures from the same
domain, while permitting expected overlap in explicitly in-distribution cells.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

CANONICAL_SEEDS = {1, 7, 19}
EVAL_SPLITS = {"test", "eval", "validation", "valid"}
HOLDOUT_KINDS = ("entity", "dynamics")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: each row must be an object")
            rows.append(value)
    return rows


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _truthy(row: dict[str, Any], key: str) -> bool:
    value = row.get(key)
    return value is True or value == 1 or str(value).lower() == "true"


def _condition(row: dict[str, Any]) -> str:
    if row.get("condition") is not None:
        return str(row["condition"])
    flags = [f"{kind}_holdout" for kind in HOLDOUT_KINDS if _truthy(row, f"{kind}_holdout")]
    if _truthy(row, "language_holdout"):
        flags.append("language_holdout")
    return "+".join(sorted(flags)) if flags else "in_distribution"


def _signature(row: dict[str, Any], kind: str) -> str | None:
    for key in (f"{kind}_id", f"{kind}_signature"):
        if row.get(key) is not None:
            return stable_hash(row[key])
    return None


def audit(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    train: dict[tuple[str, str], set[str]] = defaultdict(set)
    eval_cells: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    materialized = [dict(row) for row in rows]
    for index, row in enumerate(materialized, 1):
        try:
            domain = str(row["domain"])
            split = str(row["split"]).lower()
            seed = int(row["seed"])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"row {index}: invalid domain/split/seed: {exc}")
            continue
        condition = _condition(row)
        if split == "train":
            for kind in HOLDOUT_KINDS:
                signature = _signature(row, kind)
                if signature is not None:
                    train[(domain, kind)].add(signature)
            continue
        if split not in EVAL_SPLITS:
            warnings.append(f"row {index}: ignored non-train/non-eval split {split!r}")
            continue
        for kind in HOLDOUT_KINDS:
            declared = f"{kind}_holdout" in condition or _truthy(row, f"{kind}_holdout")
            if not declared:
                continue
            key = (domain, split, condition, kind)
            cell = eval_cells.setdefault(key, {"seeds": set(), "signatures": set(), "missing": []})
            cell["seeds"].add(seed)
            signature = _signature(row, kind)
            if signature is None:
                cell["missing"].append(str(row.get("instance_id", index)))
            else:
                cell["signatures"].add(signature)

    cell_results: list[dict[str, Any]] = []
    if not eval_cells:
        errors.append("no declared entity/dynamics holdout cells found")
    for (domain, split, condition, kind), cell in sorted(eval_cells.items()):
        train_values = train.get((domain, kind), set())
        eval_values = cell["signatures"]
        shared = sorted(train_values & eval_values)
        missing_seeds = sorted(CANONICAL_SEEDS - cell["seeds"])
        extra_seeds = sorted(cell["seeds"] - CANONICAL_SEEDS)
        if not train_values:
            errors.append(f"{kind} holdout cell {(domain, split, condition)} has no training signatures for comparison")
        if cell["missing"]:
            errors.append(
                f"{kind} holdout cell {(domain, split, condition)} has rows without {kind} signature: "
                f"{cell['missing'][:10]}"
            )
        if shared:
            errors.append(
                f"{kind} holdout violation in {(domain, split, condition)}: "
                f"{len(shared)} signatures overlap training"
            )
        if missing_seeds or extra_seeds:
            errors.append(
                f"{kind} holdout cell {(domain, split, condition)} has seeds={sorted(cell['seeds'])}; "
                f"missing={missing_seeds}, extra={extra_seeds}"
            )
        cell_results.append({
            "domain": domain,
            "split": split,
            "condition": condition,
            "kind": kind,
            "train_unique": len(train_values),
            "eval_unique": len(eval_values),
            "overlap_count": len(shared),
            "overlap_signature_hash_examples": shared[:5],
            "missing_signature_rows": cell["missing"][:10],
            "seeds": sorted(cell["seeds"]),
            "missing_seeds": missing_seeds,
            "extra_seeds": extra_seeds,
            "complete": bool(train_values) and not shared and not cell["missing"] and not missing_seeds and not extra_seeds,
        })

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": sorted(set(warnings)),
        "classification": "qualified_holdout_condition_integrity" if not errors else "initial_reproduction_failure",
        "cells": cell_results,
        "cell_count": len(cell_results),
        "canonical_seeds": sorted(CANONICAL_SEEDS),
        "condition_scoped_comparison": True,
        "in_distribution_overlap_is_not_misclassified": True,
        "dataset_sha256": stable_hash(materialized),
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
