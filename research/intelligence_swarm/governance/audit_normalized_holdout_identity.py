#!/usr/bin/env python3
"""Fail-closed Unicode/representation-normalized entity/dynamics holdout audit.

This closes a direct leakage path where semantically identical entity or dynamics
identities can cross train/evaluation splits by changing Unicode width, case,
whitespace/control characters, or structured-value representation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any

from research.intelligence_swarm.benchmarks.grounded_causal.evaluation_contract import adapt_dataset, read_jsonl

EVAL_SPLITS = {"test", "eval", "validation", "valid"}


def _canonical_string(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    return "".join(
        ch for ch in text
        if not ch.isspace() and unicodedata.category(ch) not in {"Cf", "Cc"}
    )


def canonical_identity(value: Any) -> Any:
    """Return a deterministic representation robust to cosmetic identity aliases."""
    if value is None:
        return ["null"]
    if isinstance(value, bool):
        return ["bool", value]
    if isinstance(value, (str, int, float)):
        # Scalar IDs such as 1 and "１" must not evade split isolation.
        return ["scalar", _canonical_string(value)]
    if isinstance(value, (list, tuple)):
        return ["sequence", [canonical_identity(item) for item in value]]
    if isinstance(value, dict):
        # Use a sorted pair list rather than a dict so alias-colliding keys remain visible.
        pairs = [
            [_canonical_string(key), canonical_identity(item)]
            for key, item in value.items()
        ]
        pairs.sort(key=lambda pair: json.dumps(pair, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return ["mapping", pairs]
    return ["scalar", _canonical_string(value)]


def normalized_signature(value: Any) -> str:
    payload = json.dumps(
        canonical_identity(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _identity_value(row: dict[str, Any], name: str) -> tuple[Any | None, str | None]:
    for key in (f"{name}_id", f"{name}_signature"):
        if row.get(key) is not None:
            return row[key], key
    return None, None


def _declares_holdout(row: dict[str, Any], name: str) -> bool:
    key = f"{name}_holdout"
    raw = unicodedata.normalize("NFKC", str(row.get("condition", ""))).casefold()
    parts = {
        part for part in raw.replace("+", " ").replace(",", " ").replace("|", " ").split()
        if part
    }
    flag = row.get(key)
    return key in parts or flag is True or flag == 1 or str(flag).casefold() == "true"


def audit_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    adapted = adapt_dataset(rows)
    errors: list[str] = []
    findings: list[dict[str, Any]] = []
    train_signatures: dict[str, dict[str, list[str]]] = {
        "entity": {},
        "dynamics": {},
    }

    for row in adapted:
        if str(row.get("split", "")).casefold() != "train":
            continue
        iid = str(row.get("instance_id", ""))
        for name in ("entity", "dynamics"):
            value, source = _identity_value(row, name)
            if source is None:
                continue
            signature = normalized_signature(value)
            train_signatures[name].setdefault(signature, []).append(iid)

    checked = 0
    for index, row in enumerate(adapted, 1):
        split = unicodedata.normalize("NFKC", str(row.get("split", ""))).casefold()
        if split not in EVAL_SPLITS:
            continue
        for name in ("entity", "dynamics"):
            if not _declares_holdout(row, name):
                continue
            checked += 1
            value, source = _identity_value(row, name)
            finding: dict[str, Any] = {
                "row": index,
                "instance_id": str(row.get("instance_id", "")),
                "split": split,
                "condition": str(row.get("condition", "")),
                "holdout": name,
                "identity_source": source,
            }
            if source is None:
                finding["signature_present"] = False
                findings.append(finding)
                errors.append(
                    f"row {index}: explicit {name}_holdout requires {name}_id or {name}_signature"
                )
                continue
            signature = normalized_signature(value)
            overlapping = train_signatures[name].get(signature, [])
            finding.update(
                {
                    "signature_present": True,
                    "normalized_signature": signature,
                    "overlaps_train": bool(overlapping),
                    "train_instance_ids": overlapping[:10],
                }
            )
            findings.append(finding)
            if overlapping:
                errors.append(
                    f"row {index}: normalized {name}_holdout leakage; "
                    f"equivalent train identities={overlapping[:5]}"
                )

    return {
        "valid": not errors,
        "classification": "qualified" if not errors else "initial_reproduction_failure",
        "errors": errors,
        "checked_holdout_rows": checked,
        "findings": findings,
        "normalization": "recursive NFKC + casefold + remove whitespace/control-format; scalar numeric/string aliases collapse",
        "entity_dynamics_normalized_split_isolation_required": True,
        "train_unique_normalized_signatures": {
            name: len(signatures) for name, signatures in train_signatures.items()
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_rows(read_jsonl(args.dataset))
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
