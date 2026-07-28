#!/usr/bin/env python3
"""Attach preregistered R0.2 holdout assignments to typed SILG trajectories.

This is a dataset-governance adapter, not a model. The manifest must be created
before model predictions or evaluation outcomes are inspected. It is joined by
(domain, split, seed, episode_seed), and every exported episode must have
exactly one manifest record. No holdout is inferred from observed model
performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

CANONICAL_SEEDS = (1, 7, 19)
KEY_FIELDS = ("domain", "split", "seed", "episode_seed")
SIGNATURE_FIELDS = (
    "entity_signature",
    "dynamics_signature",
    "language_form_signature",
)
HOLDOUT_FIELDS = (
    "entity_holdout",
    "dynamics_holdout",
    "language_holdout",
)
RAW_ASSIGNMENT_SOURCE = "pending_pre_outcome_generator_manifest"
QUALIFIED_ASSIGNMENT_SOURCE = "pre_outcome_generator_manifest"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            rows.append(value)
    if not rows:
        raise ValueError(f"{path}: empty JSONL")
    return rows


def key(row: dict[str, Any]) -> tuple[str, str, int, int]:
    missing = [field for field in KEY_FIELDS if field not in row]
    if missing:
        raise ValueError(f"missing key fields: {missing}")
    return (
        str(row["domain"]),
        str(row["split"]),
        int(row["seed"]),
        int(row["episode_seed"]),
    )


def validate_manifest(rows: list[dict[str, Any]]) -> dict[tuple[str, str, int, int], dict[str, Any]]:
    by_key: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    for row in rows:
        item_key = key(row)
        if item_key in by_key:
            raise ValueError(f"duplicate manifest key: {item_key}")
        if item_key[2] not in CANONICAL_SEEDS:
            raise ValueError(f"non-canonical seed in manifest: {item_key[2]}")
        for field in SIGNATURE_FIELDS:
            value = row.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{item_key}: missing non-empty {field}")
        for field in HOLDOUT_FIELDS:
            if not isinstance(row.get(field), bool):
                raise ValueError(f"{item_key}: {field} must be boolean")
        if item_key[1] == "train" and any(bool(row[field]) for field in HOLDOUT_FIELDS):
            raise ValueError(f"{item_key}: train episodes cannot be marked held out")
        by_key[item_key] = row
    return by_key


def validate_raw_trajectory_assignments(rows: list[dict[str, Any]]) -> None:
    """Reject holdout inference before the immutable generator-manifest join."""
    for row in rows:
        item_key = key(row)
        source = row.get("holdout_assignment_source")
        if source != RAW_ASSIGNMENT_SOURCE:
            raise ValueError(
                f"{item_key}: raw trajectory holdout source must be {RAW_ASSIGNMENT_SOURCE!r}, got {source!r}"
            )
        enabled = [field for field in HOLDOUT_FIELDS if row.get(field) is not False]
        if enabled:
            raise ValueError(
                f"{item_key}: raw trajectory inferred holdout fields before manifest join: {enabled}"
            )


def attach(
    trajectories: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    manifest_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    validate_raw_trajectory_assignments(trajectories)
    manifest = validate_manifest(manifest_rows)
    trajectory_keys = {key(row) for row in trajectories}
    manifest_keys = set(manifest)
    missing = sorted(trajectory_keys - manifest_keys)
    extra = sorted(manifest_keys - trajectory_keys)
    if missing or extra:
        raise ValueError(
            "manifest coverage mismatch: "
            f"missing_episode_keys={missing[:10]} extra_episode_keys={extra[:10]}"
        )

    output: list[dict[str, Any]] = []
    manifest_digest = sha256(manifest_path)
    for row in trajectories:
        assignment = manifest[key(row)]
        merged = dict(row)
        for field in SIGNATURE_FIELDS + HOLDOUT_FIELDS:
            merged[field] = assignment[field]
        merged["holdout_assignment_source"] = QUALIFIED_ASSIGNMENT_SOURCE
        merged["holdout_manifest_sha256"] = manifest_digest
        output.append(merged)

    episode_assignments = {
        key(row): tuple(bool(manifest[key(row)][field]) for field in HOLDOUT_FIELDS)
        for row in trajectories
    }
    counts = Counter()
    for assignment in episode_assignments.values():
        for field, enabled in zip(HOLDOUT_FIELDS, assignment):
            if enabled:
                counts[field] += 1

    summary = {
        "status": "success",
        "trajectory_rows": len(trajectories),
        "episodes": len(episode_assignments),
        "manifest_rows": len(manifest_rows),
        "manifest_sha256": manifest_digest,
        "held_out_episode_counts": dict(sorted(counts.items())),
        "canonical_seeds": list(CANONICAL_SEEDS),
        "holdout_assignment_source": QUALIFIED_ASSIGNMENT_SOURCE,
    }
    return output, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trajectories", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    output, summary = attach(
        load_jsonl(args.trajectories),
        load_jsonl(args.manifest),
        args.manifest,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in output) + "\n",
        encoding="utf-8",
    )
    summary["input_trajectory_sha256"] = sha256(args.trajectories)
    summary["output_dataset_sha256"] = sha256(args.out)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
