#!/usr/bin/env python3
"""Strict reproducibility, leakage and paired-statistics contract for grounded benchmarks.

Accepts canonical rows and SILG trajectory-export rows. Standard library only.
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

CANONICAL_REQUIRED = {"instance_id", "domain", "seed", "split", "condition", "utterance", "state_before", "gold_action", "gold_state_after"}
PRED_REQUIRED = {"instance_id", "method", "instance_fingerprint", "pred_action", "pred_state_after"}
REQUIRED_CONTROL_METHODS = {"random", "language_blind", "state_only", "target_label_shuffle", "outcome_shuffle"}
SHUFFLE_METHODS = {"target_label_shuffle", "outcome_shuffle"}
SHUFFLE_REQUIRED = {"control_source_instance_id", "control_source_fingerprint"}
HELD_OUT_CONDITIONS = {"entity_holdout", "dynamics_holdout", "language_holdout"}
FORBIDDEN_MODEL_INPUT_FIELDS = {"gold_action", "gold_state_after", "gold_inverse", "answer", "label", "completed_trajectory", "post_treatment_state", "state_after", "action", "reward", "done", "terminal_observation"}
GOLD_LIKE_KEYS = set(FORBIDDEN_MODEL_INPUT_FIELDS)
RESOURCE_FIELDS = {"model_bytes", "peak_rss_bytes", "training_wall_seconds", "cpu_inference_ms_per_item", "raw_log_sha256", "model_sha256", "data_sha256", "code_commit"}
ARTIFACT_FIELDS = (("raw_log_path", "raw_log_sha256"), ("model_path", "model_sha256"), ("data_path", "data_sha256"))
CANONICAL_SEEDS = {1, 7, 19}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{n}: each row must be an object")
            rows.append(obj)
    return rows


def read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return obj


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _is_hex(value: Any, n: int) -> bool:
    s = str(value)
    return len(s) == n and all(c in "0123456789abcdefABCDEF" for c in s)


def _finite_nonnegative(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and float(value) >= 0


def canonical_text(text: str) -> str:
    return "".join(str(text).split()).casefold()


def _truthy(row: dict[str, Any], key: str) -> bool:
    return row.get(key) is True or row.get(key) == 1 or str(row.get(key, False)).lower() == "true"


def adapt_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if "gold_action" not in out and "action" in out:
        out["gold_action"] = out["action"]
    if "gold_state_after" not in out and "state_after" in out:
        out["gold_state_after"] = out["state_after"]
    if "condition" not in out:
        flags = [k for k in HELD_OUT_CONDITIONS if _truthy(out, k)]
        out["condition"] = "+".join(sorted(flags)) if flags else "in_distribution"
    if "model_input_fields" not in out:
        out["model_input_fields"] = [k for k in ("utterance", "state_before", "history", "valid_action_mask") if k in out]
    return out


def adapt_dataset(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [adapt_row(r) for r in rows]


def _find_forbidden_nested(value: Any, prefix: str = "") -> list[str]:
    out = []
    if isinstance(value, dict):
        for key, nested in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if str(key) in GOLD_LIKE_KEYS:
                out.append(path)
            out.extend(_find_forbidden_nested(nested, path))
    elif isinstance(value, list):
        for i, nested in enumerate(value[:32]):
            out.extend(_find_forbidden_nested(nested, f"{prefix}[{i}]"))
    return out


def _split_sig(row: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        if row.get(key) is not None:
            return stable_hash(row[key])
    return None


def _cell_key(row: dict[str, Any]) -> tuple[int, str, str, str]:
    return (int(row["seed"]), str(row["domain"]), str(row["split"]).lower(), str(row["condition"]))


def instance_fingerprint(row: dict[str, Any]) -> str:
    payload = {k: row.get(k) for k in ("domain", "seed", "split", "condition", "utterance", "state_before", "history", "valid_action_mask", "entity_id", "entity_signature", "dynamics_id", "dynamics_signature")}
    return stable_hash(payload)


def validate_dataset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = adapt_dataset(rows)
    errors, warnings, seen = [], [], set()
    domains, seeds, conditions = set(), set(), set()
    splits, texts = Counter(), defaultdict(set)
    entities, dynamics = defaultdict(set), defaultdict(set)
    fingerprints, leakage = {}, 0
    for i, row in enumerate(rows, 1):
        missing = CANONICAL_REQUIRED - row.keys()
        if missing:
            errors.append(f"row {i}: missing fields {sorted(missing)}")
            continue
        iid = str(row["instance_id"])
        if iid in seen:
            errors.append(f"row {i}: duplicate instance_id={iid}")
        seen.add(iid)
        fingerprints[iid] = instance_fingerprint(row)
        domains.add(str(row["domain"]))
        conditions.add(str(row["condition"]))
        split = str(row["split"]).lower()
        splits[split] += 1
        try:
            seeds.add(int(row["seed"]))
        except Exception:
            errors.append(f"row {i}: seed must be integer-like")
        text = canonical_text(str(row["utterance"]))
        texts[split].add(text)
        if not text:
            warnings.append(f"row {i}: empty utterance")
        declared = {str(x) for x in row.get("model_input_fields", [])}
        bad = declared & FORBIDDEN_MODEL_INPUT_FIELDS
        if bad:
            leakage += 1
            errors.append(f"row {i}: forbidden model input fields {sorted(bad)}")
        nested = _find_forbidden_nested(row.get("model_input", {}))
        if nested:
            leakage += 1
            errors.append(f"row {i}: forbidden keys inside model_input {sorted(set(nested))}")
        if "completed_trajectory" in row and "completed_trajectory" in declared:
            leakage += 1
            errors.append(f"row {i}: completed trajectory exposed to model")
        entity_sig = _split_sig(row, "entity_id", "entity_signature")
        dynamics_sig = _split_sig(row, "dynamics_id", "dynamics_signature")
        if entity_sig:
            entities[split].add(entity_sig)
        if dynamics_sig:
            dynamics[split].add(dynamics_sig)
    overlap = {}
    train = texts.get("train", set())
    for split, values in texts.items():
        if split == "train":
            continue
        shared = train & values
        overlap[split] = {"count": len(shared), "examples": sorted(shared)[:5]}
        if shared:
            errors.append(f"exact normalized utterance leakage train->{split}: {len(shared)} texts")
    holdout = {}
    for name, mapping in (("entity", entities), ("dynamics", dynamics)):
        train_values = mapping.get("train", set())
        for split, values in mapping.items():
            if split == "train":
                continue
            shared = train_values & values
            holdout[f"{name}:train->{split}"] = {"train_unique": len(train_values), "eval_unique": len(values), "overlap": len(shared)}
            flagged = any(str(r.get("split", "")).lower() == split and _truthy(r, f"{name}_holdout") for r in rows)
            if flagged and shared:
                errors.append(f"{name} holdout violation train->{split}: {len(shared)} shared signatures")
    if len(seeds) < 3:
        errors.append(f"need >=3 seeds, found {sorted(seeds)}")
    if not domains:
        errors.append("need >=1 domain")
    if "train" not in splits:
        errors.append("train split is missing")
    if not ({"test", "eval", "validation", "valid"} & set(splits)):
        errors.append("evaluation split is missing")
    missing_holdouts = HELD_OUT_CONDITIONS - {c for condition in conditions for c in HELD_OUT_CONDITIONS if c in condition}
    if missing_holdouts:
        warnings.append(f"missing held-out conditions: {sorted(missing_holdouts)}")
    return {"valid": not errors, "errors": errors, "warnings": sorted(set(warnings)), "instances": len(rows), "domains": sorted(domains), "seeds": sorted(seeds), "conditions": sorted(conditions), "split_counts": dict(sorted(splits.items())), "utterance_overlap": overlap, "holdout_integrity": holdout, "leakage_rows": leakage, "dataset_sha256": stable_hash(rows), "instance_fingerprints_sha256": stable_hash(fingerprints), "adapted_schema": True}


def _mean_ci(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return math.nan, math.nan, math.nan
    mean = statistics.mean(values)
    if len(values) == 1:
        return mean, mean, mean
    se = statistics.stdev(values) / math.sqrt(len(values))
    z = 1.959963984540054
    return mean, mean - z * se, mean + z * se


def _paired_p(diffs: list[float], trials: int = 20000, seed: int = 20260724) -> float:
    xs = [x for x in diffs if x != 0]
    if not xs:
        return 1.0
    observed, n = abs(statistics.mean(xs)), len(xs)
    if n <= 18:
        values = [abs(statistics.mean(x if (mask >> i) & 1 else -x for i, x in enumerate(xs))) for mask in range(1 << n)]
        return sum(v >= observed - 1e-15 for v in values) / len(values)
    rng, extreme = random.Random(seed), 0
    for _ in range(trials):
        value = abs(statistics.mean(x if rng.random() < .5 else -x for x in xs))
        extreme += value >= observed - 1e-15
    return (extreme + 1) / (trials + 1)


def _mcnemar_exact(correct_only: int, control_only: int) -> float:
    n = correct_only + control_only
    if n == 0:
        return 1.0
    k = min(correct_only, control_only)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def _cluster_bootstrap_ci(instance_diffs: dict[tuple[int, str, str, str], list[float]], trials: int = 5000, seed: int = 20260724) -> tuple[float, float]:
    keys = sorted(instance_diffs)
    if not keys:
        return math.nan, math.nan
    rng, values = random.Random(seed), []
    for _ in range(trials):
        sampled = []
        for key in [keys[rng.randrange(len(keys))] for _ in keys]:
            xs = instance_diffs[key]
            sampled.extend(xs[rng.randrange(len(xs))] for _ in xs)
        values.append(statistics.mean(sampled))
    values.sort()
    return values[max(0, int(.025 * len(values)) - 1)], values[min(len(values) - 1, int(.975 * len(values)))]


def _validate_shuffle_assignments(preds: list[dict[str, Any]], by_id: dict[str, dict[str, Any]], eval_ids: set[str]) -> tuple[list[str], dict[str, Any]]:
    errors, audit = [], {}
    for method in sorted(SHUFFLE_METHODS):
        rows = [p for p in preds if str(p.get("method")) == method and str(p.get("instance_id")) in eval_ids]
        by_cell, donors_by_cell = defaultdict(list), defaultdict(list)
        for i, pred in enumerate(rows, 1):
            missing = SHUFFLE_REQUIRED - pred.keys()
            if missing:
                errors.append(f"{method} row {i}: missing shuffle provenance {sorted(missing)}")
                continue
            iid, donor_id = str(pred["instance_id"]), str(pred["control_source_instance_id"])
            target, donor = by_id[iid], by_id.get(donor_id)
            if donor is None or donor_id not in eval_ids:
                errors.append(f"{method} row {i}: unknown/non-eval donor {donor_id}")
                continue
            if donor_id == iid:
                errors.append(f"{method} row {i}: self-shuffle is not allowed for {iid}")
            if str(pred["control_source_fingerprint"]) != instance_fingerprint(donor):
                errors.append(f"{method} row {i}: donor fingerprint mismatch for {iid}<-{donor_id}")
            target_cell, donor_cell = _cell_key(target), _cell_key(donor)
            if target_cell != donor_cell:
                errors.append(f"{method} row {i}: donor crosses seed/domain/split/condition cell")
            by_cell[target_cell].append(iid)
            donors_by_cell[target_cell].append(donor_id)
        cell_audit = {}
        for cell in sorted(by_cell):
            targets, donors = by_cell[cell], donors_by_cell[cell]
            unique_donors = len(set(donors))
            bijective = len(targets) == unique_donors and set(targets) == set(donors)
            deranged = all(t != d for t, d in zip(targets, donors))
            if not bijective:
                errors.append(f"{method} cell {cell}: donor assignment is not a bijection")
            if not deranged:
                errors.append(f"{method} cell {cell}: donor assignment is not a derangement")
            cell_audit[str(cell)] = {"n": len(targets), "unique_donors": unique_donors, "bijective": bijective, "deranged": deranged}
        audit[method] = {"rows": len(rows), "cells": cell_audit, "provenance_required": True}
    return errors, audit


def score(data: list[dict[str, Any]], preds: list[dict[str, Any]]) -> dict[str, Any]:
    data = adapt_dataset(data)
    by_id = {str(r["instance_id"]): r for r in data}
    eval_ids = {iid for iid, row in by_id.items() if str(row["split"]).lower() != "train"}
    errors, seen = [], set()
    method_ids, grouped, snapshots, outcomes = defaultdict(set), defaultdict(list), defaultdict(set), defaultdict(dict)
    for i, pred in enumerate(preds, 1):
        missing = PRED_REQUIRED - pred.keys()
        if missing:
            errors.append(f"prediction row {i}: missing {sorted(missing)}")
            continue
        iid, method = str(pred["instance_id"]), str(pred["method"])
        key = (iid, method)
        if key in seen:
            errors.append(f"prediction row {i}: duplicate instance/method={key}")
            continue
        seen.add(key)
        gold = by_id.get(iid)
        if gold is None:
            errors.append(f"prediction row {i}: unknown instance_id={iid}")
            continue
        if str(gold["split"]).lower() == "train":
            errors.append(f"prediction row {i}: prediction supplied for train instance={iid}")
            continue
        expected_fp, supplied_fp = instance_fingerprint(gold), str(pred["instance_fingerprint"])
        if supplied_fp != expected_fp:
            errors.append(f"prediction row {i}: instance snapshot mismatch for {iid}/{method}")
        snapshots[iid].add(supplied_fp)
        method_ids[method].add(iid)
        item = {"prospective": float(pred["pred_state_after"] == gold["gold_state_after"]), "action": float(pred["pred_action"] == gold["gold_action"])}
        if "gold_inverse" in gold and "pred_inverse" in pred:
            item["inverse"] = float(pred["pred_inverse"] == gold["gold_inverse"])
        grouped[(method, int(gold["seed"]), str(gold["domain"]), str(gold["split"]).lower(), str(gold["condition"]))].append(item)
        outcomes[method][iid] = item
    for iid, fingerprints in snapshots.items():
        if len(fingerprints) != 1:
            errors.append(f"instance {iid}: methods used different input snapshots")
    coverage = {}
    for method, ids in sorted(method_ids.items()):
        missing = eval_ids - ids
        coverage[method] = {"expected": len(eval_ids), "predicted": len(ids & eval_ids), "coverage": len(ids & eval_ids) / max(1, len(eval_ids)), "missing": len(missing), "extra": len(ids - eval_ids), "missing_examples": sorted(missing)[:5]}
        if missing:
            errors.append(f"method {method}: incomplete prediction coverage")
    methods = set(method_ids)
    absent = REQUIRED_CONTROL_METHODS - methods
    if absent:
        errors.append(f"missing required control methods: {sorted(absent)}")
    if "correct" not in methods:
        errors.append("missing method='correct'")
    shuffle_errors, shuffle_audit = _validate_shuffle_assignments(preds, by_id, eval_ids)
    errors.extend(shuffle_errors)
    cells = []
    for (method, seed, domain, split, condition), items in sorted(grouped.items()):
        cell = {"method": method, "seed": seed, "domain": domain, "split": split, "condition": condition, "n": len(items)}
        for metric in sorted({k for item in items for k in item}):
            cell[metric] = statistics.mean(item[metric] for item in items if metric in item)
        cells.append(cell)
    metrics = sorted({k for cell in cells for k in cell if k in {"prospective", "action", "inverse"}})
    summary = defaultdict(dict)
    for method in methods:
        method_cells = [cell for cell in cells if cell["method"] == method]
        for metric in metrics:
            values = [float(cell[metric]) for cell in method_cells if metric in cell]
            if values:
                mean, low, high = _mean_ci(values)
                summary[method].update({metric: mean, f"{metric}_cell_ci95_low": low, f"{metric}_cell_ci95_high": high})
    correct_cells = {(cell["seed"], cell["domain"], cell["split"], cell["condition"]): cell for cell in cells if cell["method"] == "correct"}
    gaps = {}
    for control in sorted(methods - {"correct"}):
        control_cells = {(cell["seed"], cell["domain"], cell["split"], cell["condition"]): cell for cell in cells if cell["method"] == control}
        gaps[control] = {}
        shared_ids = sorted(eval_ids & method_ids.get("correct", set()) & method_ids.get(control, set()))
        for metric in metrics:
            diffs = [float(correct_cells[key][metric]) - float(control_cells[key][metric]) for key in sorted(correct_cells.keys() & control_cells.keys()) if metric in correct_cells[key] and metric in control_cells[key]]
            if not diffs:
                continue
            inst_by_cell, correct_only, control_only, ties = defaultdict(list), 0, 0, 0
            for iid in shared_ids:
                a, b = outcomes["correct"][iid].get(metric), outcomes[control][iid].get(metric)
                if a is None or b is None:
                    continue
                gold = by_id[iid]
                cell_key = (int(gold["seed"]), str(gold["domain"]), str(gold["split"]).lower(), str(gold["condition"]))
                inst_by_cell[cell_key].append(float(a - b))
                if a > b:
                    correct_only += 1
                elif b > a:
                    control_only += 1
                else:
                    ties += 1
            instance_values = [x for values in inst_by_cell.values() for x in values]
            bootstrap_low, bootstrap_high = _cluster_bootstrap_ci(inst_by_cell) if instance_values else (math.nan, math.nan)
            mean, low, high = _mean_ci(diffs)
            gaps[control][metric] = {"paired_cells": len(diffs), "mean_gap": mean, "min_cell_gap": min(diffs), "max_cell_gap": max(diffs), "positive_cell_fraction": sum(x > 0 for x in diffs) / len(diffs), "ci95_low": low, "ci95_high": high, "paired_randomization_p_two_sided": _paired_p(diffs), "paired_instances": len(instance_values), "instance_mean_gap": statistics.mean(instance_values) if instance_values else math.nan, "instance_cluster_bootstrap_ci95_low": bootstrap_low, "instance_cluster_bootstrap_ci95_high": bootstrap_high, "correct_only_instances": correct_only, "control_only_instances": control_only, "tied_instances": ties, "mcnemar_exact_p_two_sided": _mcnemar_exact(correct_only, control_only), "passes_mean_gap_0_10": mean >= .10, "passes_every_cell_positive": min(diffs) > 0, "passes_ci_excludes_zero": low > 0, "passes_instance_cluster_ci_excludes_zero": bootstrap_low > 0 if not math.isnan(bootstrap_low) else False}
    return {"valid": not errors, "errors": errors, "prediction_rows": len(preds), "expected_eval_instances": len(eval_ids), "coverage": coverage, "same_instance_snapshot": not any("snapshot" in error for error in errors), "fingerprints_required": True, "shuffle_assignment_audit": shuffle_audit, "cells": cells, "summary": dict(summary), "paired_gaps_vs_correct": gaps, "progress_contract": {"required_mean_gap": .10, "requires_all_three_seeds": True, "requires_same_instance_snapshot": True, "requires_explicit_instance_fingerprint": True, "requires_complete_prediction_coverage": True, "requires_shuffle_provenance": True, "requires_within_cell_derangement": True, "requires_split_condition_cells": True, "requires_ci_excludes_zero": True, "requires_instance_cluster_ci_excludes_zero": True, "internal_metrics_do_not_count": True}}


def audit_artifacts(manifest: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    errors, checks = [], []
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs:
        return {"valid": False, "errors": ["manifest.runs must be a non-empty list"], "checks": [], "classification": "initial_reproduction_failure"}
    methods, cells, seeds, domains, splits, conditions = set(), set(), set(), set(), set(), set()
    for i, run in enumerate(runs, 1):
        if not isinstance(run, dict):
            errors.append(f"run {i}: must be an object")
            continue
        missing = RESOURCE_FIELDS - run.keys()
        if missing:
            errors.append(f"run {i}: missing resource/provenance fields {sorted(missing)}")
        try:
            method, seed, domain, split, condition = str(run["method"]), int(run["seed"]), str(run["domain"]), str(run["split"]), str(run["condition"])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"run {i}: invalid indexing field {exc}")
            continue
        if not domain:
            errors.append(f"run {i}: domain must be non-empty")
        if not split:
            errors.append(f"run {i}: split must be non-empty")
        if not condition:
            errors.append(f"run {i}: condition must be non-empty")
        cell = (method, seed, domain, split, condition)
        if cell in cells:
            errors.append(f"run {i}: duplicate run cell {cell}")
        cells.add(cell)
        methods.add(method)
        seeds.add(seed)
        domains.add(domain)
        splits.add(split)
        conditions.add(condition)
        for key in ("model_bytes", "peak_rss_bytes", "training_wall_seconds", "cpu_inference_ms_per_item"):
            if not _finite_nonnegative(run.get(key)):
                errors.append(f"run {i}: {key} must be a finite non-negative number")
        if not _is_hex(run.get("code_commit"), 40):
            errors.append(f"run {i}: code_commit must be a full 40-hex commit SHA")
        for path_key, hash_key in ARTIFACT_FIELDS:
            relative_path, expected = run.get(path_key), run.get(hash_key)
            if not relative_path:
                errors.append(f"run {i}: {path_key} is required for independent checksum verification")
                continue
            if not _is_hex(expected, 64):
                errors.append(f"run {i}: {hash_key} must be a full 64-hex SHA-256")
                continue
            path = base_dir / str(relative_path)
            if not path.exists() or not path.is_file():
                errors.append(f"run {i}: missing artifact {path}")
                continue
            actual = file_sha256(path)
            ok = actual == str(expected).lower()
            checks.append({"run": i, "path": str(path), "expected": expected, "actual": actual, "ok": ok, "size_bytes": path.stat().st_size})
            if not ok:
                errors.append(f"run {i}: checksum mismatch for {path_key}")
            if path_key == "model_path" and _finite_nonnegative(run.get("model_bytes")) and int(run["model_bytes"]) != path.stat().st_size:
                errors.append(f"run {i}: model_bytes does not match model artifact size")
    required = {"correct"} | REQUIRED_CONTROL_METHODS
    missing_methods = required - methods
    if missing_methods:
        errors.append(f"manifest missing required methods {sorted(missing_methods)}")
    if seeds != CANONICAL_SEEDS:
        errors.append(f"manifest seeds must be exactly {sorted(CANONICAL_SEEDS)}, found {sorted(seeds)}")
    expected_cells = {(method, seed, domain, split, condition) for method in required for seed in CANONICAL_SEEDS for domain in domains for split in splits for condition in conditions}
    missing_cells = expected_cells - cells
    if missing_cells:
        errors.append(f"manifest incomplete Cartesian coverage: {len(missing_cells)} missing cells")
    return {"valid": not errors, "errors": errors, "warnings": [], "checks": checks, "methods": sorted(methods), "seeds": sorted(seeds), "domains": sorted(domains), "splits": sorted(splits), "conditions": sorted(conditions), "runs": len(runs), "missing_run_cells": len(missing_cells), "missing_run_cell_examples": [list(x) for x in sorted(missing_cells)[:10]], "independent_artifacts_required": True, "condition_index_required": True, "canonical_seeds": sorted(CANONICAL_SEEDS), "classification": "reproduced" if not errors else "initial_reproduction_failure"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("data", type=Path)
    score_parser = sub.add_parser("score")
    score_parser.add_argument("data", type=Path)
    score_parser.add_argument("predictions", type=Path)
    artifact_parser = sub.add_parser("audit-artifacts")
    artifact_parser.add_argument("manifest", type=Path)
    artifact_parser.add_argument("--base-dir", type=Path, default=Path("."))
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
