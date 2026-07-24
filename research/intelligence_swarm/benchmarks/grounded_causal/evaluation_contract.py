#!/usr/bin/env python3
"""Reproducibility, leakage and paired-statistics contract for grounded benchmarks.

Accepts the canonical schema and the trajectory schema produced by
``export_silg_trajectories.py``. It is model agnostic and uses only the Python
standard library.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

CANONICAL_REQUIRED = {
    "instance_id", "domain", "seed", "split", "condition", "utterance",
    "state_before", "gold_action", "gold_state_after",
}
PRED_REQUIRED = {"instance_id", "method", "pred_action", "pred_state_after"}
FORBIDDEN_MODEL_INPUT_FIELDS = {
    "gold_action", "gold_state_after", "gold_inverse", "answer", "label",
    "completed_trajectory", "post_treatment_state", "state_after", "action",
    "reward", "done", "terminal_observation",
}
GOLD_LIKE_KEYS = {
    "gold_action", "gold_state_after", "gold_inverse", "answer", "label",
    "state_after", "action", "reward", "done", "completed_trajectory",
    "post_treatment_state", "terminal_observation",
}
REQUIRED_CONTROL_METHODS = {
    "random", "language_blind", "state_only", "target_label_shuffle",
    "outcome_shuffle",
}
HELD_OUT_CONDITIONS = {
    "entity_holdout", "dynamics_holdout", "language_holdout",
}
RESOURCE_FIELDS = {
    "model_bytes", "peak_rss_bytes", "training_wall_seconds",
    "cpu_inference_ms_per_item", "raw_log_sha256", "model_sha256",
    "data_sha256", "code_commit",
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


def read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return obj


def canonical_text(text: str) -> str:
    return "".join(str(text).split()).casefold()


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _truthy(row: dict[str, Any], key: str) -> bool:
    value = row.get(key, False)
    return value is True or value == 1 or str(value).lower() == "true"


def adapt_row(row: dict[str, Any]) -> dict[str, Any]:
    """Adapt SILG trajectory export rows to the canonical evaluation schema."""
    out = dict(row)
    if "gold_action" not in out and "action" in out:
        out["gold_action"] = out["action"]
    if "gold_state_after" not in out and "state_after" in out:
        out["gold_state_after"] = out["state_after"]
    if "condition" not in out:
        flags = [k for k in HELD_OUT_CONDITIONS if _truthy(out, k)]
        out["condition"] = "+".join(sorted(flags)) if flags else "in_distribution"
    if "model_input_fields" not in out:
        out["model_input_fields"] = [
            key for key in ("utterance", "state_before", "history", "valid_action_mask")
            if key in out
        ]
    return out


def adapt_dataset(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [adapt_row(row) for row in rows]


def _find_forbidden_nested(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if str(key) in GOLD_LIKE_KEYS:
                found.append(path)
            found.extend(_find_forbidden_nested(child, path))
    elif isinstance(value, list):
        for idx, child in enumerate(value[:10]):
            found.extend(_find_forbidden_nested(child, f"{prefix}[{idx}]"))
    return found


def _split_signature(row: dict[str, Any], key: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    return stable_hash(value)


def validate_dataset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = adapt_dataset(rows)
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    split_texts: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    split_entities: dict[str, set[str]] = defaultdict(set)
    split_dynamics: dict[str, set[str]] = defaultdict(set)
    domains: set[str] = set()
    seeds: set[int] = set()
    conditions: set[str] = set()
    split_counts: Counter[str] = Counter()
    leakage_rows = 0

    for idx, row in enumerate(rows, 1):
        missing = CANONICAL_REQUIRED - row.keys()
        if missing:
            errors.append(f"row {idx}: missing fields {sorted(missing)}")
            continue
        iid = str(row["instance_id"])
        if iid in seen_ids:
            errors.append(f"row {idx}: duplicate instance_id={iid}")
        seen_ids.add(iid)
        domain = str(row["domain"])
        domains.add(domain)
        try:
            seed = int(row["seed"])
            seeds.add(seed)
        except (TypeError, ValueError):
            errors.append(f"row {idx}: seed must be integer-like")
            continue
        split = str(row["split"]).lower()
        split_counts[split] += 1
        condition = str(row["condition"])
        conditions.add(condition)
        text = canonical_text(str(row["utterance"]))
        if not text:
            warnings.append(f"row {idx}: empty utterance")
        split_texts[split][text].append(iid)

        declared_inputs = {str(x) for x in row.get("model_input_fields", [])}
        leaked = declared_inputs & FORBIDDEN_MODEL_INPUT_FIELDS
        if leaked:
            leakage_rows += 1
            errors.append(f"row {idx}: forbidden model input fields {sorted(leaked)}")
        if "model_input" in row:
            nested = _find_forbidden_nested(row["model_input"])
            if nested:
                leakage_rows += 1
                errors.append(f"row {idx}: forbidden keys inside model_input {sorted(set(nested))}")

        for source_key, target in (
            ("entity_id", split_entities),
            ("entity_signature", split_entities),
            ("dynamics_id", split_dynamics),
            ("dynamics_signature", split_dynamics),
        ):
            sig = _split_signature(row, source_key)
            if sig:
                target[split].add(sig)

        if split != "train":
            if _truthy(row, "entity_holdout") and not (
                row.get("entity_id") is not None or row.get("entity_signature") is not None
            ):
                warnings.append(f"row {idx}: entity_holdout lacks entity identity/signature")
            if _truthy(row, "dynamics_holdout") and not (
                row.get("dynamics_id") is not None or row.get("dynamics_signature") is not None
            ):
                warnings.append(f"row {idx}: dynamics_holdout lacks dynamics identity/signature")

    train_texts = set(split_texts.get("train", {}))
    overlap_report: dict[str, Any] = {}
    for split, by_text in split_texts.items():
        if split == "train":
            continue
        overlap = train_texts & set(by_text)
        overlap_report[split] = {"count": len(overlap), "examples": sorted(overlap)[:5]}
        if overlap:
            errors.append(
                f"exact normalized utterance leakage train->{split}: "
                f"{len(overlap)} texts; examples={sorted(overlap)[:5]}"
            )

    holdout_report: dict[str, Any] = {}
    for name, values in (("entity", split_entities), ("dynamics", split_dynamics)):
        train_values = values.get("train", set())
        for split, test_values in values.items():
            if split == "train":
                continue
            overlap = train_values & test_values
            holdout_report[f"{name}:train->{split}"] = {
                "train_unique": len(train_values),
                "eval_unique": len(test_values),
                "overlap": len(overlap),
            }
            flagged = any(
                str(row["split"]).lower() == split and _truthy(row, f"{name}_holdout")
                for row in rows
            )
            if flagged and overlap:
                errors.append(
                    f"{name} holdout violation train->{split}: {len(overlap)} shared signatures"
                )

    if len(seeds) < 3:
        errors.append(f"need >=3 seeds, found {sorted(seeds)}")
    if len(domains) < 1:
        errors.append("need >=1 domain")
    if "train" not in split_counts:
        errors.append("train split is missing")
    if not ({"test", "eval", "validation", "valid"} & set(split_counts)):
        errors.append("evaluation split is missing")

    missing_holdout = {
        c for c in HELD_OUT_CONDITIONS
        if not any(c in condition for condition in conditions)
    }
    if missing_holdout:
        warnings.append(f"missing held-out conditions: {sorted(missing_holdout)}")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": sorted(set(warnings)),
        "instances": len(rows),
        "domains": sorted(domains),
        "seeds": sorted(seeds),
        "conditions": sorted(conditions),
        "split_counts": dict(sorted(split_counts.items())),
        "utterance_overlap": overlap_report,
        "holdout_integrity": holdout_report,
        "leakage_rows": leakage_rows,
        "dataset_sha256": stable_hash(rows),
        "adapted_schema": True,
    }


def exact_equal(a: Any, b: Any) -> float:
    return 1.0 if a == b else 0.0


def _mean_ci(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return math.nan, math.nan, math.nan
    mean = statistics.mean(values)
    if len(values) == 1:
        return mean, mean, mean
    se = statistics.stdev(values) / math.sqrt(len(values))
    z = 1.959963984540054
    return mean, mean - z * se, mean + z * se


def _paired_permutation_pvalue(diffs: list[float], trials: int = 20000, seed: int = 20260724) -> float:
    """Two-sided paired randomization test over non-zero cell differences."""
    nonzero = [x for x in diffs if x != 0]
    if not nonzero:
        return 1.0
    observed = abs(statistics.mean(nonzero))
    n = len(nonzero)
    if n <= 18:
        extreme = 0
        total = 1 << n
        for mask in range(total):
            value = statistics.mean(
                x if (mask >> i) & 1 else -x for i, x in enumerate(nonzero)
            )
            extreme += abs(value) >= observed - 1e-15
        return extreme / total
    rng = random.Random(seed)
    extreme = 0
    for _ in range(trials):
        value = statistics.mean(x if rng.random() < 0.5 else -x for x in nonzero)
        extreme += abs(value) >= observed - 1e-15
    return (extreme + 1) / (trials + 1)


def score(data: list[dict[str, Any]], preds: list[dict[str, Any]]) -> dict[str, Any]:
    data = adapt_dataset(data)
    by_id = {str(r["instance_id"]): r for r in data}
    eval_ids = {
        str(r["instance_id"]) for r in data
        if str(r["split"]).lower() != "train"
    }
    grouped: dict[tuple[str, int, str, str], list[dict[str, float]]] = defaultdict(list)
    errors: list[str] = []
    duplicate_keys: set[tuple[str, str]] = set()
    method_ids: dict[str, set[str]] = defaultdict(set)

    for idx, pred in enumerate(preds, 1):
        missing = PRED_REQUIRED - pred.keys()
        if missing:
            errors.append(f"prediction row {idx}: missing {sorted(missing)}")
            continue
        iid = str(pred["instance_id"])
        method = str(pred["method"])
        pair = (iid, method)
        if pair in duplicate_keys:
            errors.append(f"prediction row {idx}: duplicate instance/method={pair}")
            continue
        duplicate_keys.add(pair)
        gold = by_id.get(iid)
        if gold is None:
            errors.append(f"prediction row {idx}: unknown instance_id={iid}")
            continue
        if str(gold["split"]).lower() == "train":
            errors.append(f"prediction row {idx}: prediction supplied for train instance={iid}")
            continue
        method_ids[method].add(iid)
        key = (method, int(gold["seed"]), str(gold["domain"]), str(gold["condition"]))
        item = {
            "prospective": exact_equal(pred["pred_state_after"], gold["gold_state_after"]),
            "action": exact_equal(pred["pred_action"], gold["gold_action"]),
        }
        if "gold_inverse" in gold and "pred_inverse" in pred:
            item["inverse"] = exact_equal(pred["pred_inverse"], gold["gold_inverse"])
        grouped[key].append(item)

    coverage: dict[str, Any] = {}
    for method, ids in sorted(method_ids.items()):
        missing = eval_ids - ids
        extra = ids - eval_ids
        ratio = len(ids & eval_ids) / max(1, len(eval_ids))
        coverage[method] = {
            "expected": len(eval_ids), "predicted": len(ids & eval_ids),
            "coverage": ratio, "missing": len(missing), "extra": len(extra),
            "missing_examples": sorted(missing)[:5],
        }
        if missing:
            errors.append(f"method {method}: incomplete prediction coverage {ratio:.6f}")

    methods = set(method_ids)
    absent_controls = REQUIRED_CONTROL_METHODS - methods
    if absent_controls:
        errors.append(f"missing required control methods: {sorted(absent_controls)}")
    if "correct" not in methods:
        errors.append("missing method='correct'")

    cells: list[dict[str, Any]] = []
    for (method, seed, domain, condition), items in sorted(grouped.items()):
        metrics = sorted({m for item in items for m in item})
        cell: dict[str, Any] = {
            "method": method, "seed": seed, "domain": domain,
            "condition": condition, "n": len(items),
        }
        for metric in metrics:
            vals = [item[metric] for item in items if metric in item]
            cell[metric] = statistics.mean(vals)
        cells.append(cell)

    summary: dict[str, dict[str, float]] = defaultdict(dict)
    metric_names = sorted({k for c in cells for k in c if k in {"prospective", "action", "inverse"}})
    for method in sorted(methods):
        method_cells = [c for c in cells if c["method"] == method]
        for metric in metric_names:
            values = [float(c[metric]) for c in method_cells if metric in c]
            if values:
                mean, lo, hi = _mean_ci(values)
                summary[method][metric] = mean
                summary[method][f"{metric}_cell_ci95_low"] = lo
                summary[method][f"{metric}_cell_ci95_high"] = hi

    gaps: dict[str, dict[str, Any]] = {}
    correct_cells = {
        (c["seed"], c["domain"], c["condition"]): c
        for c in cells if c["method"] == "correct"
    }
    for control in sorted(methods - {"correct"}):
        ctrl_cells = {
            (c["seed"], c["domain"], c["condition"]): c
            for c in cells if c["method"] == control
        }
        gaps[control] = {}
        for metric in metric_names:
            paired = [
                float(correct_cells[k][metric]) - float(ctrl_cells[k][metric])
                for k in sorted(correct_cells.keys() & ctrl_cells.keys())
                if metric in correct_cells[k] and metric in ctrl_cells[k]
            ]
            if paired:
                mean, lo, hi = _mean_ci(paired)
                gaps[control][metric] = {
                    "paired_cells": len(paired),
                    "mean_gap": mean,
                    "min_cell_gap": min(paired),
                    "max_cell_gap": max(paired),
                    "positive_cell_fraction": sum(x > 0 for x in paired) / len(paired),
                    "ci95_low": lo,
                    "ci95_high": hi,
                    "paired_randomization_p_two_sided": _paired_permutation_pvalue(paired),
                    "passes_mean_gap_0_10": mean >= 0.10,
                    "passes_every_cell_positive": min(paired) > 0,
                }

    return {
        "valid": not errors,
        "errors": errors,
        "prediction_rows": len(preds),
        "expected_eval_instances": len(eval_ids),
        "coverage": coverage,
        "cells": cells,
        "summary": dict(summary),
        "paired_gaps_vs_correct": gaps,
        "progress_contract": {
            "required_mean_gap": 0.10,
            "requires_all_three_seeds": True,
            "requires_control_instance_identity": True,
            "requires_complete_prediction_coverage": True,
            "internal_metrics_do_not_count": True,
        },
    }


def audit_artifacts(manifest: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs:
        return {"valid": False, "errors": ["manifest.runs must be a non-empty list"], "checks": []}

    required_methods = {"correct"} | REQUIRED_CONTROL_METHODS
    seen_methods: set[str] = set()
    seen_cells: set[tuple[str, int, str, str]] = set()
    for idx, run in enumerate(runs, 1):
        if not isinstance(run, dict):
            errors.append(f"run {idx}: must be an object")
            continue
        missing = RESOURCE_FIELDS - run.keys()
        if missing:
            errors.append(f"run {idx}: missing resource/provenance fields {sorted(missing)}")
        try:
            method = str(run["method"])
            seed = int(run["seed"])
            domain = str(run["domain"])
            split = str(run["split"])
            seen_methods.add(method)
            cell = (method, seed, domain, split)
            if cell in seen_cells:
                errors.append(f"run {idx}: duplicate run cell {cell}")
            seen_cells.add(cell)
        except KeyError as exc:
            errors.append(f"run {idx}: missing indexing field {exc}")
            continue

        for numeric in ("model_bytes", "peak_rss_bytes", "training_wall_seconds", "cpu_inference_ms_per_item"):
            value = run.get(numeric)
            if not isinstance(value, (int, float)) or value < 0:
                errors.append(f"run {idx}: {numeric} must be a non-negative number")

        for path_key, hash_key in (
            ("raw_log_path", "raw_log_sha256"),
            ("model_path", "model_sha256"),
            ("data_path", "data_sha256"),
        ):
            raw_path = run.get(path_key)
            expected = run.get(hash_key)
            if raw_path is None:
                warnings.append(f"run {idx}: {path_key} absent; checksum cannot be independently verified")
                continue
            path = base_dir / str(raw_path)
            if not path.exists():
                errors.append(f"run {idx}: missing artifact {path}")
                continue
            actual = file_sha256(path)
            ok = actual == expected
            checks.append({"run": idx, "path": str(path), "expected": expected, "actual": actual, "ok": ok})
            if not ok:
                errors.append(f"run {idx}: checksum mismatch for {path_key}")

    missing_methods = required_methods - seen_methods
    if missing_methods:
        errors.append(f"manifest missing required methods {sorted(missing_methods)}")
    seed_values = {cell[1] for cell in seen_cells}
    if len(seed_values) < 3:
        errors.append(f"manifest needs >=3 seeds, found {sorted(seed_values)}")
    domain_values = {cell[2] for cell in seen_cells}
    if not domain_values:
        errors.append("manifest has no domains")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": sorted(set(warnings)),
        "checks": checks,
        "methods": sorted(seen_methods),
        "seeds": sorted(seed_values),
        "domains": sorted(domain_values),
        "runs": len(runs),
        "classification": "reproduced" if not errors else "initial_reproduction_failure",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("data", type=Path)

    p_score = sub.add_parser("score")
    p_score.add_argument("data", type=Path)
    p_score.add_argument("predictions", type=Path)

    p_audit = sub.add_parser("audit-artifacts")
    p_audit.add_argument("manifest", type=Path)
    p_audit.add_argument("--base-dir", type=Path, default=Path("."))

    args = parser.parse_args(argv)
    try:
        if args.command == "audit-artifacts":
            result = audit_artifacts(read_json(args.manifest), args.base_dir)
        else:
            data = read_jsonl(args.data)
            result = validate_dataset(data)
            if args.command == "score":
                result["scores"] = score(data, read_jsonl(args.predictions))
                result["valid"] = result["valid"] and result["scores"]["valid"]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
