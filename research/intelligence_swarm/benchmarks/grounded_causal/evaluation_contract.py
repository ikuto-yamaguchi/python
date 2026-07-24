#!/usr/bin/env python3
"""Evaluation contract for grounded causal language baselines.

This is deliberately model-agnostic. It validates split integrity and scores
external abilities per domain/seed/condition without using candidate counts or
internal representation metrics as progress evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

REQUIRED_DATA_FIELDS = {
    "instance_id", "domain", "seed", "split", "condition", "utterance",
    "state_before", "gold_action", "gold_state_after"
}
REQUIRED_PRED_FIELDS = {"instance_id", "method", "pred_action", "pred_state_after"}
HELD_OUT_CONDITIONS = {
    "rename", "unknown_order", "subject_omission", "multi_paragraph",
    "free_japanese", "domain_transfer", "counterfactual"
}
FORBIDDEN_MODEL_INPUT_FIELDS = {
    "gold_action", "gold_state_after", "gold_inverse", "answer", "label",
    "completed_trajectory", "post_treatment_state"
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{line_no}: each row must be an object")
            rows.append(obj)
    return rows


def canonical_text(text: str) -> str:
    return "".join(text.split()).lower()


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_dataset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    split_texts: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    domains: set[str] = set()
    seeds: set[int] = set()
    conditions: set[str] = set()

    for idx, row in enumerate(rows, 1):
        missing = REQUIRED_DATA_FIELDS - row.keys()
        if missing:
            errors.append(f"row {idx}: missing fields {sorted(missing)}")
            continue
        iid = str(row["instance_id"])
        if iid in seen_ids:
            errors.append(f"row {idx}: duplicate instance_id={iid}")
        seen_ids.add(iid)
        domains.add(str(row["domain"]))
        try:
            seeds.add(int(row["seed"]))
        except (TypeError, ValueError):
            errors.append(f"row {idx}: seed must be integer-like")
        split = str(row["split"])
        condition = str(row["condition"])
        conditions.add(condition)
        split_texts[split][canonical_text(str(row["utterance"]))].append(iid)

        declared_inputs = set(row.get("model_input_fields", ["utterance", "state_before"]))
        leaked = declared_inputs & FORBIDDEN_MODEL_INPUT_FIELDS
        if leaked:
            errors.append(f"row {idx}: forbidden model input fields {sorted(leaked)}")

    train_texts = set(split_texts.get("train", {}))
    for split, by_text in split_texts.items():
        if split == "train":
            continue
        overlap = train_texts & set(by_text)
        if overlap:
            examples = sorted(overlap)[:5]
            errors.append(
                f"exact normalized utterance leakage train->{split}: "
                f"{len(overlap)} texts; examples={examples}"
            )

    if len(seeds) < 3:
        errors.append(f"need >=3 seeds, found {sorted(seeds)}")
    if len(domains) < 2:
        errors.append(f"need >=2 domains, found {sorted(domains)}")
    missing_conditions = HELD_OUT_CONDITIONS - conditions
    if missing_conditions:
        warnings.append(f"missing held-out conditions: {sorted(missing_conditions)}")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "instances": len(rows),
        "domains": sorted(domains),
        "seeds": sorted(seeds),
        "conditions": sorted(conditions),
        "dataset_sha256": stable_hash(rows),
    }


def exact_equal(a: Any, b: Any) -> float:
    return 1.0 if a == b else 0.0


def score(data: list[dict[str, Any]], preds: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {str(r["instance_id"]): r for r in data}
    grouped: dict[tuple[str, int, str, str], list[dict[str, float]]] = defaultdict(list)
    errors: list[str] = []

    for idx, pred in enumerate(preds, 1):
        missing = REQUIRED_PRED_FIELDS - pred.keys()
        if missing:
            errors.append(f"prediction row {idx}: missing {sorted(missing)}")
            continue
        iid = str(pred["instance_id"])
        gold = by_id.get(iid)
        if gold is None:
            errors.append(f"prediction row {idx}: unknown instance_id={iid}")
            continue
        key = (
            str(pred["method"]),
            int(gold["seed"]),
            str(gold["domain"]),
            str(gold["condition"]),
        )
        item = {
            "prospective": exact_equal(pred["pred_state_after"], gold["gold_state_after"]),
            "action": exact_equal(pred["pred_action"], gold["gold_action"]),
        }
        if "gold_inverse" in gold and "pred_inverse" in pred:
            item["inverse"] = exact_equal(pred["pred_inverse"], gold["gold_inverse"])
        grouped[key].append(item)

    cells: list[dict[str, Any]] = []
    for (method, seed, domain, condition), items in sorted(grouped.items()):
        metrics = sorted({m for item in items for m in item})
        cell = {
            "method": method, "seed": seed, "domain": domain,
            "condition": condition, "n": len(items)
        }
        for metric in metrics:
            vals = [item[metric] for item in items if metric in item]
            cell[metric] = statistics.mean(vals)
        cells.append(cell)

    summary: dict[str, dict[str, float]] = defaultdict(dict)
    methods = sorted({c["method"] for c in cells})
    metrics = sorted({k for c in cells for k in c if k in {"prospective", "action", "inverse"}})
    for method in methods:
        method_cells = [c for c in cells if c["method"] == method]
        for metric in metrics:
            values = [float(c[metric]) for c in method_cells if metric in c]
            if values:
                summary[method][metric] = statistics.mean(values)

    gaps: dict[str, dict[str, float]] = {}
    correct_cells = {
        (c["seed"], c["domain"], c["condition"]): c
        for c in cells if c["method"] == "correct"
    }
    for control in [m for m in methods if m != "correct"]:
        ctrl_cells = {
            (c["seed"], c["domain"], c["condition"]): c
            for c in cells if c["method"] == control
        }
        gaps[control] = {}
        for metric in metrics:
            paired = [
                float(correct_cells[k][metric]) - float(ctrl_cells[k][metric])
                for k in correct_cells.keys() & ctrl_cells.keys()
                if metric in correct_cells[k] and metric in ctrl_cells[k]
            ]
            if paired:
                gaps[control][f"{metric}_mean_gap"] = statistics.mean(paired)
                gaps[control][f"{metric}_min_cell_gap"] = min(paired)
                gaps[control][f"{metric}_positive_cells"] = sum(x > 0 for x in paired) / len(paired)

    return {
        "valid": not errors,
        "errors": errors,
        "prediction_rows": len(preds),
        "cells": cells,
        "summary": dict(summary),
        "paired_gaps_vs_correct": gaps,
        "progress_contract": {
            "required_mean_gap": 0.10,
            "requires_all_three_seeds": True,
            "requires_two_domains": True,
            "internal_metrics_do_not_count": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_validate = sub.add_parser("validate")
    p_validate.add_argument("data", type=Path)
    p_score = sub.add_parser("score")
    p_score.add_argument("data", type=Path)
    p_score.add_argument("predictions", type=Path)
    args = parser.parse_args(argv)

    try:
        data = read_jsonl(args.data)
        result = validate_dataset(data)
        if args.command == "score" and result["valid"]:
            result["scores"] = score(data, read_jsonl(args.predictions))
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
