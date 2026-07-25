#!/usr/bin/env python3
"""Fail-closed alias-normalized leakage audit for R0 datasets and predictions.

This closes schema-variant bypasses such as goldStateAfter, gold-state-after,
completedTrajectory, terminalObservation and episodeReturn.  It complements
``evaluation_contract.py`` without introducing a model or mechanism.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import evaluation_contract as contract


def normalize_key(value: Any) -> str:
    """Normalize snake/camel/kebab/space variants to one comparison key."""
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


FORBIDDEN_ALIASES = {
    normalize_key(key): key
    for key in (contract.FORBIDDEN_MODEL_INPUT_FIELDS | contract.FORBIDDEN_PREDICTION_FIELDS)
}


def find_alias_leakage(value: Any, prefix: str = "") -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(value, dict):
        for raw_key, nested in value.items():
            key = str(raw_key)
            path = f"{prefix}.{key}" if prefix else key
            canonical = FORBIDDEN_ALIASES.get(normalize_key(key))
            if canonical is not None:
                findings.append({"path": path, "key": key, "canonical_forbidden_key": canonical})
            findings.extend(find_alias_leakage(nested, path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            findings.extend(find_alias_leakage(nested, f"{prefix}[{index}]"))
    return findings


def audit(dataset: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    findings: list[dict[str, Any]] = []

    for row_index, row in enumerate(contract.adapt_dataset(dataset), 1):
        fields = row.get("model_input_fields", [])
        if isinstance(fields, list):
            for field_index, field in enumerate(fields):
                canonical = FORBIDDEN_ALIASES.get(normalize_key(field))
                if canonical is not None:
                    finding = {
                        "source": "dataset.model_input_fields",
                        "row": row_index,
                        "path": f"model_input_fields[{field_index}]",
                        "key": str(field),
                        "canonical_forbidden_key": canonical,
                    }
                    findings.append(finding)
                    errors.append(
                        f"dataset row {row_index}: alias-normalized forbidden model input field "
                        f"{field!r} -> {canonical!r}"
                    )
        for item in find_alias_leakage(row.get("model_input", {}), "model_input"):
            finding = {"source": "dataset.model_input", "row": row_index, **item}
            findings.append(finding)
            errors.append(
                f"dataset row {row_index}: alias-normalized forbidden model input key "
                f"{item['path']!r} -> {item['canonical_forbidden_key']!r}"
            )

    allowed_prediction_roots = {
        normalize_key(key) for key in contract.ALLOWED_PREDICTION_FIELDS
    }
    for row_index, row in enumerate(predictions, 1):
        for key in row:
            normalized = normalize_key(key)
            canonical = FORBIDDEN_ALIASES.get(normalized)
            if canonical is not None:
                finding = {
                    "source": "prediction",
                    "row": row_index,
                    "path": str(key),
                    "key": str(key),
                    "canonical_forbidden_key": canonical,
                }
                findings.append(finding)
                errors.append(
                    f"prediction row {row_index}: alias-normalized forbidden key "
                    f"{key!r} -> {canonical!r}"
                )
            elif normalized not in allowed_prediction_roots:
                errors.append(f"prediction row {row_index}: unregistered prediction key {key!r}")

    return {
        "valid": not errors,
        "errors": errors,
        "classification": "qualified" if not errors else "initial_reproduction_failure",
        "alias_normalization": "casefold_and_remove_non_alphanumeric",
        "forbidden_aliases": sorted(FORBIDDEN_ALIASES),
        "findings": findings,
        "dataset_rows": len(dataset),
        "prediction_rows": len(predictions),
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return contract.read_jsonl(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("predictions", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit(read_jsonl(args.dataset), read_jsonl(args.predictions))
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
