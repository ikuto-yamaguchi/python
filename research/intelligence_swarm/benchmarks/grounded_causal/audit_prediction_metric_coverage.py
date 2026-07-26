#!/usr/bin/env python3
"""Fail closed when R0 methods expose different metric payloads or selective coverage.

This audit is intentionally separate from model quality.  It verifies that every
registered method predicts the same preregistered outputs on the same evaluation
instances before cell means, confidence intervals, or paired tests are accepted.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

CANONICAL_SEEDS = {1, 7, 19}
EVAL_SPLITS = {"test", "eval", "validation", "valid"}
REQUIRED_METHODS = {
    "correct",
    "random",
    "language_blind",
    "state_only",
    "target_label_shuffle",
    "outcome_shuffle",
}
BASE_PREDICTION_FIELDS = {"pred_action", "pred_state_after"}
OPTIONAL_METRICS = {"inverse": ("gold_inverse", "pred_inverse")}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: each row must be an object")
            rows.append(value)
    return rows


def audit(dataset: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    eval_ids: set[str] = set()
    eval_cells: dict[str, tuple[int, str, str, str]] = {}

    for index, row in enumerate(dataset, 1):
        instance_id = str(row.get("instance_id", ""))
        if not instance_id:
            errors.append(f"dataset row {index}: instance_id is required")
            continue
        if instance_id in by_id:
            errors.append(f"dataset row {index}: duplicate instance_id={instance_id}")
        by_id[instance_id] = row
        split = str(row.get("split", "")).lower()
        if split == "train":
            continue
        if split not in EVAL_SPLITS:
            errors.append(f"dataset row {index}: unregistered evaluation split={split!r}")
            continue
        try:
            seed = int(row["seed"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"dataset row {index}: seed must be integer-like")
            continue
        if seed not in CANONICAL_SEEDS:
            errors.append(f"dataset row {index}: noncanonical seed={seed}")
        domain = str(row.get("domain", ""))
        condition = str(row.get("condition", ""))
        if not domain or not condition:
            errors.append(f"dataset row {index}: domain and condition are required")
        eval_ids.add(instance_id)
        eval_cells[instance_id] = (seed, domain, split, condition)

    pred_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    method_ids: dict[str, set[str]] = defaultdict(set)
    for index, row in enumerate(predictions, 1):
        instance_id = str(row.get("instance_id", ""))
        method = str(row.get("method", ""))
        if method not in REQUIRED_METHODS:
            errors.append(f"prediction row {index}: unregistered method={method!r}")
        if instance_id not in eval_ids:
            errors.append(f"prediction row {index}: instance is outside registered evaluation set: {instance_id!r}")
        key = (instance_id, method)
        if key in pred_by_key:
            errors.append(f"prediction row {index}: duplicate instance/method={key}")
        pred_by_key[key] = row
        method_ids[method].add(instance_id)
        missing_base = BASE_PREDICTION_FIELDS - row.keys()
        if missing_base:
            errors.append(f"prediction row {index}: missing base prediction fields {sorted(missing_base)}")

    coverage: dict[str, Any] = {}
    for method in sorted(REQUIRED_METHODS):
        ids = method_ids.get(method, set())
        missing = sorted(eval_ids - ids)
        extra = sorted(ids - eval_ids)
        coverage[method] = {
            "expected": len(eval_ids),
            "predicted": len(ids & eval_ids),
            "missing": len(missing),
            "extra": len(extra),
            "missing_examples": missing[:5],
            "extra_examples": extra[:5],
        }
        if missing:
            errors.append(f"method {method}: incomplete instance coverage ({len(missing)} missing)")
        if extra:
            errors.append(f"method {method}: predictions outside evaluation set ({len(extra)} extra)")

    metric_contract: dict[str, Any] = {}
    for metric, (gold_field, pred_field) in OPTIONAL_METRICS.items():
        gold_present = {instance_id for instance_id in eval_ids if gold_field in by_id[instance_id]}
        if gold_present and gold_present != eval_ids:
            errors.append(
                f"metric {metric}: gold field {gold_field} is present on only "
                f"{len(gold_present)}/{len(eval_ids)} evaluation instances"
            )
        required = gold_present == eval_ids and bool(eval_ids)
        missing_by_method: dict[str, int] = {}
        unexpected_by_method: dict[str, int] = {}
        for method in sorted(REQUIRED_METHODS):
            missing = [iid for iid in eval_ids if pred_field not in pred_by_key.get((iid, method), {})]
            unexpected = [
                iid for iid in eval_ids
                if pred_field in pred_by_key.get((iid, method), {}) and iid not in gold_present
            ]
            missing_by_method[method] = len(missing)
            unexpected_by_method[method] = len(unexpected)
            if required and missing:
                errors.append(f"metric {metric}: method {method} omits {pred_field} on {len(missing)} instances")
            if unexpected:
                errors.append(f"metric {metric}: method {method} supplies {pred_field} without {gold_field} on {len(unexpected)} instances")
        metric_contract[metric] = {
            "gold_field": gold_field,
            "prediction_field": pred_field,
            "required": required,
            "gold_coverage": len(gold_present),
            "expected_instances": len(eval_ids),
            "missing_by_method": missing_by_method,
            "unexpected_by_method": unexpected_by_method,
        }

    cell_method_counts: dict[tuple[int, str, str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for (instance_id, method), row in pred_by_key.items():
        if instance_id in eval_cells and method in REQUIRED_METHODS:
            cell_method_counts[eval_cells[instance_id]][method] += 1
    cell_audit: list[dict[str, Any]] = []
    for cell, counts in sorted(cell_method_counts.items()):
        values = {method: counts.get(method, 0) for method in sorted(REQUIRED_METHODS)}
        if len(set(values.values())) != 1:
            errors.append(f"cell {cell}: methods have unequal prediction counts {values}")
        cell_audit.append({"seed": cell[0], "domain": cell[1], "split": cell[2], "condition": cell[3], "method_counts": values})

    return {
        "valid": not errors,
        "classification": "qualified" if not errors else "initial_reproduction_failure",
        "errors": errors,
        "evaluation_instances": len(eval_ids),
        "methods": sorted(method_ids),
        "coverage": coverage,
        "metric_contract": metric_contract,
        "cells": cell_audit,
        "same_instance_metric_coverage_required": True,
        "selective_metric_reporting_forbidden": True,
        "canonical_seeds": sorted(CANONICAL_SEEDS),
        "registered_eval_splits": sorted(EVAL_SPLITS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("predictions", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit(read_jsonl(args.dataset), read_jsonl(args.predictions))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"valid": False, "classification": "initial_reproduction_failure", "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
