#!/usr/bin/env python3
"""Idempotently bind core artifact claims to machine-readable raw-log records."""
from __future__ import annotations

from pathlib import Path

CORE = Path(__file__).with_name("evaluation_contract.py")

HELPERS = r'''
RAW_LOG_MEASUREMENT_FIELDS = (
    "method", "seed", "domain", "split", "condition", "code_commit",
    "model_bytes", "peak_rss_bytes", "training_wall_seconds",
    "cpu_inference_ms_per_item", "model_sha256", "data_sha256",
)


def _iter_raw_log_objects(value: Any):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _iter_raw_log_objects(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_raw_log_objects(nested)


def _read_raw_log_objects(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    objects: list[dict[str, Any]] = []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                parsed_line = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{path}:{line_number}: raw log must be JSON, JSONL, or nested JSON: {exc}"
                ) from exc
            objects.extend(obj for obj in _iter_raw_log_objects(parsed_line) if isinstance(obj, dict))
    else:
        objects.extend(obj for obj in _iter_raw_log_objects(parsed) if isinstance(obj, dict))
    return objects


def _raw_log_cell(row: dict[str, Any]) -> tuple[str, int, str, str, str]:
    return (
        str(row["method"]),
        int(row["seed"]),
        str(row["domain"]),
        unicodedata.normalize("NFKC", str(row["split"])).casefold(),
        str(row["condition"]),
    )


def _is_raw_log_measurement(row: dict[str, Any]) -> bool:
    kind = str(row.get("record_type", row.get("event", row.get("type", "")))).casefold()
    return kind in {"r0_measurement", "resource_measurement", "measurement"} and all(
        field in row for field in RAW_LOG_MEASUREMENT_FIELDS
    )


def _audit_run_raw_log_binding(
    run: dict[str, Any], index: int, base_dir: Path, cache: dict[Path, list[dict[str, Any]]]
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    finding: dict[str, Any] = {"run": index, "matching_measurement_records": 0}
    raw_path, path_error = _resolve_contained_artifact(base_dir, run.get("raw_log_path", ""))
    if path_error is not None:
        errors.append(f"run {index}: raw_log_path {path_error}")
        return errors, finding
    assert raw_path is not None
    finding["raw_log_path"] = str(raw_path.relative_to(base_dir.resolve()))
    try:
        records = cache.setdefault(raw_path, _read_raw_log_objects(raw_path))
        cell = _raw_log_cell(run)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"run {index}: invalid raw-log measurement schema: {exc}")
        return errors, finding
    finding["cell"] = list(cell)
    matches: list[dict[str, Any]] = []
    for record in records:
        if not _is_raw_log_measurement(record):
            continue
        try:
            if _raw_log_cell(record) == cell:
                matches.append(record)
        except (KeyError, TypeError, ValueError):
            continue
    finding["matching_measurement_records"] = len(matches)
    if len(matches) != 1:
        errors.append(
            f"run {index}: expected exactly one raw-log measurement record for cell {cell}, found {len(matches)}"
        )
        return errors, finding
    record = matches[0]
    for field in RAW_LOG_MEASUREMENT_FIELDS:
        expected, observed = run.get(field), record.get(field)
        if field == "split":
            expected = unicodedata.normalize("NFKC", str(expected)).casefold()
            observed = unicodedata.normalize("NFKC", str(observed)).casefold()
        elif field == "seed":
            try:
                expected, observed = int(expected), int(observed)
            except (TypeError, ValueError):
                errors.append(f"run {index}: seed is not integer-like in manifest or raw log")
                continue
        elif field in {"model_bytes", "peak_rss_bytes", "training_wall_seconds", "cpu_inference_ms_per_item"}:
            if not _finite_positive(expected) or not _finite_positive(observed):
                errors.append(f"run {index}: raw-log {field} must be finite and positive")
                continue
            expected, observed = float(expected), float(observed)
        if observed != expected:
            errors.append(f"run {index}: raw-log {field} mismatch: manifest={expected!r}, log={observed!r}")
    return errors, finding
'''.strip("\n")


def apply() -> bool:
    text = CORE.read_text(encoding="utf-8")
    changed = False
    if "RAW_LOG_MEASUREMENT_FIELDS = (" not in text:
        anchor = "\n\ndef audit_artifacts(manifest: dict[str, Any], base_dir: Path) -> dict[str, Any]:\n"
        if anchor not in text:
            raise RuntimeError("audit_artifacts anchor not found")
        text = text.replace(anchor, "\n\n" + HELPERS + anchor, 1)
        changed = True

    old_init = "    errors, checks = [], []; runs = manifest.get(\"runs\")"
    new_init = "    errors, checks, raw_log_findings = [], [], []; raw_log_cache: dict[Path, list[dict[str, Any]]] = {}; runs = manifest.get(\"runs\")"
    if old_init in text:
        text = text.replace(old_init, new_init, 1)
        changed = True
    elif new_init not in text:
        raise RuntimeError("audit_artifacts initialization anchor not found")

    old_call_anchor = "            if path_key == \"model_path\" and _finite_positive(run.get(\"model_bytes\")) and int(run[\"model_bytes\"]) != path.stat().st_size: errors.append(f\"run {index}: model_bytes does not match model artifact size\")\n"
    new_call = old_call_anchor + "        binding_errors, binding_finding = _audit_run_raw_log_binding(run, index, base_dir, raw_log_cache)\n        errors.extend(binding_errors); raw_log_findings.append(binding_finding)\n"
    if "binding_errors, binding_finding = _audit_run_raw_log_binding" not in text:
        if old_call_anchor not in text:
            raise RuntimeError("artifact-loop anchor not found")
        text = text.replace(old_call_anchor, new_call, 1)
        changed = True

    old_return_piece = '"artifact_split_scope_fail_closed": True, "classification"'
    new_return_piece = '"artifact_split_scope_fail_closed": True, "raw_log_measurement_findings": raw_log_findings, "raw_log_measurement_binding_required": True, "exactly_one_measurement_record_per_run_required": True, "raw_log_bound_fields": list(RAW_LOG_MEASUREMENT_FIELDS), "classification"'
    if old_return_piece in text:
        text = text.replace(old_return_piece, new_return_piece, 1)
        changed = True
    elif new_return_piece not in text:
        raise RuntimeError("audit return anchor not found")

    if changed:
        CORE.write_text(text, encoding="utf-8")
    return changed


if __name__ == "__main__":
    print("changed" if apply() else "already-applied")
