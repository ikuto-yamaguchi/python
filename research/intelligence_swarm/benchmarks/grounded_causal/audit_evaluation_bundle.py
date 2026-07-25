#!/usr/bin/env python3
"""Fail-closed end-to-end audit for R0 grounded-causal evaluation bundles.

Every method×seed×domain×split×condition cell is bound to immutable data,
prediction, model and raw-log artifacts.  The joined real bundle is then passed
through evaluation_contract.py and the semantic alias/value leakage auditor, so
artifact integrity, split leakage, prediction coverage, shuffle provenance and
paired statistics cannot be reported independently.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load sibling {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contract = _load("evaluation_contract", "evaluation_contract.py")
semantic = _load("audit_model_input_semantic_leakage", "audit_model_input_semantic_leakage.py")
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
            "valid": False,
            "errors": errors or ["manifest.runs must be a non-empty list"],
            "checks": checks,
            "classification": "initial_reproduction_failure",
        }

    ids_by_method_cell: dict[tuple[str, int, str, str, str], set[str]] = {}
    data_hashes_by_cell: dict[tuple[int, str, str, str], set[str]] = defaultdict(set)
    model_identity: dict[tuple[str, int], set[tuple[str, str]]] = defaultdict(set)
    datasets_by_hash: dict[str, list[dict[str, Any]]] = {}
    combined_data_by_id: dict[str, dict[str, Any]] = {}
    combined_predictions: list[dict[str, Any]] = []
    prediction_rows = 0

    for index, run in enumerate(runs, 1):
        if not isinstance(run, dict):
            errors.append(f"run {index}: run must be an object")
            continue
        try:
            method = str(run["method"])
            cell = _cell(run)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"run {index}: invalid cell identity: {exc}")
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

        data_hash = str(run.get("data_sha256", "")).lower()
        datasets_by_hash.setdefault(data_hash, data)
        for row in data:
            iid = str(row.get("instance_id", ""))
            previous = combined_data_by_id.get(iid)
            if previous is not None and contract.stable_hash(previous) != contract.stable_hash(row):
                errors.append(f"instance {iid}: conflicting dataset rows across artifacts")
            else:
                combined_data_by_id[iid] = row

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
            if gold is not None:
                expected_fp = contract.instance_fingerprint(gold)
                if str(pred.get("instance_fingerprint")) != expected_fp:
                    errors.append(
                        f"run {index} prediction {row_number}: instance fingerprint mismatch for {iid}"
                    )
            combined_predictions.append(pred)
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
        data_hashes_by_cell[cell].add(data_hash)
        model_identity[(method, cell[0])].add((
            str(run.get("model_sha256", "")).lower(),
            str(run.get("code_commit", "")).lower(),
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
        if any(not ids for ids in method_sets.values()):
            missing_methods = sorted(method for method, ids in method_sets.items() if not ids)
            errors.append(f"cell {cell}: missing method prediction cells {missing_methods}")
        present = [value for value in method_sets.values() if value]
        if present and any(value != present[0] for value in present[1:]):
            errors.append(f"cell {cell}: methods do not cover identical instance IDs")

    for key, identities in sorted(model_identity.items()):
        if len(identities) != 1:
            errors.append(f"method/seed {key}: model or code identity changed across split/condition cells")

    combined_data = list(combined_data_by_id.values())
    dataset_audit = contract.validate_dataset(combined_data) if combined_data else {
        "valid": False, "errors": ["no readable dataset rows"]
    }
    semantic_audit = semantic.audit_rows(combined_data) if combined_data else {
        "valid": False, "errors": ["no readable dataset rows"]
    }
    score_audit = contract.score(combined_data, combined_predictions) if combined_data else {
        "valid": False, "errors": ["no readable dataset rows"]
    }
    for prefix, audit in (
        ("dataset", dataset_audit), ("semantic_leakage", semantic_audit),
        ("prediction_statistics", score_audit),
    ):
        errors.extend(f"{prefix}: {message}" for message in audit.get("errors", []))

    valid = not errors
    return {
        "valid": valid,
        "errors": errors,
        "checks": checks,
        "prediction_rows_read": prediction_rows,
        "unique_dataset_artifacts": len(datasets_by_hash),
        "prediction_artifacts_required": True,
        "exact_prediction_dataset_join_required": True,
        "same_dataset_hash_across_methods_required": True,
        "stable_model_identity_across_conditions_required": True,
        "full_dataset_contract_executed": True,
        "semantic_alias_value_leakage_executed": True,
        "paired_statistics_executed": True,
        "dataset_audit": dataset_audit,
        "semantic_leakage_audit": semantic_audit,
        "prediction_statistics": score_audit,
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
