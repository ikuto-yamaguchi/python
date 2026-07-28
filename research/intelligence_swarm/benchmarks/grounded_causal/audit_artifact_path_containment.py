#!/usr/bin/env python3
"""Fail closed when an R0 evidence manifest references artifacts outside its bundle.

This auditor is intentionally independent from checksum validation.  A checksum can
prove the bytes that were read, but not that those bytes were shipped as part of the
reproduction bundle.  Absolute paths, ``..`` escapes and symlink traversal are
therefore rejected before an R0 result can be accepted.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

CLASSIFICATION = "initial_reproduction_failure"
RUN_PATH_FIELDS = ("model_path", "data_path", "raw_log_path", "predictions_path")
TOP_LEVEL_PATH_FIELDS = ("statistics_path", "predictions_path")


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _symlink_components(root: Path, relative: Path) -> list[str]:
    found: list[str] = []
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            found.append(str(current))
    return found


def _iter_references(manifest: dict[str, Any]) -> Iterable[tuple[str, Any]]:
    for field in TOP_LEVEL_PATH_FIELDS:
        if field in manifest:
            yield field, manifest[field]
    runs = manifest.get("runs", [])
    if isinstance(runs, list):
        for index, run in enumerate(runs, 1):
            if not isinstance(run, dict):
                continue
            for field in RUN_PATH_FIELDS:
                if field in run:
                    yield f"runs[{index}].{field}", run[field]


def audit(manifest: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    checks: list[dict[str, Any]] = []
    root = base_dir.resolve(strict=True)

    references = list(_iter_references(manifest))
    if not references:
        errors.append("manifest contains no auditable artifact path references")

    for source, raw in references:
        value = str(raw) if raw is not None else ""
        record: dict[str, Any] = {"source": source, "value": value}
        if not value:
            errors.append(f"{source}: artifact path must be non-empty")
            record["contained"] = False
            checks.append(record)
            continue

        relative = Path(value)
        if relative.is_absolute():
            errors.append(f"{source}: absolute artifact paths are forbidden: {value}")
            record.update({"absolute": True, "contained": False})
            checks.append(record)
            continue

        lexical_escape = any(part == ".." for part in relative.parts)
        symlinks = _symlink_components(root, relative)
        resolved = (root / relative).resolve(strict=False)
        contained = _inside(root, resolved)
        exists = resolved.is_file()
        nonempty = exists and resolved.stat().st_size > 0
        record.update(
            {
                "resolved": str(resolved),
                "absolute": False,
                "lexical_parent_escape": lexical_escape,
                "symlink_components": symlinks,
                "contained": contained,
                "regular_file": exists,
                "nonempty": nonempty,
            }
        )

        if lexical_escape:
            errors.append(f"{source}: parent-directory components are forbidden: {value}")
        if symlinks:
            errors.append(f"{source}: symlink traversal is forbidden: {symlinks}")
        if not contained:
            errors.append(f"{source}: resolved artifact escapes bundle root: {resolved}")
        if not exists:
            errors.append(f"{source}: artifact is not a regular file inside bundle: {value}")
        elif not nonempty:
            errors.append(f"{source}: artifact is empty: {value}")
        checks.append(record)

    return {
        "valid": not errors,
        "errors": errors,
        "checks": checks,
        "bundle_root": str(root),
        "path_references": len(references),
        "absolute_paths_forbidden": True,
        "parent_escape_forbidden": True,
        "symlink_traversal_forbidden": True,
        "nonempty_regular_files_required": True,
        "classification": "qualified" if not errors else CLASSIFICATION,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--base-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest top level must be an object")
        result = audit(manifest, args.base_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"valid": False, "errors": [str(exc)], "classification": CLASSIFICATION}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
