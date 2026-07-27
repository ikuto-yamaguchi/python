#!/usr/bin/env python3
"""Fail closed when scoring emits statistics for an invalid R0 dataset."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import evaluation_contract as contract

STATISTICAL_FIELDS = ("cells", "summary", "paired_gaps_vs_correct")


def audit_score_dataset_contract_binding(
    dataset_rows: list[dict[str, Any]], prediction_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    dataset_audit = contract.validate_dataset(dataset_rows)
    score_audit = contract.score(dataset_rows, prediction_rows)
    emitted = {
        field: bool(score_audit.get(field))
        for field in STATISTICAL_FIELDS
    }
    errors: list[str] = []

    if not dataset_audit.get("valid", False):
        contaminated = sorted(field for field, present in emitted.items() if present)
        if contaminated:
            errors.append(
                "score emitted statistical evidence for a dataset that failed the "
                f"dataset contract: {contaminated}"
            )
        if score_audit.get("classification") != "initial_reproduction_failure":
            errors.append(
                "score did not classify an invalid dataset as initial_reproduction_failure"
            )

    score_dataset_binding = score_audit.get("dataset_contract_binding")
    if score_dataset_binding is not True:
        errors.append("score artifact does not declare dataset_contract_binding=true")

    if score_audit.get("dataset_contract_valid") is not dataset_audit.get("valid"):
        errors.append("score artifact dataset_contract_valid does not match validate_dataset()")

    return {
        "valid": not errors,
        "classification": "qualified" if not errors else "initial_reproduction_failure",
        "errors": errors,
        "dataset_contract_valid": bool(dataset_audit.get("valid", False)),
        "dataset_contract_errors": list(dataset_audit.get("errors", [])),
        "score_valid": bool(score_audit.get("valid", False)),
        "score_classification": score_audit.get("classification"),
        "statistical_evidence_emitted": emitted,
        "dataset_contract_binding_required": True,
        "invalid_dataset_statistics_forbidden": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = audit_score_dataset_contract_binding(
        contract.read_jsonl(args.dataset), contract.read_jsonl(args.predictions)
    )
    text = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
