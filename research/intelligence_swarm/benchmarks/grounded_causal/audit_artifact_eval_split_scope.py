#!/usr/bin/env python3
"""Fail closed when resource manifests use train or unregistered split cells."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

MODULE_PATH = Path(__file__).with_name("evaluation_contract.py")
SPEC = importlib.util.spec_from_file_location("evaluation_contract", MODULE_PATH)
assert SPEC and SPEC.loader
EC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EC)


def audit(manifest: dict[str, Any]) -> dict[str, Any]:
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

    for index, run in enumerate(runs, 1):
        if not isinstance(run, dict):
            errors.append(f"run {index}: must be an object")
            continue
        raw_split = run.get("split")
        split = str(raw_split).strip().casefold() if raw_split is not None else ""
        finding = {
            "run": index,
            "method": str(run.get("method", "")),
            "seed": run.get("seed"),
            "domain": str(run.get("domain", "")),
            "condition": str(run.get("condition", "")),
            "raw_split": raw_split,
            "normalized_split": split,
            "registered_evaluation_split": split in EC.EVAL_SPLITS,
        }
        findings.append(finding)
        if not split:
            errors.append(f"run {index}: split must be non-empty")
        elif split not in EC.EVAL_SPLITS:
            errors.append(
                f"run {index}: artifact run split={split!r} is not a registered evaluation split; "
                f"allowed={sorted(EC.EVAL_SPLITS)}"
            )

    return {
        "valid": not errors,
        "errors": errors,
        "findings": findings,
        "allowed_evaluation_splits": sorted(EC.EVAL_SPLITS),
        "train_resource_cells_forbidden": True,
        "unregistered_resource_cells_forbidden": True,
        "classification": "reproduced" if not errors else "initial_reproduction_failure",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest top-level JSON must be an object")
        result = audit(manifest)
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
