#!/usr/bin/env python3
"""Fail-closed audit for real R0.2 RTFM S1 holdout assignments.

RTFM S1 exposes a generator-defined dynamics split.  It does not expose
independently held-out entity or language-form splits.  This evaluator therefore
requires a clean three-seed dynamics holdout and rejects any attempt to label
entity/language-form transfer as measured.  It is an evaluation contract, not a
new model or mechanism.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

CANONICAL_SEEDS = (1, 7, 19)
DYNAMICS_CONDITION = "dynamics_holdout"
DYNAMICS_SIGNATURE = "dynamics_signature"
INAPPLICABLE = {
    "entity_holdout": "entity_signature",
    "language_holdout": "language_form_signature",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"line {line_number}: expected object")
            rows.append(row)
    if not rows:
        raise ValueError("empty dataset")
    return rows


def dataset_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(rows: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    failures: list[str] = []
    by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_split[str(row.get("split", ""))].append(row)

    train = by_split.get("train", [])
    test = by_split.get("test", [])
    if not train or not test:
        failures.append("both train and test rows are required")

    observed_seeds = {int(row["seed"]) for row in rows if "seed" in row}
    if observed_seeds != set(CANONICAL_SEEDS):
        failures.append(
            f"canonical seeds required: expected={list(CANONICAL_SEEDS)} observed={sorted(observed_seeds)}"
        )

    selected = [row for row in test if bool(row.get(DYNAMICS_CONDITION, False))]
    dynamics_seeds = {int(row["seed"]) for row in selected if "seed" in row}
    test_signatures = {str(row.get(DYNAMICS_SIGNATURE, "")) for row in selected}
    test_signatures.discard("")
    train_signatures = {str(row.get(DYNAMICS_SIGNATURE, "")) for row in train}
    train_signatures.discard("")
    overlap = sorted(test_signatures & train_signatures)

    if not selected:
        failures.append("dynamics_holdout: no held-out test rows")
    if dynamics_seeds != set(CANONICAL_SEEDS):
        failures.append(
            f"dynamics_holdout: missing canonical seed coverage; observed={sorted(dynamics_seeds)}"
        )
    if any(DYNAMICS_SIGNATURE not in row or not str(row.get(DYNAMICS_SIGNATURE, "")) for row in selected):
        failures.append(f"dynamics_holdout: missing {DYNAMICS_SIGNATURE}")
    if overlap:
        failures.append(
            f"dynamics_holdout: train/test signature leakage ({len(overlap)} overlaps)"
        )
    if any(bool(row.get(DYNAMICS_CONDITION, False)) for row in train):
        failures.append("dynamics_holdout: train rows cannot be marked held out")

    inapplicable_cells: dict[str, Any] = {}
    for condition, signature_field in INAPPLICABLE.items():
        marked = [row for row in rows if bool(row.get(condition, False))]
        if marked:
            failures.append(
                f"{condition}: RTFM S1 has no qualified split; marked_rows={len(marked)}"
            )
        inapplicable_cells[condition] = {
            "applicable": False,
            "marked_rows": len(marked),
            "signature_field": signature_field,
            "reason": "RTFM S1 does not define an independent generator-backed split",
        }

    assignment_sources = {str(row.get("holdout_assignment_source", "")) for row in rows}
    if assignment_sources != {"pre_outcome_generator_manifest"}:
        failures.append(
            "holdout assignments must come only from pre_outcome_generator_manifest; "
            f"observed={sorted(assignment_sources)}"
        )
    missing_manifest_hash = sum(
        1 for row in rows if not str(row.get("holdout_manifest_sha256", ""))
    )
    if missing_manifest_hash:
        failures.append(f"missing holdout manifest SHA-256 on {missing_manifest_hash} rows")

    status = "pass" if not failures else "initial_reproduction_failure"
    return {
        "status": status,
        "dataset": str(path),
        "dataset_sha256": dataset_sha256(path),
        "rows": len(rows),
        "canonical_seeds": list(CANONICAL_SEEDS),
        "holdout_scope": {
            "dynamics": "applicable",
            "entity": "inapplicable",
            "language_form": "inapplicable",
        },
        "dynamics_holdout": {
            "rows": len(selected),
            "seeds": sorted(dynamics_seeds),
            "unique_test_signatures": len(test_signatures),
            "train_overlap_count": len(overlap),
            "overlap_examples": overlap[:10],
        },
        "inapplicable_cells": inapplicable_cells,
        "assignment_sources": sorted(assignment_sources),
        "missing_manifest_hash_rows": missing_manifest_hash,
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = audit(load_jsonl(args.data), args.data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
