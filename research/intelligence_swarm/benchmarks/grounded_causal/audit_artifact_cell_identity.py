#!/usr/bin/env python3
"""Fail-closed cross-method artifact identity audit for R0 benchmark bundles.

The evaluation contract already validates individual artifacts and prediction
coverage. This companion audit closes a separate provenance hole: every method
compared in one seed/domain/split/condition cell must use the exact same dataset
artifact, and the complete bundle must be produced by one immutable code commit.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

CANONICAL_SEEDS = {1, 7, 19}
REQUIRED_METHODS = {
    "correct",
    "random",
    "language_blind",
    "state_only",
    "target_label_shuffle",
    "outcome_shuffle",
}


def read_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("manifest top level must be an object")
    return value


def audit(manifest: dict[str, Any]) -> dict[str, Any]:
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs:
        return {
            "valid": False,
            "errors": ["manifest.runs must be a non-empty list"],
            "classification": "initial_reproduction_failure",
        }

    errors: list[str] = []
    by_cell: dict[tuple[int, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    commits: set[str] = set()
    methods: set[str] = set()
    seeds: set[int] = set()

    for index, run in enumerate(runs, 1):
        if not isinstance(run, dict):
            errors.append(f"run {index}: must be an object")
            continue
        missing = {
            "method",
            "seed",
            "domain",
            "split",
            "condition",
            "data_path",
            "data_sha256",
            "code_commit",
        } - run.keys()
        if missing:
            errors.append(f"run {index}: missing fields {sorted(missing)}")
            continue
        try:
            seed = int(run["seed"])
        except (TypeError, ValueError):
            errors.append(f"run {index}: seed must be integer-like")
            continue
        method = str(run["method"])
        domain = str(run["domain"])
        split = str(run["split"]).lower()
        condition = str(run["condition"])
        if not domain or not split or not condition:
            errors.append(f"run {index}: domain/split/condition must be non-empty")
            continue
        by_cell[(seed, domain, split, condition)].append(run)
        commits.add(str(run["code_commit"]))
        methods.add(method)
        seeds.add(seed)

    if seeds != CANONICAL_SEEDS:
        errors.append(
            f"bundle seeds must be exactly {sorted(CANONICAL_SEEDS)}, found {sorted(seeds)}"
        )
    if methods != REQUIRED_METHODS:
        errors.append(
            f"bundle methods must be exactly {sorted(REQUIRED_METHODS)}, found {sorted(methods)}"
        )
    if len(commits) != 1:
        errors.append(f"bundle must use exactly one code_commit, found {sorted(commits)}")

    cells: dict[str, Any] = {}
    expected_method_count = len(REQUIRED_METHODS)
    for cell, cell_runs in sorted(by_cell.items()):
        cell_methods = [str(run["method"]) for run in cell_runs]
        method_set = set(cell_methods)
        duplicate_methods = sorted(
            method for method in method_set if cell_methods.count(method) > 1
        )
        data_hashes = {str(run["data_sha256"]).lower() for run in cell_runs}
        data_paths = {str(run["data_path"]) for run in cell_runs}

        if len(cell_runs) != expected_method_count or method_set != REQUIRED_METHODS:
            errors.append(
                f"cell {cell}: methods must be exactly {sorted(REQUIRED_METHODS)}, "
                f"found {sorted(method_set)} across {len(cell_runs)} runs"
            )
        if duplicate_methods:
            errors.append(f"cell {cell}: duplicate methods {duplicate_methods}")
        if len(data_hashes) != 1:
            errors.append(
                f"cell {cell}: methods used different data_sha256 values {sorted(data_hashes)}"
            )
        if len(data_paths) != 1:
            errors.append(
                f"cell {cell}: methods used different data_path values {sorted(data_paths)}"
            )

        cells[str(cell)] = {
            "runs": len(cell_runs),
            "methods": sorted(method_set),
            "data_sha256_values": sorted(data_hashes),
            "data_path_values": sorted(data_paths),
            "matched_dataset": len(data_hashes) == 1 and len(data_paths) == 1,
        }

    return {
        "valid": not errors,
        "errors": errors,
        "classification": "reproduced" if not errors else "initial_reproduction_failure",
        "canonical_seeds": sorted(CANONICAL_SEEDS),
        "required_methods": sorted(REQUIRED_METHODS),
        "single_code_commit_required": True,
        "same_dataset_per_cell_required": True,
        "code_commits": sorted(commits),
        "cells": cells,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        result = audit(read_manifest(args.manifest))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "valid": False,
            "errors": [str(exc)],
            "classification": "initial_reproduction_failure",
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
