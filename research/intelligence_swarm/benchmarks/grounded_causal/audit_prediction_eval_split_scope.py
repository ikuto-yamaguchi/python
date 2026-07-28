#!/usr/bin/env python3
"""Reject R0 prediction/statistics bundles that use unregistered split names."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

CANONICAL_SEEDS = {1, 7, 19}
TRAIN_SPLIT = "train"
EVAL_SPLITS = {"test", "eval", "validation", "valid"}
ALLOWED_SPLITS = {TRAIN_SPLIT} | EVAL_SPLITS
REQUIRED_METHODS = {
    "correct",
    "random",
    "language_blind",
    "state_only",
    "target_label_shuffle",
    "outcome_shuffle",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: row must be an object")
            rows.append(value)
    return rows


def audit(dataset: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    eval_ids: set[str] = set()
    observed_splits: set[str] = set()
    eval_topology: set[tuple[int, str, str, str]] = set()

    for index, row in enumerate(dataset, 1):
        iid = str(row.get("instance_id", ""))
        split = str(row.get("split", "")).strip().lower()
        if not iid:
            errors.append(f"dataset row {index}: instance_id is required")
            continue
        if iid in by_id:
            errors.append(f"dataset row {index}: duplicate instance_id={iid}")
            continue
        by_id[iid] = row
        observed_splits.add(split)
        if split not in ALLOWED_SPLITS:
            errors.append(f"dataset row {index}: unregistered split={split!r}")
            continue
        if split in EVAL_SPLITS:
            eval_ids.add(iid)
            try:
                cell = (int(row["seed"]), str(row["domain"]), split, str(row["condition"]))
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(f"dataset row {index}: invalid evaluation cell: {exc}")
                continue
            eval_topology.add(cell)

    prediction_ids: dict[str, set[str]] = defaultdict(set)
    prediction_cells: dict[str, set[tuple[int, str, str, str]]] = defaultdict(set)
    for index, row in enumerate(predictions, 1):
        iid = str(row.get("instance_id", ""))
        method = str(row.get("method", ""))
        if method not in REQUIRED_METHODS:
            errors.append(f"prediction row {index}: unregistered method={method!r}")
            continue
        source = by_id.get(iid)
        if source is None:
            errors.append(f"prediction row {index}: unknown instance_id={iid}")
            continue
        split = str(source.get("split", "")).strip().lower()
        if split not in EVAL_SPLITS:
            errors.append(f"prediction row {index}: instance {iid} belongs to non-evaluation split={split!r}")
            continue
        prediction_ids[method].add(iid)
        prediction_cells[method].add((int(source["seed"]), str(source["domain"]), split, str(source["condition"])))

    for method in sorted(REQUIRED_METHODS):
        missing = eval_ids - prediction_ids.get(method, set())
        extra = prediction_ids.get(method, set()) - eval_ids
        if missing:
            errors.append(f"method {method}: missing {len(missing)} registered evaluation instances")
        if extra:
            errors.append(f"method {method}: contains {len(extra)} non-evaluation instances")
        missing_cells = eval_topology - prediction_cells.get(method, set())
        if missing_cells:
            errors.append(f"method {method}: missing {len(missing_cells)} registered evaluation cells")

    seeds = {cell[0] for cell in eval_topology}
    if seeds != CANONICAL_SEEDS:
        errors.append(f"evaluation topology seeds must be exactly {sorted(CANONICAL_SEEDS)}, found {sorted(seeds)}")

    return {
        "valid": not errors,
        "classification": "qualified" if not errors else "initial_reproduction_failure",
        "errors": errors,
        "allowed_splits": sorted(ALLOWED_SPLITS),
        "observed_splits": sorted(observed_splits),
        "registered_eval_instances": len(eval_ids),
        "registered_eval_cells": [list(cell) for cell in sorted(eval_topology)],
        "prediction_coverage": {
            method: {
                "instances": len(prediction_ids.get(method, set())),
                "cells": len(prediction_cells.get(method, set())),
            }
            for method in sorted(REQUIRED_METHODS)
        },
        "fail_closed_unknown_split": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("predictions", type=Path)
    args = parser.parse_args()
    try:
        result = audit(read_jsonl(args.dataset), read_jsonl(args.predictions))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"valid": False, "classification": "initial_reproduction_failure", "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
