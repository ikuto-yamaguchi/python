#!/usr/bin/env python3
"""Fail-closed semantic audit for target-label and outcome shuffle controls."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

METHOD_SPECS = {
    "target_label_shuffle": {
        "transform": "replace_gold_action_from_donor",
        "source_keys": ("gold_action", "action", "target_label"),
        "kind": "target_label",
    },
    "outcome_shuffle": {
        "transform": "replace_gold_state_after_from_donor",
        "source_keys": ("gold_state_after", "state_after", "outcome", "episode_success", "task_success"),
        "kind": "outcome",
    },
}
REQUIRED_PROVENANCE = {
    "control_source_instance_id",
    "control_source_fingerprint",
    "control_source_value_sha256",
    "control_applied_value_sha256",
    "control_transform",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: row must be an object")
            rows.append(value)
    return rows


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if "gold_action" not in out and "action" in out:
        out["gold_action"] = out["action"]
    if "gold_state_after" not in out and "state_after" in out:
        out["gold_state_after"] = out["state_after"]
    if "condition" not in out:
        out["condition"] = "in_distribution"
    return out


def instance_fingerprint(row: dict[str, Any]) -> str:
    canonical = _canonical_row(row)
    payload = {
        key: canonical.get(key)
        for key in (
            "domain", "seed", "split", "condition", "utterance", "text_tokens",
            "state_before", "history", "valid_action_mask", "valid", "entity_id",
            "entity_signature", "dynamics_id", "dynamics_signature", "episode_id",
            "episode_seed", "observation_fingerprint",
        )
    }
    return stable_hash(payload)


def _cell(row: dict[str, Any]) -> tuple[int, str, str, str]:
    canonical = _canonical_row(row)
    return (
        int(canonical["seed"]),
        str(canonical["domain"]),
        str(canonical["split"]).lower(),
        str(canonical["condition"]),
    )


def _source_value(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, Any] | None:
    canonical = _canonical_row(row)
    for key in keys:
        if key in canonical:
            return key, canonical[key]
    return None


def audit(dataset: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    canonical_data = [_canonical_row(row) for row in dataset]
    by_id = {str(row.get("instance_id")): row for row in canonical_data if row.get("instance_id") is not None}
    if len(by_id) != len(canonical_data):
        errors.append("dataset instance_id values must be present and unique")

    audit_by_method: dict[str, Any] = {}
    for method, spec in METHOD_SPECS.items():
        rows = [row for row in predictions if str(row.get("method")) == method]
        cell_targets: dict[tuple[int, str, str, str], list[str]] = defaultdict(list)
        cell_donors: dict[tuple[int, str, str, str], list[str]] = defaultdict(list)
        cell_value_changes: dict[tuple[int, str, str, str], list[bool]] = defaultdict(list)
        source_fields: set[str] = set()

        if not rows:
            errors.append(f"missing required shuffle method: {method}")

        for index, pred in enumerate(rows, 1):
            missing = REQUIRED_PROVENANCE - pred.keys()
            if missing:
                errors.append(f"{method} row {index}: missing semantic provenance {sorted(missing)}")
                continue
            target_id = str(pred.get("instance_id"))
            donor_id = str(pred["control_source_instance_id"])
            target = by_id.get(target_id)
            donor = by_id.get(donor_id)
            if target is None:
                errors.append(f"{method} row {index}: unknown target instance {target_id}")
                continue
            if donor is None:
                errors.append(f"{method} row {index}: unknown donor instance {donor_id}")
                continue
            if target_id == donor_id:
                errors.append(f"{method} row {index}: self-shuffle is not allowed")
            if _cell(target) != _cell(donor):
                errors.append(f"{method} row {index}: donor crosses seed/domain/split/condition cell")
            expected_fingerprint = instance_fingerprint(donor)
            if str(pred["control_source_fingerprint"]) != expected_fingerprint:
                errors.append(f"{method} row {index}: donor fingerprint mismatch")
            if str(pred["control_transform"]) != spec["transform"]:
                errors.append(f"{method} row {index}: control_transform must be {spec['transform']!r}")

            donor_value = _source_value(donor, spec["source_keys"])
            target_value = _source_value(target, spec["source_keys"])
            if donor_value is None or target_value is None:
                errors.append(f"{method} row {index}: dataset lacks a supported {spec['kind']} field")
                continue
            donor_key, donor_payload = donor_value
            _, target_payload = target_value
            source_fields.add(donor_key)
            expected_value_hash = stable_hash({"kind": spec["kind"], "value": donor_payload})
            if str(pred["control_source_value_sha256"]) != expected_value_hash:
                errors.append(f"{method} row {index}: donor value hash mismatch")
            if str(pred["control_applied_value_sha256"]) != expected_value_hash:
                errors.append(f"{method} row {index}: applied control value is not the donor value")

            cell = _cell(target)
            cell_targets[cell].append(target_id)
            cell_donors[cell].append(donor_id)
            cell_value_changes[cell].append(donor_payload != target_payload)

        cells: dict[str, Any] = {}
        for cell in sorted(cell_targets):
            targets = cell_targets[cell]
            donors = cell_donors[cell]
            changes = cell_value_changes[cell]
            bijective = len(targets) == len(set(donors)) and set(targets) == set(donors)
            deranged = all(target != donor for target, donor in zip(targets, donors))
            changed = sum(changes)
            changed_fraction = changed / len(changes) if changes else 0.0
            if not bijective:
                errors.append(f"{method} cell {cell}: donor assignment is not a bijection")
            if not deranged:
                errors.append(f"{method} cell {cell}: donor assignment is not a derangement")
            if changes and changed == 0:
                errors.append(f"{method} cell {cell}: shuffle changes no semantic values")
            if changes and changed_fraction < 0.25:
                warnings.append(f"{method} cell {cell}: only {changed_fraction:.3f} of semantic values changed")
            cells[str(cell)] = {
                "n": len(targets),
                "unique_donors": len(set(donors)),
                "bijective": bijective,
                "deranged": deranged,
                "changed_values": changed,
                "changed_value_fraction": changed_fraction,
            }

        audit_by_method[method] = {
            "rows": len(rows),
            "source_fields": sorted(source_fields),
            "required_transform": spec["transform"],
            "cells": cells,
        }

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": sorted(set(warnings)),
        "methods": audit_by_method,
        "semantic_payload_hash_required": True,
        "same_cell_bijection_required": True,
        "value_level_change_required_per_cell": True,
        "classification": "reproduced" if not errors else "initial_reproduction_failure",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = audit(read_jsonl(args.dataset), read_jsonl(args.predictions))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"valid": False, "errors": [str(exc)], "classification": "initial_reproduction_failure"}
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
