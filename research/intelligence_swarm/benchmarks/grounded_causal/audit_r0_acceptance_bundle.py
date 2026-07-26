#!/usr/bin/env python3
"""Single fail-closed acceptance gate for an R0 benchmark evidence bundle.

This module does not add a model or research mechanism. It prevents a bundle from
being accepted by running only a convenient subset of the existing contracts.
Dataset/schema leakage, alias-normalized leakage, paired statistics, resource
artifacts, strictly-positive measured resources, bundle-contained artifact paths,
prediction-payload leakage, and prediction/statistics checksums must all pass in
one invocation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import audit_artifact_path_containment as artifact_path_containment
import audit_nonzero_measurements as nonzero_measurements
import audit_prediction_payload_leakage as prediction_payload
import audit_prediction_statistics_artifacts as prediction_statistics
import audit_schema_alias_leakage as schema_alias
import evaluation_contract


CLASSIFICATION_FAILURE = "initial_reproduction_failure"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return value


def audit_acceptance(
    data: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    manifest: dict[str, Any],
    base_dir: Path,
) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}

    checks["dataset_contract"] = evaluation_contract.validate_dataset(data)
    checks["schema_alias_leakage_contract"] = schema_alias.audit(data, predictions)
    checks["prediction_payload_contract"] = prediction_payload.audit_rows(data, predictions)
    checks["paired_statistics_contract"] = evaluation_contract.score(data, predictions)
    checks["resource_artifact_contract"] = evaluation_contract.audit_artifacts(manifest, base_dir)
    checks["nonzero_measurement_contract"] = nonzero_measurements.audit(manifest, base_dir)
    checks["artifact_path_containment_contract"] = artifact_path_containment.audit(manifest, base_dir)
    checks["prediction_statistics_evidence_contract"] = prediction_statistics.audit(manifest, base_dir)

    failed = sorted(name for name, result in checks.items() if result.get("valid") is not True)
    errors = [
        {"contract": name, "errors": result.get("errors", ["contract did not return valid=true"])}
        for name, result in checks.items()
        if result.get("valid") is not True
    ]
    valid = not failed
    return {
        "valid": valid,
        "classification": "reproduced" if valid else CLASSIFICATION_FAILURE,
        "failed_contracts": failed,
        "errors": errors,
        "checks": checks,
        "acceptance_requires_all_contracts": True,
        "alias_normalized_leakage_audit_required": True,
        "strictly_positive_measured_resources_required": True,
        "nonempty_resource_artifacts_required": True,
        "artifact_paths_must_be_bundle_contained": True,
        "absolute_parent_escape_and_symlink_paths_forbidden": True,
        "partial_contract_success_is_not_acceptance": True,
        "new_mechanism_introduced": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    try:
        result = audit_acceptance(
            evaluation_contract.read_jsonl(args.data),
            evaluation_contract.read_jsonl(args.predictions),
            read_json(args.manifest),
            args.base_dir,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "valid": False,
            "classification": CLASSIFICATION_FAILURE,
            "failed_contracts": ["bundle_loading"],
            "errors": [{"contract": "bundle_loading", "errors": [str(exc)]}],
        }

    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
