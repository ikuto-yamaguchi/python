#!/usr/bin/env python3
"""Fail closed on placeholder resource measurements in R0 manifests.

The core contract historically accepted finite non-negative numbers.  A bundle
could therefore use zero for model bytes, peak RSS, training wall time or CPU
latency and still look structurally complete.  This auditor requires actual,
strictly-positive measurements and non-empty independently hashed artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

MEASUREMENTS = (
    "model_bytes",
    "peak_rss_bytes",
    "training_wall_seconds",
    "cpu_inference_ms_per_item",
)
ARTIFACTS = (
    ("raw_log_path", "raw_log_sha256"),
    ("model_path", "model_sha256"),
    ("data_path", "data_sha256"),
)
FAILURE = "initial_reproduction_failure"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def positive_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) > 0.0
    )


def audit(manifest: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    checks: list[dict[str, Any]] = []
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs:
        return {
            "valid": False,
            "errors": ["manifest.runs must be a non-empty list"],
            "classification": FAILURE,
            "checks": [],
        }

    for index, run in enumerate(runs, 1):
        if not isinstance(run, dict):
            errors.append(f"run {index}: must be an object")
            continue
        for key in MEASUREMENTS:
            value = run.get(key)
            ok = positive_number(value)
            checks.append({"run": index, "field": key, "value": value, "strictly_positive": ok})
            if not ok:
                errors.append(f"run {index}: {key} must be a finite strictly-positive measured value")

        for path_key, hash_key in ARTIFACTS:
            relative = run.get(path_key)
            expected = str(run.get(hash_key, "")).lower()
            if not relative:
                errors.append(f"run {index}: {path_key} is required")
                continue
            path = base_dir / str(relative)
            if not path.is_file():
                errors.append(f"run {index}: missing artifact {path}")
                continue
            size = path.stat().st_size
            actual = sha256(path)
            ok_hash = len(expected) == 64 and actual == expected
            checks.append({
                "run": index,
                "path": str(path),
                "size_bytes": size,
                "nonempty": size > 0,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "checksum_ok": ok_hash,
            })
            if size <= 0:
                errors.append(f"run {index}: {path_key} artifact must be non-empty")
            if not ok_hash:
                errors.append(f"run {index}: checksum mismatch for {path_key}")
            if path_key == "model_path" and positive_number(run.get("model_bytes")):
                if int(run["model_bytes"]) != size:
                    errors.append(f"run {index}: model_bytes does not match model artifact size")

    return {
        "valid": not errors,
        "errors": errors,
        "classification": "qualified_measurements" if not errors else FAILURE,
        "runs": len(runs),
        "checks": checks,
        "strictly_positive_measurements_required": list(MEASUREMENTS),
        "nonempty_artifacts_required": [item[0] for item in ARTIFACTS],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be a JSON object")
        result = audit(manifest, args.base_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"valid": False, "errors": [str(exc)], "classification": FAILURE}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
