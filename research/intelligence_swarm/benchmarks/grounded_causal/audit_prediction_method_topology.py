#!/usr/bin/env python3
"""Fail-closed audit for exact R0 prediction-method topology.

`evaluation_contract.score` verifies coverage for required methods, but historical
bundles could still carry an unregistered extra method. This auditor requires the
exact six-method set on every evaluation instance and every
seed/domain/split/condition cell before accepting any statistics.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import evaluation_contract as ec

EXPECTED_METHODS = {"correct"} | ec.REQUIRED_CONTROL_METHODS


def audit(data: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    adapted = ec.adapt_dataset(data)
    by_id = {str(row.get("instance_id")): row for row in adapted if row.get("instance_id") is not None}
    eval_ids = {
        iid for iid, row in by_id.items()
        if str(row.get("split", "")).lower() != "train"
    }
    errors: list[str] = []
    by_instance: dict[str, set[str]] = defaultdict(set)
    by_cell: dict[tuple[int, str, str, str], dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    observed_methods: set[str] = set()

    for index, pred in enumerate(predictions, 1):
        iid = str(pred.get("instance_id", ""))
        method = str(pred.get("method", ""))
        if not iid or iid not in by_id:
            errors.append(f"prediction row {index}: unknown or empty instance_id={iid!r}")
            continue
        if iid not in eval_ids:
            errors.append(f"prediction row {index}: prediction supplied outside evaluation set: {iid}")
            continue
        if not method:
            errors.append(f"prediction row {index}: method must be non-empty")
            continue
        observed_methods.add(method)
        by_instance[iid].add(method)
        cell = ec._cell_key(by_id[iid])
        by_cell[cell][method].add(iid)

    extra_methods = observed_methods - EXPECTED_METHODS
    missing_methods = EXPECTED_METHODS - observed_methods
    if extra_methods:
        errors.append(f"unregistered prediction methods: {sorted(extra_methods)}")
    if missing_methods:
        errors.append(f"missing required prediction methods: {sorted(missing_methods)}")

    instance_audit: dict[str, Any] = {}
    for iid in sorted(eval_ids):
        methods = by_instance.get(iid, set())
        missing = EXPECTED_METHODS - methods
        extra = methods - EXPECTED_METHODS
        instance_audit[iid] = {
            "methods": sorted(methods),
            "missing": sorted(missing),
            "extra": sorted(extra),
        }
        if missing or extra:
            errors.append(
                f"instance {iid}: method topology mismatch; missing={sorted(missing)} extra={sorted(extra)}"
            )

    cell_audit: dict[str, Any] = {}
    for cell in sorted({ec._cell_key(by_id[iid]) for iid in eval_ids}):
        expected_ids = {iid for iid in eval_ids if ec._cell_key(by_id[iid]) == cell}
        method_map = by_cell.get(cell, {})
        cell_audit[str(cell)] = {}
        for method in sorted(EXPECTED_METHODS):
            ids = set(method_map.get(method, set()))
            missing = expected_ids - ids
            extra = ids - expected_ids
            cell_audit[str(cell)][method] = {
                "expected": len(expected_ids),
                "observed": len(ids),
                "missing": len(missing),
                "extra": len(extra),
            }
            if missing or extra:
                errors.append(
                    f"cell {cell}/{method}: prediction identity mismatch; "
                    f"missing={len(missing)} extra={len(extra)}"
                )

    dataset_result = ec.validate_dataset(data)
    score_result = ec.score(data, predictions)
    if not dataset_result.get("valid", False):
        errors.extend(f"dataset contract: {e}" for e in dataset_result.get("errors", []))
    if not score_result.get("valid", False):
        errors.extend(f"score contract: {e}" for e in score_result.get("errors", []))

    return {
        "valid": not errors,
        "classification": "reproduced" if not errors else "initial_reproduction_failure",
        "errors": errors,
        "expected_methods": sorted(EXPECTED_METHODS),
        "observed_methods": sorted(observed_methods),
        "evaluation_instances": len(eval_ids),
        "instance_method_topology": instance_audit,
        "cell_method_topology": cell_audit,
        "dataset_contract_valid": bool(dataset_result.get("valid", False)),
        "score_contract_valid": bool(score_result.get("valid", False)),
        "exact_method_set_required": True,
        "exact_method_set_per_instance_required": True,
        "exact_method_set_per_cell_required": True,
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return ec.read_jsonl(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = audit(read_jsonl(args.data), read_jsonl(args.predictions))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "valid": False,
            "classification": "initial_reproduction_failure",
            "errors": [str(exc)],
        }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
