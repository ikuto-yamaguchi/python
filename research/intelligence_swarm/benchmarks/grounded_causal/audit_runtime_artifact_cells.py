#!/usr/bin/env python3
"""Fail-closed audit for R0 runtime/resource artifacts.

The audit binds every evaluated method/seed/domain/split/condition cell to an
immutable prediction file, dataset, checkpoint (except random), raw log, code
commit, and measured resource record.  It rejects copied aggregate resource
values, mixed checkpoints, missing canonical seeds, and checksum drift.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

CANONICAL_SEEDS = {1, 7, 19}
REQUIRED_METHODS = {
    "correct", "random", "language_blind", "state_only",
    "target_label_shuffle", "outcome_shuffle",
}
REQUIRED_FIELDS = {
    "method", "seed", "domain", "split", "condition",
    "prediction_path", "prediction_sha256", "data_path", "data_sha256",
    "raw_log_path", "raw_log_sha256", "code_commit",
    "peak_rss_bytes", "training_wall_seconds", "cpu_inference_ms_per_item",
}
MODEL_REQUIRED = {"model_path", "model_sha256", "model_bytes"}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _is_sha(value: Any, size: int = 64) -> bool:
    text = str(value)
    return len(text) == size and all(ch in "0123456789abcdefABCDEF" for ch in text)


def _finite_nonnegative(value: Any, *, positive: bool = False) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    number = float(value)
    return math.isfinite(number) and (number > 0 if positive else number >= 0)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
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


def _cell(row: dict[str, Any]) -> tuple[str, int, str, str, str]:
    return (
        str(row["method"]), int(row["seed"]), str(row["domain"]),
        str(row["split"]).lower(), str(row["condition"]),
    )


def audit(rows: list[dict[str, Any]], root: Path) -> dict[str, Any]:
    errors: list[str] = []
    seen: set[tuple[str, int, str, str, str]] = set()
    cells_by_method: dict[str, set[tuple[int, str, str, str]]] = defaultdict(set)
    dataset_by_eval_cell: dict[tuple[int, str, str, str], set[str]] = defaultdict(set)
    commit_by_method_seed: dict[tuple[str, int], set[str]] = defaultdict(set)
    model_by_method_seed: dict[tuple[str, int], set[str]] = defaultdict(set)
    resource_tuple_owners: dict[tuple[Any, ...], set[tuple[str, int]]] = defaultdict(set)
    verified_files = 0

    for index, row in enumerate(rows, 1):
        missing = REQUIRED_FIELDS - row.keys()
        method = str(row.get("method", ""))
        if method != "random":
            missing |= MODEL_REQUIRED - row.keys()
        if missing:
            errors.append(f"row {index}: missing fields {sorted(missing)}")
            continue
        try:
            cell = _cell(row)
        except (TypeError, ValueError, KeyError) as exc:
            errors.append(f"row {index}: invalid cell key: {exc}")
            continue
        if cell in seen:
            errors.append(f"row {index}: duplicate cell {cell}")
        seen.add(cell)
        method, seed, domain, split, condition = cell
        if method not in REQUIRED_METHODS:
            errors.append(f"row {index}: unsupported method={method}")
        if seed not in CANONICAL_SEEDS:
            errors.append(f"row {index}: non-canonical seed={seed}")
        cells_by_method[method].add((seed, domain, split, condition))

        if not _is_sha(row["prediction_sha256"]):
            errors.append(f"row {index}: invalid prediction_sha256")
        if not _is_sha(row["data_sha256"]):
            errors.append(f"row {index}: invalid data_sha256")
        if not _is_sha(row["raw_log_sha256"]):
            errors.append(f"row {index}: invalid raw_log_sha256")
        if not _is_sha(row["code_commit"], 40):
            errors.append(f"row {index}: code_commit must be a full 40-hex SHA")
        if method != "random" and not _is_sha(row["model_sha256"]):
            errors.append(f"row {index}: invalid model_sha256")

        for field, positive in (
            ("peak_rss_bytes", True), ("training_wall_seconds", False),
            ("cpu_inference_ms_per_item", True),
        ):
            if not _finite_nonnegative(row[field], positive=positive):
                errors.append(f"row {index}: invalid {field}={row[field]!r}")
        if method != "random" and not _finite_nonnegative(row["model_bytes"], positive=True):
            errors.append(f"row {index}: invalid model_bytes={row.get('model_bytes')!r}")

        for path_field, hash_field in (
            ("prediction_path", "prediction_sha256"),
            ("data_path", "data_sha256"),
            ("raw_log_path", "raw_log_sha256"),
            *(([("model_path", "model_sha256")]) if method != "random" else []),
        ):
            path = root / str(row[path_field])
            if not path.is_file():
                errors.append(f"row {index}: missing artifact {path_field}={path}")
                continue
            actual = _sha256(path)
            if actual != str(row[hash_field]).lower():
                errors.append(f"row {index}: checksum mismatch for {path_field}")
            else:
                verified_files += 1
            if path_field == "model_path" and path.stat().st_size != int(row["model_bytes"]):
                errors.append(f"row {index}: model_bytes does not match file size")

        eval_cell = (seed, domain, split, condition)
        dataset_by_eval_cell[eval_cell].add(str(row["data_sha256"]).lower())
        commit_by_method_seed[(method, seed)].add(str(row["code_commit"]).lower())
        if method != "random":
            model_by_method_seed[(method, seed)].add(str(row["model_sha256"]).lower())

        resource_tuple = (
            row["peak_rss_bytes"], row["training_wall_seconds"],
            row["cpu_inference_ms_per_item"], row.get("model_bytes"),
            row["raw_log_sha256"], row.get("model_sha256"),
        )
        resource_tuple_owners[resource_tuple].add((method, seed))

    missing_methods = REQUIRED_METHODS - set(cells_by_method)
    if missing_methods:
        errors.append(f"missing methods: {sorted(missing_methods)}")

    reference = cells_by_method.get("correct", set())
    for method in sorted(REQUIRED_METHODS):
        observed = cells_by_method.get(method, set())
        if observed != reference:
            errors.append(
                f"method {method}: cell coverage differs from correct "
                f"(missing={len(reference-observed)}, extra={len(observed-reference)})"
            )

    for eval_cell, hashes in sorted(dataset_by_eval_cell.items()):
        if len(hashes) != 1:
            errors.append(f"eval cell {eval_cell}: methods use different datasets")
    for key, commits in sorted(commit_by_method_seed.items()):
        if len(commits) != 1:
            errors.append(f"method/seed {key}: code_commit changes across cells")
    for key, models in sorted(model_by_method_seed.items()):
        if len(models) != 1:
            errors.append(f"method/seed {key}: checkpoint changes across cells")

    copied_resource_groups = [
        sorted(owners) for owners in resource_tuple_owners.values()
        if len(owners) > 1 and len({method for method, _ in owners}) > 1
    ]
    if copied_resource_groups:
        errors.append(
            "identical full resource/artifact tuples reused across different methods; "
            "per-method measurements or explicit shared-model provenance are required"
        )

    seeds_by_method = {
        method: sorted({seed for seed, _, _, _ in cells})
        for method, cells in sorted(cells_by_method.items())
    }
    for method, seeds in seeds_by_method.items():
        if set(seeds) != CANONICAL_SEEDS:
            errors.append(f"method {method}: expected seeds {sorted(CANONICAL_SEEDS)}, found {seeds}")

    return {
        "valid": not errors,
        "classification": "audited" if not errors else "initial_reproduction_failure",
        "errors": errors,
        "rows": len(rows),
        "verified_files": verified_files,
        "methods": sorted(cells_by_method),
        "seeds_by_method": seeds_by_method,
        "reference_cells": len(reference),
        "copied_resource_groups": copied_resource_groups,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = audit(_read_jsonl(args.manifest), args.root)
    except Exception as exc:  # fail closed with reproducible machine-readable output
        result = {
            "valid": False,
            "classification": "initial_reproduction_failure",
            "errors": [f"audit exception: {type(exc).__name__}: {exc}"],
        }
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
