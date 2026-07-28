#!/usr/bin/env python3
"""Fail-closed auditor for the pre-100M SILG infrastructure qualification.

This is not a capability gate.  It checks whether the runner can execute the
pinned official sampling contract for a short segment and preserve enough state
to justify a later full public reproduction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

import torch


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def first_mapping(payload: Mapping[str, Any], keys: tuple[str, ...]) -> tuple[str | None, Mapping[str, Any] | None]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, Mapping):
            return key, value
    return None, None


def frame_counter(payload: Mapping[str, Any]) -> tuple[str | None, int | None]:
    for key in ("frames", "frame", "step", "steps", "num_frames", "total_frames"):
        value = payload.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            return key, int(value)
    return None, None


def exact_model_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if set(left) != set(right):
        failures.append("model_key_set_mismatch")
        return False, failures
    for key in sorted(left):
        a, b = left[key], right[key]
        if torch.is_tensor(a) and torch.is_tensor(b):
            if a.shape != b.shape or a.dtype != b.dtype or not torch.equal(a.cpu(), b.cpu()):
                failures.append(f"model_tensor_mismatch:{key}")
        elif a != b:
            failures.append(f"model_value_mismatch:{key}")
    return not failures, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--model-state", type=Path, required=True)
    parser.add_argument("--training-summary", type=Path, required=True)
    parser.add_argument("--minimum-frames", type=int, required=True)
    parser.add_argument("--official-total-frames", type=int, default=100_000_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    failures: list[str] = []
    for path, label in (
        (args.checkpoint, "checkpoint"),
        (args.model_state, "model_state"),
        (args.training_summary, "training_summary"),
    ):
        if not path.is_file():
            failures.append(f"missing_{label}:{path}")

    if failures:
        payload = {
            "status": "rejected",
            "classification": "official_contract_infrastructure_qualification",
            "failures": failures,
            "capability_progress_claimed": False,
            "new_intelligence_principle_claimed": False,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    checkpoint = torch.load(args.checkpoint, map_location="cpu")
    exported = torch.load(args.model_state, map_location="cpu")
    summary = json.loads(args.training_summary.read_text(encoding="utf-8"))
    if not isinstance(checkpoint, Mapping):
        failures.append("checkpoint_not_mapping")
        checkpoint = {}
    if not isinstance(exported, Mapping):
        failures.append("model_state_not_mapping")
        exported = {}

    model_key, model = first_mapping(checkpoint, ("model_state_dict", "model_state", "model", "state_dict"))
    optimizer_key, optimizer = first_mapping(checkpoint, ("optimizer_state_dict", "optimizer_state", "optimizer"))
    scheduler_key, scheduler = first_mapping(checkpoint, ("scheduler_state_dict", "scheduler_state", "scheduler"))
    frame_key, frames = frame_counter(checkpoint)

    if model is None:
        failures.append("missing_model_state")
    if optimizer is None:
        failures.append("missing_optimizer_state")
    else:
        if not isinstance(optimizer.get("state"), Mapping) or not optimizer.get("state"):
            failures.append("optimizer_state_empty")
        if not isinstance(optimizer.get("param_groups"), list) or not optimizer.get("param_groups"):
            failures.append("optimizer_param_groups_empty")
    if frames is None:
        failures.append("missing_frame_counter")
    elif frames < args.minimum_frames:
        failures.append(f"frame_counter_below_segment:{frames}<{args.minimum_frames}")

    model_equal = False
    if model is not None and exported:
        model_equal, equality_failures = exact_model_equal(model, exported)
        failures.extend(equality_failures)

    runs = summary.get("runs", []) if isinstance(summary, Mapping) else []
    command = runs[0].get("command", []) if runs else []
    command = [str(value) for value in command]
    required_pairs = {
        "--model": "multi",
        "--num_actors": "30",
        "--num_threads": "4",
        "--batch_size": "24",
        "--unroll_length": "80",
    }
    for flag, expected in required_pairs.items():
        if flag not in command:
            failures.append(f"missing_command_flag:{flag}")
        elif command[command.index(flag) + 1] != expected:
            failures.append(f"command_value_mismatch:{flag}")
    if "--stateful" in command:
        failures.append("official_stateful_default_violated")
    if "--learning_rate" in command:
        failures.append("official_learning_rate_default_overridden")

    resource = runs[0].get("resource", {}) if runs else {}
    wall_seconds = float(runs[0].get("wall_seconds", 0.0)) if runs else 0.0
    completed_frames = int(frames or 0)
    throughput = completed_frames / wall_seconds if wall_seconds > 0 else None
    projected_seconds = args.official_total_frames / throughput if throughput else None

    resume_fields = {
        "rng_state_present": any(key in checkpoint for key in ("rng_state", "rng_states", "random_state")),
        "batch_state_present": any(key in checkpoint for key in ("batch", "batch_state", "learner_batch")),
        "scheduler_state_present": scheduler is not None,
    }
    if not resume_fields["rng_state_present"]:
        failures.append("missing_rng_state_for_one_step_resume_equivalence")
    if not resume_fields["batch_state_present"]:
        failures.append("missing_batch_state_for_one_step_resume_equivalence")

    payload = {
        "status": "accepted" if not failures else "rejected",
        "classification": "official_contract_infrastructure_qualification",
        "capability_evidence": False,
        "checkpoint": {
            "path": str(args.checkpoint),
            "bytes": args.checkpoint.stat().st_size,
            "sha256": sha256(args.checkpoint),
            "top_level_keys": sorted(map(str, checkpoint.keys())),
            "model_key": model_key,
            "optimizer_key": optimizer_key,
            "scheduler_key": scheduler_key,
            "frame_key": frame_key,
            "frames": frames,
            "model_state_exact_match": model_equal,
            "optimizer_state_entries": len(optimizer.get("state", {})) if optimizer is not None else 0,
            "optimizer_param_groups": len(optimizer.get("param_groups", [])) if optimizer is not None else 0,
        },
        "official_command_contract": {
            "model": "multi",
            "stateful": False,
            "num_actors": 30,
            "num_threads": 4,
            "batch_size": 24,
            "unroll_length": 80,
            "learning_rate": 0.0005,
            "optimizer": "RMSprop",
            "gradient_clip_norm": 40.0,
        },
        "resource": {
            "segment_frames": completed_frames,
            "wall_seconds": wall_seconds,
            "peak_rss_kib": resource.get("peak_rss_kib"),
            "frames_per_second": throughput,
            "projected_100m_seconds": projected_seconds,
            "projected_100m_days": projected_seconds / 86400.0 if projected_seconds else None,
        },
        "resume_equivalence_prerequisites": resume_fields,
        "one_step_resume_equivalence_verified": False,
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
