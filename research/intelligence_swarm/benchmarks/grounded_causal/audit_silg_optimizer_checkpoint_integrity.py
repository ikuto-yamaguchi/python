#!/usr/bin/env python3
"""Fail-closed SILG optimizer/checkpoint integrity audit.

This audit is artifact-only: it inspects preserved official ``job.tar`` files and
standalone model-state exports without retraining.  It verifies that each seed
contains restorable optimizer state, a finite frame counter, and a model state
identical to the separately exported state dict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Tuple

import torch


def _parse_seed_path(value: str) -> Tuple[int, Path]:
    try:
        seed_text, path_text = value.split("=", 1)
        seed = int(seed_text)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError("expected SEED=PATH") from exc
    path = Path(path_text)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"file does not exist: {path}")
    return seed, path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _first_mapping(payload: Mapping[str, Any], keys: Iterable[str]) -> Tuple[str | None, Mapping[str, Any] | None]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, Mapping):
            return key, value
    return None, None


def _frame_counter(payload: Mapping[str, Any]) -> Tuple[str | None, int | None]:
    for key in ("frames", "frame", "step", "steps", "num_frames", "total_frames"):
        value = payload.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            return key, int(value)
    return None, None


def _tensor_state_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> Tuple[bool, list[str]]:
    failures: list[str] = []
    left_keys = set(left)
    right_keys = set(right)
    if left_keys != right_keys:
        failures.append(
            f"model_key_mismatch missing={sorted(right_keys-left_keys)} extra={sorted(left_keys-right_keys)}"
        )
        return False, failures
    for key in sorted(left_keys):
        lhs, rhs = left[key], right[key]
        if torch.is_tensor(lhs) and torch.is_tensor(rhs):
            if lhs.shape != rhs.shape or lhs.dtype != rhs.dtype or not torch.equal(lhs.cpu(), rhs.cpu()):
                failures.append(f"model_tensor_mismatch:{key}")
        elif lhs != rhs:
            failures.append(f"model_value_mismatch:{key}")
    return not failures, failures


def _audit_one(seed: int, checkpoint_path: Path, model_state_path: Path, min_frames: int) -> Dict[str, Any]:
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    exported_model = torch.load(model_state_path, map_location="cpu")
    failures: list[str] = []
    if not isinstance(checkpoint, Mapping):
        return {"seed": seed, "status": "rejected", "failures": ["checkpoint_not_mapping"]}
    if not isinstance(exported_model, Mapping):
        return {"seed": seed, "status": "rejected", "failures": ["exported_model_not_mapping"]}

    model_key, checkpoint_model = _first_mapping(
        checkpoint, ("model_state_dict", "model_state", "model", "state_dict")
    )
    optimizer_key, optimizer = _first_mapping(
        checkpoint, ("optimizer_state_dict", "optimizer_state", "optimizer")
    )
    frame_key, frames = _frame_counter(checkpoint)

    if checkpoint_model is None:
        failures.append("missing_checkpoint_model_state")
    if optimizer is None:
        failures.append("missing_optimizer_state")
    else:
        state = optimizer.get("state")
        groups = optimizer.get("param_groups")
        if not isinstance(state, Mapping) or len(state) == 0:
            failures.append("optimizer_state_empty")
        if not isinstance(groups, list) or len(groups) == 0:
            failures.append("optimizer_param_groups_empty")
    if frames is None:
        failures.append("missing_frame_counter")
    elif frames < min_frames:
        failures.append(f"frame_counter_below_budget:{frames}<{min_frames}")

    model_equal = False
    if checkpoint_model is not None:
        model_equal, model_failures = _tensor_state_equal(checkpoint_model, exported_model)
        failures.extend(model_failures)

    return {
        "seed": seed,
        "status": "accepted" if not failures else "rejected",
        "checkpoint": str(checkpoint_path),
        "checkpoint_bytes": checkpoint_path.stat().st_size,
        "checkpoint_sha256": _sha256(checkpoint_path),
        "model_state": str(model_state_path),
        "model_state_bytes": model_state_path.stat().st_size,
        "model_state_sha256": _sha256(model_state_path),
        "checkpoint_top_level_keys": sorted(map(str, checkpoint.keys())),
        "model_key": model_key,
        "optimizer_key": optimizer_key,
        "frame_key": frame_key,
        "frames": frames,
        "model_state_exact_match": model_equal,
        "optimizer_state_entries": len(optimizer.get("state", {})) if optimizer is not None else 0,
        "optimizer_param_groups": len(optimizer.get("param_groups", [])) if optimizer is not None else 0,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", action="append", required=True, type=_parse_seed_path)
    parser.add_argument("--model-state", action="append", required=True, type=_parse_seed_path)
    parser.add_argument("--min-frames", type=int, default=131072)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    checkpoints = dict(args.checkpoint)
    model_states = dict(args.model_state)
    expected = {1, 7, 19}
    failures: list[str] = []
    if set(checkpoints) != expected:
        failures.append(f"checkpoint_seed_set:{sorted(checkpoints)}")
    if set(model_states) != expected:
        failures.append(f"model_state_seed_set:{sorted(model_states)}")

    results = []
    for seed in sorted(expected & set(checkpoints) & set(model_states)):
        results.append(_audit_one(seed, checkpoints[seed], model_states[seed], args.min_frames))
    for result in results:
        failures.extend(f"seed_{result['seed']}:{item}" for item in result["failures"])

    payload = {
        "status": "accepted" if not failures else "rejected",
        "classification": "silg_optimizer_checkpoint_restore_integrity",
        "artifact_only": True,
        "expected_seeds": sorted(expected),
        "minimum_frames": args.min_frames,
        "results": results,
        "failures": failures,
        "capability_progress_claimed": False,
        "new_intelligence_principle_claimed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
