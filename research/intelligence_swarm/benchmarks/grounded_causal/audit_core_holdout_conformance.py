#!/usr/bin/env python3
"""Detect disagreement between the core dataset contract and explicit holdout audit.

This is a fail-closed reproducibility check.  It introduces no model or memory
mechanism; it verifies that ``evaluation_contract.validate_dataset`` cannot
silently accept an entity/dynamics holdout violation that the authoritative
explicit-condition audit rejects.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import audit_explicit_holdout_condition
import evaluation_contract

CLASSIFICATION_FAILURE = "initial_reproduction_failure"


def audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    core = evaluation_contract.validate_dataset(rows)
    explicit = audit_explicit_holdout_condition.audit(rows)

    explicit_errors = list(explicit.get("errors", []))
    core_errors = list(core.get("errors", []))
    explicit_violation = not bool(explicit.get("valid"))
    core_rejects = not bool(core.get("valid"))

    # A clean dataset must pass both.  A dataset rejected by the explicit
    # holdout contract must also be rejected by the core contract; otherwise
    # direct callers of validate_dataset can bypass the holdout guarantee.
    agreement = bool(core.get("valid")) == bool(explicit.get("valid"))
    bypass = explicit_violation and not core_rejects
    errors: list[str] = []
    if bypass:
        errors.append(
            "evaluation_contract.validate_dataset accepted an explicit "
            "entity/dynamics holdout violation"
        )
    elif not agreement:
        errors.append("core and explicit holdout contracts disagree")

    return {
        "valid": not errors,
        "classification": "qualified" if not errors else CLASSIFICATION_FAILURE,
        "errors": errors,
        "core_valid": bool(core.get("valid")),
        "explicit_holdout_valid": bool(explicit.get("valid")),
        "core_explicit_holdout_agreement": agreement,
        "direct_core_bypass_detected": bypass,
        "core_error_count": len(core_errors),
        "explicit_holdout_error_count": len(explicit_errors),
        "core_error_examples": core_errors[:10],
        "explicit_holdout_error_examples": explicit_errors[:10],
        "explicit_condition_labels_are_authoritative": True,
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
        result = {
            "valid": False,
            "classification": CLASSIFICATION_FAILURE,
            "errors": [str(exc)],
        }
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
