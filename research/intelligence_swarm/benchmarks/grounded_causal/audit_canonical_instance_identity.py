#!/usr/bin/env python3
"""Fail-closed audit for Unicode/format aliases of R0 instance identifiers."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from .evaluation_contract import canonical_text, read_jsonl
except ImportError:
    from evaluation_contract import canonical_text, read_jsonl


def canonical_instance_id(value: Any) -> str:
    return canonical_text(value)


def audit(dataset: list[dict[str, Any]], predictions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    raw_by_canonical: dict[str, set[str]] = defaultdict(set)
    dataset_ids: set[str] = set()

    for index, row in enumerate(dataset, 1):
        if "instance_id" not in row:
            errors.append(f"dataset row {index}: missing instance_id")
            continue
        raw = str(row["instance_id"])
        canonical = canonical_instance_id(raw)
        if not canonical:
            errors.append(f"dataset row {index}: instance_id is empty after canonicalization")
            continue
        dataset_ids.add(raw)
        raw_by_canonical[canonical].add(raw)

    collisions = {
        canonical: sorted(raws)
        for canonical, raws in sorted(raw_by_canonical.items())
        if len(raws) > 1
    }
    if collisions:
        errors.append(f"instance_id aliases collide after canonicalization: {collisions}")

    prediction_findings: list[dict[str, Any]] = []
    if predictions is not None:
        canonical_dataset = {canonical_instance_id(raw): raw for raw in dataset_ids}
        for index, row in enumerate(predictions, 1):
            if "instance_id" not in row:
                errors.append(f"prediction row {index}: missing instance_id")
                continue
            raw = str(row["instance_id"])
            canonical = canonical_instance_id(raw)
            exact = raw in dataset_ids
            alias_target = canonical_dataset.get(canonical)
            finding = {
                "row": index,
                "raw_instance_id": raw,
                "canonical_instance_id": canonical,
                "exact_dataset_match": exact,
                "canonical_dataset_match": alias_target,
            }
            prediction_findings.append(finding)
            if not canonical:
                errors.append(f"prediction row {index}: instance_id is empty after canonicalization")
            elif not exact and alias_target is not None:
                errors.append(
                    f"prediction row {index}: instance_id {raw!r} is a non-exact alias of dataset id {alias_target!r}"
                )

    return {
        "valid": not errors,
        "classification": "qualified" if not errors else "initial_reproduction_failure",
        "errors": errors,
        "canonical_instance_identity_required": True,
        "normalization": "NFKC + casefold + remove whitespace/control-format characters",
        "dataset_instance_count": len(dataset),
        "canonical_instance_count": len(raw_by_canonical),
        "collisions": collisions,
        "prediction_findings": prediction_findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(read_jsonl(args.dataset), read_jsonl(args.predictions) if args.predictions else None)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
