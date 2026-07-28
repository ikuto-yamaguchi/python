#!/usr/bin/env python3
"""Fail-closed public-baseline reproduction audit for an R0 evidence bundle.

This auditor does not introduce a model or mechanism.  It requires a submitted
public baseline claim to be tied to an immutable upstream revision, explicit
expected/observed values, preregistered tolerances, and the checksummed
statistics artifact from which the observations were taken.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

CLASSIFICATION_FAILURE = "initial_reproduction_failure"
HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return value


def audit(manifest: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    baseline = manifest.get("public_baseline")
    if not isinstance(baseline, dict):
        return {
            "valid": False,
            "classification": CLASSIFICATION_FAILURE,
            "errors": ["manifest.public_baseline must be an object"],
            "metric_checks": {},
        }

    name = baseline.get("name")
    source_url = baseline.get("source_url")
    source_commit = baseline.get("source_commit")
    source_version = baseline.get("source_version")
    expected = baseline.get("expected_values")
    observed = baseline.get("observed_values")
    tolerances = baseline.get("absolute_tolerances")
    baseline_statistics_sha = baseline.get("statistics_sha256")
    manifest_statistics_sha = manifest.get("statistics_sha256")

    if not isinstance(name, str) or not name.strip():
        errors.append("public_baseline.name must be a non-empty string")
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        errors.append("public_baseline.source_url must be an https URL")
    if not isinstance(source_commit, str) or HEX40.fullmatch(source_commit) is None:
        errors.append("public_baseline.source_commit must be a full 40-hex upstream commit")
    if not isinstance(source_version, str) or not source_version.strip():
        errors.append("public_baseline.source_version must be a non-empty immutable release/tag description")
    if not isinstance(expected, dict) or not expected:
        errors.append("public_baseline.expected_values must be a non-empty object")
        expected = {}
    if not isinstance(observed, dict) or not observed:
        errors.append("public_baseline.observed_values must be a non-empty object")
        observed = {}
    if not isinstance(tolerances, dict) or not tolerances:
        errors.append("public_baseline.absolute_tolerances must be a non-empty object")
        tolerances = {}
    if not isinstance(baseline_statistics_sha, str) or HEX64.fullmatch(baseline_statistics_sha) is None:
        errors.append("public_baseline.statistics_sha256 must be a full 64-hex SHA-256")
    if not isinstance(manifest_statistics_sha, str) or HEX64.fullmatch(manifest_statistics_sha) is None:
        errors.append("manifest.statistics_sha256 must be a full 64-hex SHA-256")
    elif baseline_statistics_sha != manifest_statistics_sha:
        errors.append("public baseline observations are not bound to manifest.statistics_sha256")

    expected_keys = set(expected)
    observed_keys = set(observed)
    tolerance_keys = set(tolerances)
    if expected_keys != observed_keys:
        errors.append(
            f"expected/observed metric keys differ: expected={sorted(expected_keys)}, observed={sorted(observed_keys)}"
        )
    if expected_keys != tolerance_keys:
        errors.append(
            f"expected/tolerance metric keys differ: expected={sorted(expected_keys)}, tolerances={sorted(tolerance_keys)}"
        )

    checks: dict[str, dict[str, Any]] = {}
    for metric in sorted(expected_keys | observed_keys | tolerance_keys):
        exp = expected.get(metric)
        obs = observed.get(metric)
        tol = tolerances.get(metric)
        metric_errors: list[str] = []
        if not _finite_number(exp):
            metric_errors.append("expected value must be finite numeric")
        if not _finite_number(obs):
            metric_errors.append("observed value must be finite numeric")
        if not _finite_number(tol) or (_finite_number(tol) and float(tol) < 0):
            metric_errors.append("absolute tolerance must be finite and non-negative")
        delta = None
        within = False
        if not metric_errors:
            delta = float(obs) - float(exp)
            within = abs(delta) <= float(tol)
            if not within:
                metric_errors.append(
                    f"absolute deviation {abs(delta):.12g} exceeds tolerance {float(tol):.12g}"
                )
        checks[metric] = {
            "expected": exp,
            "observed": obs,
            "absolute_tolerance": tol,
            "delta": delta,
            "within_tolerance": within,
            "errors": metric_errors,
        }
        errors.extend(f"metric {metric}: {message}" for message in metric_errors)

    valid = not errors
    return {
        "valid": valid,
        "classification": "reproduced" if valid else CLASSIFICATION_FAILURE,
        "errors": errors,
        "baseline_name": name,
        "source_url": source_url,
        "source_commit": source_commit,
        "source_version": source_version,
        "statistics_sha256": baseline_statistics_sha,
        "metric_checks": checks,
        "immutable_upstream_revision_required": True,
        "explicit_expected_observed_values_required": True,
        "preregistered_absolute_tolerances_required": True,
        "statistics_checksum_binding_required": True,
        "new_mechanism_introduced": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit(_read_json(args.manifest))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "valid": False,
            "classification": CLASSIFICATION_FAILURE,
            "errors": [str(exc)],
            "metric_checks": {},
        }
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
