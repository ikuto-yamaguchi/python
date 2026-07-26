#!/usr/bin/env python3
"""Single fail-closed acceptance gate for an R0 benchmark evidence bundle.

This module does not add a model or research mechanism. It prevents a bundle from
being accepted by running only a convenient subset of the existing contracts.
Dataset/schema leakage, alias-normalized leakage, explicit holdout-condition
integrity, registered train/evaluation split scope, paired statistics, complete
same-instance metric coverage, resource artifacts, strictly-positive measured
resources, bundle-contained artifact paths, prediction-payload leakage,
prediction-cell binding, prediction/statistics checksums, and deterministic
statistics recomputation must all pass together.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import audit_artifact_path_containment as artifact_path_containment
import audit_explicit_holdout_condition as explicit_holdout_condition
import audit_nonzero_measurements as nonzero_measurements
import audit_prediction_cell_binding as prediction_cell_binding
import audit_prediction_eval_split_scope as prediction_eval_split_scope
import audit_prediction_metric_coverage as prediction_metric_coverage
import audit_prediction_payload_leakage as prediction_payload
import audit_prediction_statistics_artifacts as prediction_statistics
import audit_schema_alias_leakage as schema_alias
import audit_statistics_recomputation_binding as statistics_recomputation
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
    checks["explicit_holdout_condition_contract"] = explicit_holdout_condition.audit(data)
    checks["prediction_eval_split_scope_contract"] = prediction_eval_split_scope.audit(data, predictions)
    checks["prediction_payload_contract"] = prediction_payload.audit_rows(data, predictions)
    checks["prediction_metric_coverage_contract"] = prediction_metric_coverage.audit(data, predictions)
    checks["paired_statistics_contract"] = evaluation_contract.score(data, predictions)
    checks["resource_artifact_contract"] = evaluation_contract.audit_artifacts(manifest, base_dir)
    checks["nonzero_measurement_contract"] = nonzero_measurements.audit(manifest, base_dir)
    checks["artifact_path_containment_contract"] = artifact_path_containment.audit(manifest, base_dir)
    checks["prediction_cell_binding_contract"] = prediction_cell_binding.audit(manifest, base_dir)
    checks["prediction_statistics_evidence_contract"] = prediction_statistics.audit(manifest, base_dir)
    checks["statistics_recomputation_binding_contract"] = statistics_recomputation.audit(
        data, predictions, manifest, base_dir
    )

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
        "explicit_holdout_condition_labels_are_authoritative": True,
        "held_out_signature_presence_required": True,
        "train_holdout_signature_disjointness_required": True,
        "registered_split_vocabulary_required": True,
        "allowed_train_split": "train",
        "allowed_evaluation_splits": ["eval", "test", "valid", "validation"],
        "nonregistered_debug_calibration_posthoc_splits_forbidden": True,
        "same_instance_metric_coverage_required": True,
        "selective_metric_reporting_forbidden": True,
        "optional_gold_metrics_must_be_all_or_none": True,
        "all_methods_must_report_each_preregistered_metric": True,
        "strictly_positive_measured_resources_required": True,
        "nonempty_resource_artifacts_required": True,
        "artifact_paths_must_be_bundle_contained": True,
        "absolute_parent_escape_and_symlink_paths_forbidden": True,
        "prediction_rows_must_match_declared_run_cell": True,
        "pooled_or_reused_prediction_artifacts_forbidden": True,
        "saved_statistics_must_equal_fresh_recomputation": True,
        "statistics_checksum_alone_is_not_acceptance": True,
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
