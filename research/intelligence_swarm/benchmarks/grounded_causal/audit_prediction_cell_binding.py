#!/usr/bin/env python3
"""Fail-closed binding audit between manifest run cells and prediction rows.

A checksummed prediction file is not evidence for a declared run cell unless every
row belongs to that exact seed/domain/split/condition and method. This auditor
prevents one arbitrary or pooled prediction file from being reused to fabricate
complete domain x seed x condition coverage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_METHODS = {
    "correct",
    "random",
    "language_blind",
    "state_only",
    "target_label_shuffle",
    "outcome_shuffle",
}
CANONICAL_SEEDS = {1, 7, 19}
INDEX_FIELDS = ("method", "seed", "domain", "split", "condition")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: row must be an object")
            rows.append(value)
    return rows


def _cell(value: dict[str, Any]) -> tuple[str, int, str, str, str]:
    return (
        str(value["method"]),
        int(value["seed"]),
        str(value["domain"]),
        str(value["split"]).lower(),
        str(value["condition"]),
    )


def audit(manifest: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    evidence: list[dict[str, Any]] = []
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs:
        return {
            "valid": False,
            "errors": ["manifest.runs must be a non-empty list"],
            "classification": "initial_reproduction_failure",
        }

    declared_cells: set[tuple[str, int, str, str, str]] = set()
    artifact_to_cells: dict[str, set[tuple[str, int, str, str, str]]] = {}
    methods: set[str] = set()
    seeds: set[int] = set()

    for index, run in enumerate(runs, 1):
        if not isinstance(run, dict):
            errors.append(f"run {index}: must be an object")
            continue
        missing = set(INDEX_FIELDS) | {"predictions_path"} - run.keys()
        if missing:
            errors.append(f"run {index}: missing fields {sorted(missing)}")
            continue
        try:
            cell = _cell(run)
        except (TypeError, ValueError, KeyError) as exc:
            errors.append(f"run {index}: invalid run cell {exc}")
            continue
        if cell in declared_cells:
            errors.append(f"run {index}: duplicate declared cell {cell}")
        declared_cells.add(cell)
        methods.add(cell[0])
        seeds.add(cell[1])

        rel = str(run["predictions_path"])
        artifact_to_cells.setdefault(rel, set()).add(cell)
        path = base_dir / rel
        if not path.is_file():
            errors.append(f"run {index}: missing prediction artifact {path}")
            continue
        try:
            rows = _read_jsonl(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
            continue
        if not rows:
            errors.append(f"run {index}: prediction artifact is empty")
            continue

        observed_cells: set[tuple[str, int, str, str, str]] = set()
        for row_no, row in enumerate(rows, 1):
            missing_row = set(INDEX_FIELDS) - row.keys()
            if missing_row:
                errors.append(f"run {index} prediction row {row_no}: missing cell fields {sorted(missing_row)}")
                continue
            try:
                observed = _cell(row)
            except (TypeError, ValueError, KeyError) as exc:
                errors.append(f"run {index} prediction row {row_no}: invalid cell {exc}")
                continue
            observed_cells.add(observed)
            if observed != cell:
                errors.append(
                    f"run {index} prediction row {row_no}: artifact row cell {observed} does not match declared cell {cell}"
                )
        if observed_cells != {cell}:
            errors.append(
                f"run {index}: prediction artifact must contain exactly declared cell {cell}, found {sorted(observed_cells)}"
            )
        evidence.append({
            "run": index,
            "path": rel,
            "declared_cell": list(cell),
            "observed_cells": [list(value) for value in sorted(observed_cells)],
            "rows": len(rows),
        })

    for rel, cells in sorted(artifact_to_cells.items()):
        if len(cells) != 1:
            errors.append(
                f"prediction artifact {rel!r} is reused across multiple declared cells {sorted(cells)}"
            )

    if methods != REQUIRED_METHODS:
        errors.append(f"methods must be exactly {sorted(REQUIRED_METHODS)}, found {sorted(methods)}")
    if seeds != CANONICAL_SEEDS:
        errors.append(f"seeds must be exactly {sorted(CANONICAL_SEEDS)}, found {sorted(seeds)}")

    return {
        "valid": not errors,
        "errors": errors,
        "runs": len(runs),
        "evidence": evidence,
        "prediction_artifacts": len(artifact_to_cells),
        "declared_cells": len(declared_cells),
        "row_cell_binding_required": True,
        "one_prediction_artifact_per_cell_required": True,
        "pooled_or_reused_prediction_artifacts_forbidden": True,
        "classification": "reproduced" if not errors else "initial_reproduction_failure",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        result = audit(_read_json(args.manifest), args.base_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "valid": False,
            "errors": [str(exc)],
            "classification": "initial_reproduction_failure",
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
