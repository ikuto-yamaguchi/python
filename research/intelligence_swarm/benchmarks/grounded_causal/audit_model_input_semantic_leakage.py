#!/usr/bin/env python3
"""Fail-closed semantic leakage audit for grounded-causal model inputs.

This companion audit covers alias/value leakage that key-name checks in
``evaluation_contract.py`` cannot reliably detect.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

FUTURE_OR_OUTCOME_TOKENS = {
    "future", "next_state", "after_state", "state_after", "post_treatment",
    "trajectory", "rollout", "terminal", "reward", "return_to_go",
    "episode_return", "success", "outcome", "oracle", "answer", "gold",
}
CURRENT_ACTION_ALIASES = {
    "gold_action", "target_action", "correct_action", "chosen_action",
    "oracle_action", "next_action", "action_label",
}
SAFE_TOP_LEVEL_INPUTS = {
    "utterance", "state_before", "history", "valid_action_mask",
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


def adapt_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if "gold_action" not in out and "action" in out:
        out["gold_action"] = out["action"]
    if "gold_state_after" not in out and "state_after" in out:
        out["gold_state_after"] = out["state_after"]
    if "model_input_fields" not in out:
        out["model_input_fields"] = [
            key for key in ("utterance", "state_before", "history", "valid_action_mask")
            if key in out
        ]
    if "model_input" not in out:
        out["model_input"] = {
            key: out[key] for key in out["model_input_fields"] if key in out
        }
    return out


def _normalized_key(key: Any) -> str:
    return str(key).strip().lower().replace("-", "_").replace(" ", "_")


def _walk(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, nested in value.items():
            yield from _walk(nested, path + (_normalized_key(key),))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _walk(nested, path + (f"[{index}]",))


def _path_text(path: tuple[str, ...]) -> str:
    return ".".join(path)


def _has_future_or_outcome_alias(path: tuple[str, ...]) -> bool:
    text = _path_text(path)
    return any(token in text for token in FUTURE_OR_OUTCOME_TOKENS)


def _has_current_action_alias(path: tuple[str, ...]) -> bool:
    text = _path_text(path)
    return any(alias in text for alias in CURRENT_ACTION_ALIASES)


def audit_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    findings: list[dict[str, Any]] = []
    audited = 0

    for row_no, raw in enumerate(rows, 1):
        row = adapt_row(raw)
        missing = {"instance_id", "gold_action", "gold_state_after", "model_input"} - row.keys()
        if missing:
            errors.append(f"row {row_no}: missing fields {sorted(missing)}")
            continue

        audited += 1
        iid = str(row["instance_id"])
        model_input = row["model_input"]
        if not isinstance(model_input, dict):
            errors.append(f"row {row_no}: model_input must be an object")
            continue

        gold_after = row["gold_state_after"]
        gold_action = row["gold_action"]
        state_before = row.get("state_before")
        row_findings: set[tuple[str, str]] = set()

        for path, value in _walk(model_input):
            if not path:
                continue
            text = _path_text(path)

            if _has_future_or_outcome_alias(path):
                row_findings.add(("future_or_outcome_alias", text))

            if _has_current_action_alias(path) and value == gold_action:
                row_findings.add(("gold_action_value_under_alias", text))

            top = path[0]
            if (
                value == gold_after
                and gold_after != state_before
                and top not in SAFE_TOP_LEVEL_INPUTS
            ):
                row_findings.add(("gold_after_value_match", text))

        for kind, path in sorted(row_findings):
            findings.append({"row": row_no, "instance_id": iid, "kind": kind, "path": path})
            errors.append(f"row {row_no} instance={iid}: {kind} at model_input.{path}")

    return {
        "valid": not errors,
        "errors": errors,
        "findings": findings,
        "rows": len(rows),
        "rows_audited": audited,
        "semantic_alias_audit": True,
        "gold_after_value_audit": True,
        "gold_action_alias_value_audit": True,
        "completed_trajectory_alias_audit": True,
        "classification": "qualified" if not errors else "initial_reproduction_failure",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit_rows(read_jsonl(args.data))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "valid": False,
            "errors": [str(exc)],
            "classification": "initial_reproduction_failure",
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
