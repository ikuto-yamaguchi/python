#!/usr/bin/env python3
"""Bind public-baseline observed values to exact fields in the saved statistics JSON."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

CLASSIFICATION_FAILURE = "initial_reproduction_failure"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _contained_file(base_dir: Path, raw: Any) -> tuple[Path | None, str | None]:
    rel = Path(str(raw))
    if not str(raw) or rel.is_absolute() or ".." in rel.parts:
        return None, "statistics_path must be a contained relative path"
    root = base_dir.resolve()
    cursor = base_dir
    for part in rel.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return None, "statistics_path must not traverse symlinks"
    try:
        path = (base_dir / rel).resolve(strict=True)
    except OSError as exc:
        return None, f"statistics_path cannot be resolved: {exc}"
    if path != root and root not in path.parents:
        return None, "statistics_path resolves outside bundle root"
    if not path.is_file() or path.stat().st_size <= 0:
        return None, "statistics_path must be a non-empty regular file"
    return path, None


def _pointer_get(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("metric path must be an RFC 6901 JSON pointer")
    current = value
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise KeyError(token)
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit() or int(token) >= len(current):
                raise KeyError(token)
            current = current[int(token)]
        else:
            raise KeyError(token)
    return current


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def audit(manifest: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    baseline = manifest.get("public_baseline")
    if not isinstance(baseline, dict):
        return {"valid": False, "classification": CLASSIFICATION_FAILURE, "errors": ["manifest.public_baseline must be an object"], "metric_checks": {}}

    observed = baseline.get("observed_values")
    metric_paths = baseline.get("metric_paths")
    if not isinstance(observed, dict) or not observed:
        errors.append("public_baseline.observed_values must be a non-empty object")
        observed = {}
    if not isinstance(metric_paths, dict) or not metric_paths:
        errors.append("public_baseline.metric_paths must be a non-empty object")
        metric_paths = {}
    if set(observed) != set(metric_paths):
        errors.append(f"observed/metric_paths keys differ: observed={sorted(observed)}, metric_paths={sorted(metric_paths)}")

    path, path_error = _contained_file(base_dir, manifest.get("statistics_path"))
    statistics: dict[str, Any] = {}
    actual_sha = None
    if path_error:
        errors.append(path_error)
    else:
        assert path is not None
        actual_sha = _sha256(path)
        expected_sha = manifest.get("statistics_sha256")
        if not isinstance(expected_sha, str) or actual_sha != expected_sha.lower():
            errors.append("statistics artifact checksum does not match manifest.statistics_sha256")
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                errors.append("statistics artifact top-level JSON must be an object")
            else:
                statistics = loaded
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"statistics artifact cannot be read: {exc}")

    checks: dict[str, dict[str, Any]] = {}
    for metric in sorted(set(observed) | set(metric_paths)):
        claimed = observed.get(metric)
        pointer = metric_paths.get(metric)
        resolved = None
        metric_errors: list[str] = []
        if not _finite_number(claimed):
            metric_errors.append("observed value must be finite numeric")
        try:
            resolved = _pointer_get(statistics, pointer)
        except (KeyError, ValueError, TypeError) as exc:
            metric_errors.append(f"statistics field cannot be resolved: {exc}")
        if resolved is not None and not _finite_number(resolved):
            metric_errors.append("resolved statistics value must be finite numeric")
        if not metric_errors and float(claimed) != float(resolved):
            metric_errors.append(f"observed value {claimed!r} does not equal statistics value {resolved!r}")
        checks[metric] = {"json_pointer": pointer, "claimed_observed": claimed, "resolved_statistics_value": resolved, "errors": metric_errors}
        errors.extend(f"metric {metric}: {message}" for message in metric_errors)

    valid = not errors
    return {
        "valid": valid,
        "classification": "reproduced" if valid else CLASSIFICATION_FAILURE,
        "errors": errors,
        "statistics_sha256_actual": actual_sha,
        "metric_checks": checks,
        "rfc6901_metric_paths_required": True,
        "observed_values_must_equal_statistics_fields": True,
        "checksum_binding_alone_is_insufficient": True,
        "new_mechanism_introduced": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest top-level JSON must be an object")
        result = audit(manifest, args.base_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"valid": False, "classification": CLASSIFICATION_FAILURE, "errors": [str(exc)], "metric_checks": {}}
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
