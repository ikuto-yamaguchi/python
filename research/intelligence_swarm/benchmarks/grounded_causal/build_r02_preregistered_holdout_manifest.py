#!/usr/bin/env python3
"""Build an immutable R0.2 holdout manifest from generator metadata only.

This utility deliberately does not read trajectories, actions, rewards, model
predictions, or evaluation metrics.  It consumes one row per generated episode
and a preregistered split specification containing explicit signature sets.
That separation prevents post-hoc holdout assignment based on model outcomes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CANONICAL_SEEDS = (1, 7, 19)
KEY_FIELDS = ("domain", "split", "seed", "episode_seed")
SIGNATURE_FIELDS = (
    "entity_signature",
    "dynamics_signature",
    "language_form_signature",
)
HOLDOUT_TO_SIGNATURE = {
    "entity_holdout": "entity_signature",
    "dynamics_holdout": "dynamics_signature",
    "language_holdout": "language_form_signature",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def episode_key(row: dict[str, Any]) -> tuple[str, str, int, int]:
    missing = [field for field in KEY_FIELDS if field not in row]
    if missing:
        raise ValueError(f"missing key fields: {missing}")
    return (
        str(row["domain"]),
        str(row["split"]),
        int(row["seed"]),
        int(row["episode_seed"]),
    )


def validate_metadata(rows: list[dict[str, Any]]) -> None:
    seen: set[tuple[str, str, int, int]] = set()
    for row in rows:
        key = episode_key(row)
        if key in seen:
            raise ValueError(f"duplicate episode metadata key: {key}")
        seen.add(key)
        if key[2] not in CANONICAL_SEEDS:
            raise ValueError(f"non-canonical seed: {key[2]}")
        if key[1] not in {"train", "test"}:
            raise ValueError(f"unsupported split: {key[1]!r}")
        for field in SIGNATURE_FIELDS:
            value = row.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{key}: missing non-empty {field}")
        forbidden = {
            "action", "reward", "done", "episode_return", "task_success",
            "prediction", "action_accuracy", "next_state_loss",
        }
        present = sorted(forbidden.intersection(row))
        if present:
            raise ValueError(f"{key}: outcome/model fields forbidden in generator metadata: {present}")


def validate_spec(spec: Any) -> dict[str, set[str]]:
    if not isinstance(spec, dict):
        raise ValueError("split specification must be a JSON object")
    if spec.get("version") != 1:
        raise ValueError("split specification version must be 1")
    result: dict[str, set[str]] = {}
    for holdout_field, signature_field in HOLDOUT_TO_SIGNATURE.items():
        values = spec.get(holdout_field)
        if not isinstance(values, list) or not values:
            raise ValueError(f"{holdout_field} must be a non-empty list")
        normalized = {str(value).strip() for value in values}
        if "" in normalized or len(normalized) != len(values):
            raise ValueError(f"{holdout_field} contains empty or duplicate signatures")
        result[signature_field] = normalized
    return result


def build_manifest(
    metadata_rows: list[dict[str, Any]],
    spec: Any,
    metadata_path: Path,
    spec_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    validate_metadata(metadata_rows)
    holdout_sets = validate_spec(spec)

    observed_by_field = {
        field: {str(row[field]) for row in metadata_rows if row["split"] == "test"}
        for field in SIGNATURE_FIELDS
    }
    for field, requested in holdout_sets.items():
        missing = sorted(requested - observed_by_field[field])
        if missing:
            raise ValueError(f"preregistered {field} signatures absent from test metadata: {missing}")

    output: list[dict[str, Any]] = []
    held_out_episode_counts = {field: 0 for field in HOLDOUT_TO_SIGNATURE}
    held_out_seed_coverage = {field: set() for field in HOLDOUT_TO_SIGNATURE}
    for row in metadata_rows:
        item = {field: row[field] for field in KEY_FIELDS + SIGNATURE_FIELDS}
        for holdout_field, signature_field in HOLDOUT_TO_SIGNATURE.items():
            enabled = row["split"] == "test" and str(row[signature_field]) in holdout_sets[signature_field]
            item[holdout_field] = enabled
            if enabled:
                held_out_episode_counts[holdout_field] += 1
                held_out_seed_coverage[holdout_field].add(int(row["seed"]))
        output.append(item)

    for holdout_field, seeds in held_out_seed_coverage.items():
        if seeds != set(CANONICAL_SEEDS):
            raise ValueError(
                f"{holdout_field} lacks canonical seed coverage: "
                f"observed={sorted(seeds)} expected={list(CANONICAL_SEEDS)}"
            )

    output.sort(key=episode_key)
    summary = {
        "status": "success",
        "episodes": len(output),
        "canonical_seeds": list(CANONICAL_SEEDS),
        "metadata_sha256": sha256(metadata_path),
        "split_spec_sha256": sha256(spec_path),
        "held_out_episode_counts": held_out_episode_counts,
        "held_out_seed_coverage": {
            field: sorted(seeds) for field, seeds in held_out_seed_coverage.items()
        },
        "assignment_source": "generator_metadata_and_preregistered_signature_sets_only",
    }
    return output, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-metadata", type=Path, required=True)
    parser.add_argument("--split-spec", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    rows, summary = build_manifest(
        load_jsonl(args.episode_metadata),
        load_json(args.split_spec),
        args.episode_metadata,
        args.split_spec,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows) + "\n",
        encoding="utf-8",
    )
    summary["manifest_sha256"] = sha256(args.out)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
