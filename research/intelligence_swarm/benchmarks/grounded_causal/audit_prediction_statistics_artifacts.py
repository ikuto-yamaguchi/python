#!/usr/bin/env python3
"""Fail-closed checksum and provenance audit for R0 predictions and statistics.

The model, dataset and raw log are insufficient evidence when the prediction JSONL
or the derived statistics report can be replaced after evaluation.  This auditor
closes that gap without introducing any model or research mechanism.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
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
RUN_REQUIRED = {
    "method", "seed", "domain", "split", "condition",
    "predictions_path", "predictions_sha256",
}
STAT_REQUIRED = {"statistics_path", "statistics_sha256"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _hex(value: Any, length: int) -> bool:
    text = str(value)
    return len(text) == length and all(ch in "0123456789abcdefABCDEF" for ch in text)


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


def _finite_json(value: Any) -> bool:
    if value is None or isinstance(value, (bool, int, str)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _finite_json(item) for key, item in value.items())
    return False


def audit(manifest: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    checks: list[dict[str, Any]] = []
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs:
        return {
            "valid": False,
            "errors": ["manifest.runs must be a non-empty list"],
            "classification": "initial_reproduction_failure",
        }

    methods: set[str] = set()
    seeds: set[int] = set()
    cells: set[tuple[str, int, str, str, str]] = set()
    prediction_paths: set[str] = set()

    for index, run in enumerate(runs, 1):
        if not isinstance(run, dict):
            errors.append(f"run {index}: must be an object")
            continue
        missing = RUN_REQUIRED - run.keys()
        if missing:
            errors.append(f"run {index}: missing prediction evidence fields {sorted(missing)}")
            continue
        try:
            method = str(run["method"])
            seed = int(run["seed"])
            domain = str(run["domain"])
            split = str(run["split"])
            condition = str(run["condition"])
        except (TypeError, ValueError, KeyError) as exc:
            errors.append(f"run {index}: invalid indexing field {exc}")
            continue
        cell = (method, seed, domain, split, condition)
        if cell in cells:
            errors.append(f"run {index}: duplicate prediction artifact cell {cell}")
        cells.add(cell)
        methods.add(method)
        seeds.add(seed)

        rel = str(run["predictions_path"])
        expected = str(run["predictions_sha256"])
        prediction_paths.add(rel)
        if not _hex(expected, 64):
            errors.append(f"run {index}: predictions_sha256 must be a full SHA-256")
            continue
        path = base_dir / rel
        if not path.is_file():
            errors.append(f"run {index}: missing prediction artifact {path}")
            continue
        actual = _sha256(path)
        checks.append({"kind": "predictions", "run": index, "path": str(path), "expected": expected, "actual": actual, "ok": actual == expected.lower()})
        if actual != expected.lower():
            errors.append(f"run {index}: prediction checksum mismatch")
            continue
        try:
            rows = _read_jsonl(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
            continue
        if not rows:
            errors.append(f"run {index}: prediction artifact is empty")
        row_methods = {str(row.get("method")) for row in rows}
        if row_methods != {method}:
            errors.append(f"run {index}: prediction rows must contain only method {method}, found {sorted(row_methods)}")
        if not _finite_json(rows):
            errors.append(f"run {index}: prediction artifact contains non-finite or unsupported JSON values")

    unexpected = methods - REQUIRED_METHODS
    missing_methods = REQUIRED_METHODS - methods
    if unexpected:
        errors.append(f"unexpected methods in prediction evidence: {sorted(unexpected)}")
    if missing_methods:
        errors.append(f"missing methods in prediction evidence: {sorted(missing_methods)}")
    if seeds != CANONICAL_SEEDS:
        errors.append(f"prediction evidence seeds must be exactly {sorted(CANONICAL_SEEDS)}, found {sorted(seeds)}")

    missing_stats = STAT_REQUIRED - manifest.keys()
    statistics_summary: dict[str, Any] = {}
    if missing_stats:
        errors.append(f"manifest missing statistics evidence fields {sorted(missing_stats)}")
    else:
        rel = str(manifest["statistics_path"])
        expected = str(manifest["statistics_sha256"])
        if not _hex(expected, 64):
            errors.append("statistics_sha256 must be a full SHA-256")
        else:
            path = base_dir / rel
            if not path.is_file():
                errors.append(f"missing statistics artifact {path}")
            else:
                actual = _sha256(path)
                checks.append({"kind": "statistics", "path": str(path), "expected": expected, "actual": actual, "ok": actual == expected.lower()})
                if actual != expected.lower():
                    errors.append("statistics checksum mismatch")
                else:
                    try:
                        report = _read_json(path)
                    except (OSError, ValueError, json.JSONDecodeError) as exc:
                        errors.append(str(exc))
                    else:
                        score = report.get("scores", report)
                        if not isinstance(score, dict):
                            errors.append("statistics artifact must contain an object score report")
                        else:
                            required_sections = {"cells", "summary", "paired_gaps_vs_correct", "coverage"}
                            absent = required_sections - score.keys()
                            if absent:
                                errors.append(f"statistics artifact missing sections {sorted(absent)}")
                            if report.get("valid") is not True or score.get("valid") is not True:
                                errors.append("statistics artifact is not a valid accepted evaluation")
                            classification = str(report.get("classification", score.get("classification", "")))
                            if classification == "initial_reproduction_failure":
                                errors.append("statistics artifact is classified as initial_reproduction_failure")
                            if not _finite_json(score):
                                errors.append("statistics artifact contains non-finite or unsupported JSON values")
                            statistics_summary = {
                                "cells": len(score.get("cells", [])) if isinstance(score.get("cells"), list) else None,
                                "methods": sorted(score.get("summary", {}).keys()) if isinstance(score.get("summary"), dict) else [],
                                "controls": sorted(score.get("paired_gaps_vs_correct", {}).keys()) if isinstance(score.get("paired_gaps_vs_correct"), dict) else [],
                            }

    return {
        "valid": not errors,
        "errors": errors,
        "checks": checks,
        "runs": len(runs),
        "prediction_artifacts": len(prediction_paths),
        "methods": sorted(methods),
        "seeds": sorted(seeds),
        "statistics_summary": statistics_summary,
        "prediction_checksums_required": True,
        "statistics_checksum_required": True,
        "statistics_validity_required": True,
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
        result = {"valid": False, "errors": [str(exc)], "classification": "initial_reproduction_failure"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
