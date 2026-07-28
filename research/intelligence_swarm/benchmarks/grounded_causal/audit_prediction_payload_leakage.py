#!/usr/bin/env python3
"""Fail-closed audit for prediction-payload leakage and schema integrity.

The evaluation dataset may be clean while a prediction exporter still writes gold
labels, future states, rewards, completed trajectories, or invalid actions into the
prediction JSONL.  Those rows must not enter paired statistics or an accepted R0
bundle.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

REQUIRED_METHODS = {
    "correct",
    "random",
    "language_blind",
    "state_only",
    "target_label_shuffle",
    "outcome_shuffle",
}
FORBIDDEN_PREDICTION_KEYS = {
    "gold_action",
    "gold_state_after",
    "gold_inverse",
    "answer",
    "label",
    "reward",
    "done",
    "terminal_observation",
    "episode_return",
    "episode_success",
    "completed_trajectory",
    "rollout",
    "future_state",
    "next_state_gold",
    "oracle_action",
    "target_action",
}
ALLOWED_TOP_LEVEL = {
    "instance_id",
    "method",
    "instance_fingerprint",
    "pred_action",
    "pred_state_after",
    "pred_inverse",
    "control_source_instance_id",
    "control_source_fingerprint",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: row must be an object")
            rows.append(value)
    return rows


def _finite_json(value: Any) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _finite_json(item) for key, item in value.items())
    return False


def _action_is_valid(action: Any, mask: Any) -> bool:
    if mask is None:
        return True
    if not isinstance(action, int) or isinstance(action, bool):
        return False
    if isinstance(mask, list):
        return 0 <= action < len(mask) and bool(mask[action])
    if isinstance(mask, dict):
        return bool(mask.get(str(action), mask.get(action, False)))
    return False


def audit_rows(data: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    findings: list[dict[str, Any]] = []
    by_id = {str(row.get("instance_id")): row for row in data if row.get("instance_id") is not None}
    eval_ids = {
        iid for iid, row in by_id.items()
        if str(row.get("split", "")).lower() not in {"train", "training"}
    }
    seen: set[tuple[str, str]] = set()
    method_ids: dict[str, set[str]] = {method: set() for method in REQUIRED_METHODS}

    for row_no, row in enumerate(predictions, 1):
        missing = {"instance_id", "method", "instance_fingerprint", "pred_action", "pred_state_after"} - row.keys()
        if missing:
            errors.append(f"prediction row {row_no}: missing fields {sorted(missing)}")
            continue

        iid = str(row["instance_id"])
        method = str(row["method"])
        key = (iid, method)
        if key in seen:
            errors.append(f"prediction row {row_no}: duplicate instance/method {key}")
        seen.add(key)

        leaked = sorted(set(row) & FORBIDDEN_PREDICTION_KEYS)
        unexpected = sorted(set(row) - ALLOWED_TOP_LEVEL)
        if leaked:
            findings.append({"row": row_no, "instance_id": iid, "kind": "forbidden_gold_or_outcome_fields", "fields": leaked})
            errors.append(f"prediction row {row_no}: forbidden gold/outcome fields {leaked}")
        if unexpected:
            findings.append({"row": row_no, "instance_id": iid, "kind": "unregistered_prediction_fields", "fields": unexpected})
            errors.append(f"prediction row {row_no}: unregistered fields {unexpected}")

        if method not in REQUIRED_METHODS:
            errors.append(f"prediction row {row_no}: unexpected method {method}")
        else:
            method_ids[method].add(iid)

        gold = by_id.get(iid)
        if gold is None:
            errors.append(f"prediction row {row_no}: unknown instance_id={iid}")
            continue
        if iid not in eval_ids:
            errors.append(f"prediction row {row_no}: prediction supplied for train instance={iid}")

        if not _finite_json(row["pred_state_after"]):
            errors.append(f"prediction row {row_no}: pred_state_after contains non-finite or unsupported values")
        if not _finite_json(row.get("pred_inverse")):
            errors.append(f"prediction row {row_no}: pred_inverse contains non-finite or unsupported values")
        if not _action_is_valid(row["pred_action"], gold.get("valid_action_mask", gold.get("valid"))):
            errors.append(f"prediction row {row_no}: pred_action is outside the instance valid-action schema")

    for method in sorted(REQUIRED_METHODS):
        missing = eval_ids - method_ids[method]
        extra = method_ids[method] - eval_ids
        if missing:
            errors.append(f"method {method}: incomplete prediction coverage ({len(missing)} missing)")
        if extra:
            errors.append(f"method {method}: predictions outside evaluation set ({len(extra)} extra)")

    return {
        "valid": not errors,
        "errors": errors,
        "findings": findings,
        "prediction_rows": len(predictions),
        "expected_eval_instances": len(eval_ids),
        "required_methods": sorted(REQUIRED_METHODS),
        "forbidden_prediction_fields": sorted(FORBIDDEN_PREDICTION_KEYS),
        "strict_top_level_schema": True,
        "valid_action_schema_checked": True,
        "finite_prediction_values_checked": True,
        "classification": "qualified" if not errors else "initial_reproduction_failure",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("predictions", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit_rows(read_jsonl(args.data), read_jsonl(args.predictions))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"valid": False, "errors": [str(exc)], "classification": "initial_reproduction_failure"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
