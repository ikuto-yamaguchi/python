#!/usr/bin/env python3
"""Fail closed unless saved R0 statistics equal deterministic recomputation.

Checksums preserve bytes, but a fabricated statistics report can still be checksummed.
This audit binds the saved report to the canonical dataset and prediction rows by
re-running evaluation_contract.score and comparing the complete score object.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import evaluation_contract

CLASSIFICATION_FAILURE = "initial_reproduction_failure"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return value


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def audit(
    data: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    manifest: dict[str, Any],
    base_dir: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    relative = manifest.get("statistics_path")
    if not isinstance(relative, str) or not relative:
        return {
            "valid": False,
            "classification": CLASSIFICATION_FAILURE,
            "errors": ["manifest.statistics_path must be a non-empty relative path"],
        }

    path = base_dir / relative
    if not path.is_file():
        return {
            "valid": False,
            "classification": CLASSIFICATION_FAILURE,
            "errors": [f"statistics artifact does not exist: {path}"],
        }

    saved_report = _read_json(path)
    saved_score = saved_report.get("scores", saved_report)
    if not isinstance(saved_score, dict):
        errors.append("statistics artifact must contain an object score report")
        saved_score = {}

    recomputed = evaluation_contract.score(data, predictions)
    if recomputed.get("valid") is not True:
        errors.append("fresh deterministic score is not valid")

    try:
        saved_canonical = _canonical(saved_score)
        recomputed_canonical = _canonical(recomputed)
    except (TypeError, ValueError) as exc:
        errors.append(f"statistics contain non-canonical or non-finite JSON: {exc}")
        saved_canonical = ""
        recomputed_canonical = ""

    if saved_canonical != recomputed_canonical:
        errors.append("saved statistics do not exactly match fresh evaluation_contract.score recomputation")

    return {
        "valid": not errors,
        "classification": "reproduced" if not errors else CLASSIFICATION_FAILURE,
        "errors": errors,
        "statistics_path": relative,
        "saved_score_sha256": evaluation_contract.stable_hash(saved_score),
        "recomputed_score_sha256": evaluation_contract.stable_hash(recomputed),
        "exact_score_binding_required": True,
        "deterministic_recomputation_required": True,
        "checksum_alone_is_insufficient": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        result = audit(
            evaluation_contract.read_jsonl(args.data),
            evaluation_contract.read_jsonl(args.predictions),
            _read_json(args.manifest),
            args.base_dir,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"valid": False, "classification": CLASSIFICATION_FAILURE, "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
