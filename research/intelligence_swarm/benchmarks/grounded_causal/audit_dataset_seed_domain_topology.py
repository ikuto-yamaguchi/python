#!/usr/bin/env python3
"""Fail-closed audit for canonical seed/domain/split/condition dataset topology.

This complements evaluation_contract.py by rejecting datasets that merely contain
three arbitrary seeds or silently omit one canonical seed from an evaluation cell.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

CANONICAL_SEEDS = {1, 7, 19}
EVAL_SPLITS = {"test", "eval", "validation", "valid"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{line_no}: row must be a JSON object")
            rows.append(obj)
    return rows


def audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    global_seeds: set[int] = set()
    topology: dict[tuple[str, str, str], set[int]] = defaultdict(set)
    seed_splits: dict[int, set[str]] = defaultdict(set)

    for index, row in enumerate(rows, 1):
        domain = str(row.get("domain", "")).strip()
        split = str(row.get("split", "")).strip().lower()
        condition = str(row.get("condition", "in_distribution")).strip()
        if not domain:
            errors.append(f"row {index}: empty/missing domain")
        if not split:
            errors.append(f"row {index}: empty/missing split")
        if not condition:
            errors.append(f"row {index}: empty condition")
        try:
            seed = int(row["seed"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"row {index}: seed must be integer-like")
            continue
        global_seeds.add(seed)
        seed_splits[seed].add(split)
        if domain and split and condition:
            topology[(domain, split, condition)].add(seed)

    if global_seeds != CANONICAL_SEEDS:
        errors.append(
            "dataset seeds must be exactly [1, 7, 19]; "
            f"found {sorted(global_seeds)}"
        )

    topology_audit: dict[str, Any] = {}
    for cell, seeds in sorted(topology.items()):
        domain, split, condition = cell
        missing = CANONICAL_SEEDS - seeds
        extra = seeds - CANONICAL_SEEDS
        topology_audit[f"{domain}|{split}|{condition}"] = {
            "seeds": sorted(seeds),
            "missing": sorted(missing),
            "extra": sorted(extra),
        }
        if split in EVAL_SPLITS and (missing or extra):
            errors.append(
                f"evaluation cell {cell} must contain exactly seeds [1, 7, 19]; "
                f"missing={sorted(missing)} extra={sorted(extra)}"
            )

    for seed in sorted(CANONICAL_SEEDS):
        splits = seed_splits.get(seed, set())
        if "train" not in splits:
            errors.append(f"seed {seed}: train split is missing")
        if not (splits & EVAL_SPLITS):
            errors.append(f"seed {seed}: evaluation split is missing")

    return {
        "valid": not errors,
        "classification": "qualified" if not errors else "initial_reproduction_failure",
        "errors": errors,
        "canonical_seeds": sorted(CANONICAL_SEEDS),
        "observed_seeds": sorted(global_seeds),
        "topology": topology_audit,
        "rows": len(rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(read_jsonl(args.dataset))
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
