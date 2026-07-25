#!/usr/bin/env python3
"""Fail-closed join audit for R0 grounded-causal evaluation artifacts.

This supplements evaluation_contract.py by proving that every reported
method×seed×domain×split×condition run is backed by a readable prediction
file over exactly the immutable instances declared by its dataset artifact.
Standard library only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "evaluation_contract", HERE / "evaluation_contract.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load sibling evaluation_contract.py")
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)

PREDICTION_ARTIFACT_FIELDS = ("prediction_path", "prediction_sha256")


def _cell(run: dict[str, Any]) -> tuple[int, str, str, str]:
    return (
        int(run["seed"]), str(run["domain"]), str(run["split"]).lower(),
        str(run["condition"]),
    )


def _verify_file(base_dir: Path, run_index: int, run: dict[str, Any],
                 path_key: str, hash_key: str, errors: list[str],
                 checks: list[dict[str, Any]]) -> Path | None:
    relative = run.get(path_key)
    expected = run.get(hash_key)
    if not relative:
        errors.append(f"run {run_index}: {path_key} is required")
        return None
    if not contract._is_hex(expected, 64):
        errors.append(f"run {run_index}: {hash_key} must be a full 64-hex SHA-256")
        return None
    path = base_dir / str(relative)
    if not path.is_file():
        errors.append(f"run {run_index}: missing artifact {path}")
        return None
    actual = contract.file_sha256(path)
    ok = actual == str(expected).lower()
    checks.append({
        "run": run_index, "path": str(path), "expected": expected,
        "actual": actual, "ok": ok, "size_bytes": path.stat().st_size,
    })
    if not ok:
        errors.append(f"run {run_index}: checksum mismatch for {path_key}")
        return None
    return path


def audit_bundle(manifest: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    base = contract.audit_artifacts(manifest, base_dir)
    errors = list(base.get("errors", []))
    checks = list(base.get("checks", []))
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs:
        return {
            "valid": False, "errors": errors or ["manifest.runs must be a non-empty list"],
            "checks": checks, "classification": "initial_reproduction_failure",
        }

    ids_by_method_cell: dict[tuple[str, int, str, str, str], set[str]] = {}
    data_hashes_by_cell: dict[tuple[int, str, str, str], set[str]] = defaultdict(set)
    model_identity: dict[tuple[str, int], set[tuple[str, str]]] = defaultdict(set)
    prediction_rows = 0

    for index, run in enumerate(runs, 1):
        if not isinstance(run, dict):
            continue
        try:
            method = str(run["method"])
            cell = _cell(run)
        except (KeyError, TypeError, ValueError):
            continue

        prediction_path = _verify_file(
            base_dir, index, run, *PREDICTION_ARTIFACT_FIELDS, errors, checks
        )
        data_path_value = run.get("data_path")
        data_path = base_dir / str(data_path_value) if data_path_value else None
        if prediction_path is None or data_path is None or not data_path.is_file():
            continue

        try:
            data = contract.adapt_dataset(contract.read_jsonl(data_path))
            predictions = contract.read_jsonl(prediction_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"run {index}: unreadable dataset/prediction artifact: {exc}")
            continue

        expected_rows = [
            row for row in data
            if int(row.get("seed", -1)) == cell[0]
            and str(row.get("domain")) == cell[1]
            and str(row.get("split", "")).lower() == cell[2]
            and str(row.get("condition")) == cell[3]
        ]
        expected_ids = {str(row["instance_id"]) for row in expected_rows}
        if not expected_ids:
            errors.append(f"run {index}: dataset has no instances for cell {cell}")

        actual_ids: set[str] = set()
        duplicates: set[str] = set()
        expected_by_id = {str(row["instance_id"]): row for row in expected_rows}
        for row_number, pred in enumerate(predictions, 1):
            prediction_rows += 1
            if str(pred.get("method")) != method:
                errors.append(
                    f"run {index} prediction {row_number}: method mismatch "
                    f"{pred.get('method')!r} != {method!r}"
                )
            iid = str(pred.get("instance_id", ""))
            if iid in actual_ids:
                duplicates.add(iid)
            actual_ids.add(iid)
            gold = expected_by_id.get(iid)
            if gold is None:
                continue
            expected_fp = contract.instance_fingerprint(gold)
            if str(pred.get("instance_fingerprint")) != expected_fp:
                errors.append(
                    f"run {index} prediction {row_number}: instance fingerprint mismatch for {iid}"
                )
        if duplicates:
            errors.append(f"run {index}: duplicate prediction instance IDs: {sorted(duplicates)[:5]}")
        missing = expected_ids - actual_ids
        extra = actual_ids - expected_ids
        if missing or extra:
            errors.append(
                f"run {index}: prediction/data join mismatch "
                f"missing={len(missing)} extra={len(extra)}"
            )

        ids_by_method_cell[(method, *cell)] = actual_ids
        data_hashes_by_cell[cell].add(str(run.get("data_sha256", "")).lower())
        model_identity[(method, cell[0])].add((
            str(run.get("model_sha256", "")).lower(), str(run.get("code_commit", "")).lower()
        ))

    required_methods = {"correct"} | contract.REQUIRED_CONTROL_METHODS
    for cell in sorted(data_hashes_by_cell):
        hashes = data_hashes_by_cell[cell]
        if len(hashes) != 1:
            errors.append(f"cell {cell}: methods did not use one immutable dataset hash")
        method_sets = {
            method: ids_by_method_cell.get((method, *cell), set())
            for method in required_methods
        }
        present = [value for value in method_sets.values() if value]
        if present and any(value != present[0] for value in present[1:]):
            errors.append(f"cell {cell}: methods do not cover identical instance IDs")

    for key, identities in sorted(model_identity.items()):
        if len(identities) != 1:
            errors.append(
                f"method/seed {key}: model or code identity changed across split/condition cells"
            )

    valid = not errors
    return {
        "valid": valid,
        "errors": errors,
        "checks": checks,
        "prediction_rows_read": prediction_rows,
        "prediction_artifacts_required": True,
        "exact_prediction_dataset_join_required": True,
        "same_dataset_hash_across_methods_required": True,
        "stable_model_identity_across_conditions_required": True,
        "classification": "reproduced" if valid else "initial_reproduction_failure",
        "base_artifact_audit": base,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        result = audit_bundle(contract.read_json(args.manifest), args.base_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "valid": False, "errors": [str(exc)],
            "classification": "initial_reproduction_failure",
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
