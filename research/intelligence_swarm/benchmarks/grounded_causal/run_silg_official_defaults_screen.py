#!/usr/bin/env python3
"""One-factor R0.1 screen using SILG's pinned official execution defaults.

This does not change the model, data, seeds, split, frame request, optimizer, or
entropy coefficient.  It tests only the previously diagnosed execution-profile
mismatch: num_actors/batch_size/unroll_length/num_threads.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from run_silg_recurrent_smoke import (
    deterministic_patch,
    extract_final_model,
    inspect_model,
    parse_time_v,
    sha256,
)

OFFICIAL_PROFILE = {
    "num_actors": 30,
    "batch_size": 24,
    "unroll_length": 80,
    "num_threads": 4,
}
REFERENCE_REDUCED_PROFILE = {
    "num_actors": 2,
    "batch_size": 2,
    "unroll_length": 20,
    "num_threads": 1,
}


def timeout_seconds(frames: int) -> int:
    # The official profile has substantially more actor/learner concurrency than
    # the reduced CI profile. Keep a conservative per-seed ceiling.
    return max(2400, int(math.ceil(frames / 32768.0) * 900))


def run_seed(root: Path, output: Path, seed: int, frames: int, entropy_cost: float) -> dict[str, Any]:
    savedir = (output / f"official_defaults_exp_seed_{seed}").resolve()
    log_path = output / f"SILG_RTFM_RECURRENT_SEED_{seed}.log"
    cmd = [
        "/usr/bin/time", "-v", sys.executable, str(root / "run_exp.py"),
        "--env", "silg:rtfm_train_s1-v0",
        "--val_env", "silg:rtfm_test_s1-v0",
        "--model", "multi",
        "--xpid", f"rtfm-multi-r01-official-defaults-seed-{seed}",
        "--savedir", str(savedir),
        "--seed", str(seed),
        "--total_frames", str(frames),
        "--num_actors", str(OFFICIAL_PROFILE["num_actors"]),
        "--num_threads", str(OFFICIAL_PROFILE["num_threads"]),
        "--batch_size", str(OFFICIAL_PROFILE["batch_size"]),
        "--unroll_length", str(OFFICIAL_PROFILE["unroll_length"]),
        "--disable_cuda",
        "--entropy_cost", str(entropy_cost),
    ]
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(OFFICIAL_PROFILE["num_threads"])
    started = time.perf_counter()
    limit = timeout_seconds(frames)
    timed_out = False
    try:
        proc = subprocess.run(
            cmd,
            cwd=root,
            env=env,
            text=True,
            capture_output=True,
            timeout=limit,
        )
        stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        returncode = 124
        stderr += f"\nHARNESS TIMEOUT: exceeded {limit} seconds\n"
    wall = time.perf_counter() - started
    log_path.write_text(stdout + "\n--- STDERR ---\n" + stderr, encoding="utf-8")
    checkpoint = extract_final_model(savedir, output, seed) if returncode == 0 else {"completed": False}
    return {
        "seed": seed,
        "frames_requested": frames,
        "entropy_cost": entropy_cost,
        "execution_profile": OFFICIAL_PROFILE,
        "returncode": returncode,
        "wall_seconds": wall,
        "timeout_seconds": limit,
        "timed_out": timed_out,
        "resource": parse_time_v(stderr),
        "command": cmd,
        "log": str(log_path),
        "log_sha256": sha256(log_path),
        "checkpoint": checkpoint,
        "completed": returncode == 0 and checkpoint.get("completed", False),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silg-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 7, 19])
    parser.add_argument("--frames", type=int, default=131072)
    parser.add_argument("--entropy-cost", type=float, default=0.005, choices=[0.005])
    args = parser.parse_args()
    if args.seeds != [1, 7, 19]:
        raise SystemExit(f"canonical seeds required in order: [1, 7, 19], got {args.seeds}")
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    patch = deterministic_patch(args.silg_root)
    model = inspect_model(args.silg_root, args.output)
    runs = [run_seed(args.silg_root, args.output, s, args.frames, args.entropy_cost) for s in args.seeds]
    quantum = OFFICIAL_PROFILE["batch_size"] * OFFICIAL_PROFILE["unroll_length"]
    expected_checkpoint_frames = int(math.ceil(args.frames / quantum) * quantum)
    payload = {
        "status": "success" if all(r["completed"] for r in runs) else "failed",
        "classification": "official_recurrent_training_execution_profile_screen",
        "source_pins": {
            "silg": "2af07578e1264029a240fcfb78d4ac0aea16f5de",
            "rtfm": "58f17955595b5a127c96d045d896fcbcc7d4b570",
        },
        "environment": "silg:rtfm_train_s1-v0",
        "validation_environment": "silg:rtfm_test_s1-v0",
        "model": "official SILG multi recurrent",
        "pretrained_language_model": False,
        "seeds": args.seeds,
        "frames_per_seed": args.frames,
        "entropy_cost": args.entropy_cost,
        "screening_change": "official_actor_batch_unroll_thread_profile_only",
        "reference_reduced_profile": REFERENCE_REDUCED_PROFILE,
        "execution_profile": OFFICIAL_PROFILE,
        "learner_update_quantum_frames": quantum,
        "expected_checkpoint_frames": expected_checkpoint_frames,
        "determinism_patch": patch,
        "model_audit": model,
        "runs": runs,
        "total_wall_seconds": time.perf_counter() - started,
        "official_full_baseline_completed": False,
        "matched_controls_completed": False,
        "capability_progress_claimed": False,
    }
    out = args.output / "SILG_RTFM_RECURRENT_SMOKE_3SEED.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
