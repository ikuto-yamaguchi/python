#!/usr/bin/env python3
"""Fail-closed audit for the R0.2 Gaddy & Klein-style SILG adaptation.

This script does not train a model. It verifies that an exported trajectory
bundle contains enough information to run a defensible environment-first
baseline rather than accepting the current flattened-state approximation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

CANONICAL_SEEDS = {1, 7, 19}
HOLDOUT_POLICY = {
    "entity_holdout": "conditional",
    "dynamics_holdout": "required",
    "language_holdout": "conditional",
}
ALLOWED_TYPES = {"continuous", "binary", "categorical"}
ALLOWED_SUPPORT_STATUS = {"supported", "unsupported"}


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _declared_support(metadata: dict[str, Any] | None, key: str) -> str | None:
    """Read an optional fail-closed transfer-support declaration.

    The declaration may be either ``"supported"``/``"unsupported"`` or an
    object with a ``status`` field. Conditional holdouts may be absent and are
    then inferred as supported only when real test rows are present. Dynamics
    remains mandatory regardless of this declaration.
    """
    transfer_support = (metadata or {}).get("transfer_support", {})
    if not isinstance(transfer_support, dict):
        return None
    value = transfer_support.get(key)
    if isinstance(value, dict):
        value = value.get("status")
    return str(value) if value in ALLOWED_SUPPORT_STATUS else None


def audit(rows: list[dict[str, Any]], metadata: dict[str, Any] | None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not rows:
        return {"status": "blocked", "errors": ["empty trajectory dataset"]}

    required = {
        "instance_id", "episode_id", "seed", "split", "domain", "state_before",
        "state_after", "text_tokens", "action", "reward", "done",
    }
    missing = sorted(required - set.intersection(*(set(row) for row in rows)))
    if missing:
        errors.append(f"missing required row fields: {missing}")

    seeds = {int(row["seed"]) for row in rows if "seed" in row}
    if seeds != CANONICAL_SEEDS:
        errors.append(f"canonical seed coverage required: {sorted(CANONICAL_SEEDS)}, found {sorted(seeds)}")

    splits = {str(row.get("split")) for row in rows}
    if not {"train", "test"}.issubset(splits):
        errors.append(f"train/test split coverage required, found {sorted(splits)}")

    episodes_by_split: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        episodes_by_split[str(row.get("split"))].add(str(row.get("episode_id")))
    overlap = episodes_by_split.get("train", set()) & episodes_by_split.get("test", set())
    if overlap:
        errors.append(f"episode leakage across train/test: {len(overlap)} overlapping episode ids")

    lengths = {(len(row.get("state_before", [])), len(row.get("state_after", []))) for row in rows}
    if len(lengths) != 1 or next(iter(lengths))[0] != next(iter(lengths))[1]:
        errors.append(f"state dimensions are inconsistent: {sorted(lengths)}")

    schema = (metadata or {}).get("state_schema")
    if not isinstance(schema, list) or not schema:
        errors.append(
            "typed state_schema is missing; flattened mixed SILG fields cannot use one global MSE"
        )
    else:
        covered: set[int] = set()
        for field in schema:
            kind = field.get("type")
            start, end = field.get("start"), field.get("end")
            if kind not in ALLOWED_TYPES:
                errors.append(f"invalid state field type: {kind!r}")
            if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
                errors.append(f"invalid state slice: {field}")
                continue
            covered.update(range(start, end))
        state_dim = len(rows[0].get("state_before", []))
        if covered != set(range(state_dim)):
            errors.append("typed state_schema does not exactly cover the flattened state vector")

    holdout_counts: dict[str, int] = {}
    transfer_support: dict[str, dict[str, Any]] = {}
    for key, policy in HOLDOUT_POLICY.items():
        count = sum(bool(row.get(key, False)) for row in rows if row.get("split") == "test")
        holdout_counts[key] = count
        declared = _declared_support(metadata, key)
        inferred = "supported" if count > 0 else "unsupported"
        effective = declared or inferred

        if policy == "required" and count == 0:
            errors.append(f"real test examples for required {key} are absent")
        elif policy == "conditional" and count == 0:
            if declared == "supported":
                errors.append(f"{key} is declared supported but has no real test examples")
            else:
                warnings.append(f"{key} transfer is unsupported; no generator-backed test examples")

        if count > 0 and declared == "unsupported":
            errors.append(f"{key} has test examples but metadata declares it unsupported")

        transfer_support[key] = {
            "policy": policy,
            "declared_status": declared,
            "effective_status": effective,
            "test_examples": count,
        }

    train_forms = {tuple(row.get("text_tokens", [])) for row in rows if row.get("split") == "train"}
    test_forms = {tuple(row.get("text_tokens", [])) for row in rows if row.get("split") == "test"}
    form_overlap = len(train_forms & test_forms)
    language_supported = transfer_support["language_holdout"]["effective_status"] == "supported"
    if language_supported and test_forms and form_overlap == len(test_forms):
        errors.append("language-form holdout is not demonstrated; every test token sequence occurs in train")

    action_counts = Counter(int(row.get("action", -1)) for row in rows if row.get("split") == "train")
    if len([a for a, n in action_counts.items() if n > 0]) < 3:
        errors.append(f"source-policy action collapse: train action counts={dict(action_counts)}")

    terminal_rows = [row for row in rows if bool(row.get("done", False))]
    wins = sum(float(row.get("reward", 0.0)) > 0.8 for row in terminal_rows)
    win_rate = wins / len(terminal_rows) if terminal_rows else 0.0
    if win_rate <= 0.0:
        errors.append("source policy has no successful terminal episodes")
    elif win_rate < 0.05:
        warnings.append(f"source policy competence is weak: terminal win rate={win_rate:.4f}")

    return {
        "status": "eligible" if not errors else "blocked",
        "classification": (
            "r02_fidelity_contract_passed" if not errors
            else "initial_reproduction_failure"
        ),
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "rows": len(rows),
            "episodes": len({str(row.get("episode_id")) for row in rows}),
            "seeds": sorted(seeds),
            "splits": sorted(splits),
            "actions_train": dict(sorted(action_counts.items())),
            "terminal_episodes": len(terminal_rows),
            "wins": wins,
            "win_rate": win_rate,
            "holdouts": holdout_counts,
            "train_language_forms": len(train_forms),
            "test_language_forms": len(test_forms),
            "overlapping_language_forms": form_overlap,
        },
        "transfer_support": transfer_support,
        "required_method_properties": {
            "discrete_message_default": True,
            "message_alignment_loss": True,
            "decoder_pretrained_before_language": True,
            "decoder_frozen_by_default": True,
            "typed_next_state_loss": True,
            "matched_parameter_budget": True,
            "matched_data_and_split": True,
            "online_task_success_required": True,
            "pretrained_language_model": False,
        },
        "capability_progress_claimed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = load_rows(args.data)
    metadata = json.loads(args.metadata.read_text()) if args.metadata else None
    result = audit(rows, metadata)
    result["data_path"] = str(args.data)
    result["data_sha256"] = sha256(args.data)
    if args.metadata:
        result["metadata_path"] = str(args.metadata)
        result["metadata_sha256"] = sha256(args.metadata)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "eligible" else 2)


if __name__ == "__main__":
    main()
