#!/usr/bin/env python3
"""Fail-closed entity/dynamics holdout audit for explicit condition labels.

The core dataset adapter accepts either boolean holdout flags or an explicit
``condition`` string. This auditor prevents an explicit ``entity_holdout`` or
``dynamics_holdout`` cell from bypassing overlap checks merely because the
legacy boolean flag is absent.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

import evaluation_contract

CLASSIFICATION_FAILURE = "initial_reproduction_failure"
EVAL_SPLITS = {"test", "eval", "validation", "valid"}
HOLDOUTS = {"entity": "entity_holdout", "dynamics": "dynamics_holdout"}


def _condition_tokens(value: Any) -> set[str]:
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    return {token for token in re.split(r"[+,|;/\s]+", text) if token}


def _signature(row: dict[str, Any], name: str) -> str | None:
    for key in (f"{name}_id", f"{name}_signature"):
        if row.get(key) is not None:
            return evaluation_contract.stable_hash(row[key])
    return None


def _declares_holdout(row: dict[str, Any], label: str) -> bool:
    return label in _condition_tokens(row.get("condition", "")) or evaluation_contract._truthy(row, label)


def audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    adapted = evaluation_contract.adapt_dataset(rows)
    errors: list[str] = []
    evidence: dict[str, Any] = {}

    for name, label in HOLDOUTS.items():
        train_signatures = {
            signature
            for row in adapted
            if str(row.get("split", "")).casefold() == "train"
            for signature in [_signature(row, name)]
            if signature is not None
        }
        held_rows = [
            row for row in adapted
            if str(row.get("split", "")).casefold() in EVAL_SPLITS and _declares_holdout(row, label)
        ]
        missing = [str(row.get("instance_id", "")) for row in held_rows if _signature(row, name) is None]
        overlap = [
            str(row.get("instance_id", ""))
            for row in held_rows
            if _signature(row, name) is not None and _signature(row, name) in train_signatures
        ]
        by_cell: dict[tuple[str, str, str], int] = defaultdict(int)
        for row in held_rows:
            by_cell[(str(row.get("domain", "")), str(row.get("split", "")).casefold(), str(row.get("condition", "")))] += 1

        if missing:
            errors.append(f"{label}: {len(missing)} held-out rows lack {name}_id/{name}_signature")
        if overlap:
            errors.append(f"{label}: {len(overlap)} held-out rows overlap train {name} signatures")

        evidence[name] = {
            "condition_label": label,
            "train_unique_signatures": len(train_signatures),
            "held_out_rows": len(held_rows),
            "missing_signature_rows": len(missing),
            "missing_signature_examples": missing[:10],
            "overlap_rows": len(overlap),
            "overlap_examples": overlap[:10],
            "held_out_cells": [
                {"domain": domain, "split": split, "condition": condition, "rows": count}
                for (domain, split, condition), count in sorted(by_cell.items())
            ],
        }

    return {
        "valid": not errors,
        "classification": "qualified" if not errors else CLASSIFICATION_FAILURE,
        "errors": errors,
        "checks": evidence,
        "explicit_condition_labels_are_authoritative": True,
        "legacy_boolean_flags_are_not_required": True,
        "held_out_signature_presence_required": True,
        "train_holdout_signature_disjointness_required": True,
        "new_mechanism_introduced": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit(evaluation_contract.read_jsonl(args.data))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"valid": False, "classification": CLASSIFICATION_FAILURE, "errors": [str(exc)]}
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
