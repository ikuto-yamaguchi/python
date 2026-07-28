#!/usr/bin/env python3
"""Bind R0 manifest resource claims to machine-readable records in raw logs."""
from __future__ import annotations

import argparse
import json
import math
import unicodedata
from pathlib import Path
from typing import Any

MEASUREMENT_FIELDS = (
    "method", "seed", "domain", "split", "condition", "code_commit",
    "model_bytes", "peak_rss_bytes", "training_wall_seconds",
    "cpu_inference_ms_per_item", "model_sha256", "data_sha256",
)
EVAL_SPLITS = {"test", "eval", "validation", "valid"}


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _canonical_split(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value)).casefold()


def _canonical_cell(row: dict[str, Any]) -> tuple[str, int, str, str, str]:
    return (
        str(row["method"]),
        int(row["seed"]),
        str(row["domain"]),
        _canonical_split(row["split"]),
        str(row["condition"]),
    )


def _iter_objects(value: Any):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _iter_objects(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_objects(nested)


def _read_log_objects(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    objects: list[dict[str, Any]] = []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                parsed_line = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{path}:{line_number}: raw log must be JSON, JSONL, or nested JSON: {exc}"
                ) from exc
            objects.extend(obj for obj in _iter_objects(parsed_line) if isinstance(obj, dict))
    else:
        objects.extend(obj for obj in _iter_objects(parsed) if isinstance(obj, dict))
    return objects


def _is_measurement_record(row: dict[str, Any]) -> bool:
    kind = str(row.get("record_type", row.get("event", row.get("type", "")))).casefold()
    return kind in {"r0_measurement", "resource_measurement", "measurement"} and all(
        field in row for field in MEASUREMENT_FIELDS
    )


def audit(manifest: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    findings: list[dict[str, Any]] = []
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs:
        return {
            "valid": False,
            "errors": ["manifest.runs must be a non-empty list"],
            "findings": [],
            "classification": "initial_reproduction_failure",
        }

    root = base_dir.resolve()
    cache: dict[Path, list[dict[str, Any]]] = {}
    for index, run in enumerate(runs, 1):
        if not isinstance(run, dict):
            errors.append(f"run {index}: must be an object")
            continue
        missing = [field for field in MEASUREMENT_FIELDS if field not in run]
        if "raw_log_path" not in run:
            missing.append("raw_log_path")
        if missing:
            errors.append(f"run {index}: missing fields {sorted(set(missing))}")
            continue

        rel = Path(str(run["raw_log_path"]))
        if rel.is_absolute() or ".." in rel.parts:
            errors.append(f"run {index}: raw_log_path must be a contained relative path")
            continue
        try:
            path = (root / rel).resolve(strict=True)
        except OSError as exc:
            errors.append(f"run {index}: raw log cannot be resolved: {exc}")
            continue
        if root != path and root not in path.parents:
            errors.append(f"run {index}: raw log resolves outside bundle root")
            continue
        if not path.is_file() or path.stat().st_size <= 0:
            errors.append(f"run {index}: raw log must be a non-empty regular file")
            continue

        try:
            records = cache.setdefault(path, _read_log_objects(path))
            cell = _canonical_cell(run)
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(f"run {index}: invalid manifest/log schema: {exc}")
            continue

        matches = []
        for record in records:
            if not _is_measurement_record(record):
                continue
            try:
                if _canonical_cell(record) == cell:
                    matches.append(record)
            except (KeyError, TypeError, ValueError):
                continue

        findings.append({
            "run": index,
            "raw_log_path": str(rel),
            "cell": list(cell),
            "matching_measurement_records": len(matches),
        })
        if len(matches) != 1:
            errors.append(
                f"run {index}: expected exactly one raw-log measurement record for cell {cell}, "
                f"found {len(matches)}"
            )
            continue

        record = matches[0]
        for field in MEASUREMENT_FIELDS:
            expected, observed = run[field], record[field]
            if field == "split":
                expected, observed = _canonical_split(expected), _canonical_split(observed)
            elif field == "seed":
                try:
                    expected, observed = int(expected), int(observed)
                except (TypeError, ValueError):
                    errors.append(f"run {index}: seed is not integer-like in manifest or raw log")
                    continue
            elif field in {
                "model_bytes", "peak_rss_bytes", "training_wall_seconds",
                "cpu_inference_ms_per_item",
            }:
                if not _finite_number(expected) or not _finite_number(observed):
                    errors.append(f"run {index}: {field} must be finite in manifest and raw log")
                    continue
                expected, observed = float(expected), float(observed)
            if observed != expected:
                errors.append(
                    f"run {index}: raw-log {field} mismatch: manifest={expected!r}, log={observed!r}"
                )

        if cell[3] not in EVAL_SPLITS:
            errors.append(
                f"run {index}: measurement record split={cell[3]!r} is not a registered evaluation split"
            )

    return {
        "valid": not errors,
        "errors": errors,
        "findings": findings,
        "raw_log_measurement_binding_required": True,
        "exactly_one_measurement_record_per_run_required": True,
        "bound_fields": list(MEASUREMENT_FIELDS),
        "classification": "reproduced" if not errors else "initial_reproduction_failure",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be a JSON object")
        result = audit(manifest, args.base_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "valid": False,
            "errors": [str(exc)],
            "findings": [],
            "classification": "initial_reproduction_failure",
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
