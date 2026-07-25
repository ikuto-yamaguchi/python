#!/usr/bin/env python3
"""Deterministic, resource-audited reproduction of SILG's official `multi`
recurrent learner on RTFM S1.

No model architecture is changed. The only external-source patch makes actor
and evaluation RNGs deterministic functions of the declared experiment seed.
The official Train class still performs the learning and final checkpoint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def deterministic_patch(root: Path) -> dict[str, Any]:
    exp_utils = root / "exp_utils.py"
    run_exp = root / "run_exp.py"
    before = {"exp_utils.py": sha256(exp_utils), "run_exp.py": sha256(run_exp)}

    parser_text = exp_utils.read_text(encoding="utf-8")
    seed_arg = "    parser.add_argument('--seed', default=0, type=int, help='deterministic experiment seed')\n"
    anchor = "    parser.add_argument('--random_agent', action='store_true',\n"
    if "--seed" not in parser_text:
        if anchor not in parser_text:
            raise RuntimeError("exp_utils.py parser anchor not found")
        parser_text = parser_text.replace(anchor, seed_arg + anchor, 1)
        exp_utils.write_text(parser_text, encoding="utf-8")

    run_text = run_exp.read_text(encoding="utf-8")
    old = "seed = i ^ int.from_bytes(os.urandom(4), byteorder='little')"
    new = "seed = int(flags.seed) * 1000003 + i"
    if new not in run_text:
        if old not in run_text:
            raise RuntimeError("run_exp.py actor seed anchor not found")
        run_text = run_text.replace(old, new, 1)

    eval_anchor = "    gym_env = Net.create_env(flags)\n    env = environment.Environment(gym_env)"
    eval_patch = (
        "    gym_env = Net.create_env(flags)\n"
        "    eval_seed = int(getattr(flags, 'seed', 0))\n"
        "    gym_env.seed(eval_seed)\n"
        "    np.random.seed(eval_seed)\n"
        "    random.seed(eval_seed)\n"
        "    torch.manual_seed(eval_seed)\n"
        "    env = environment.Environment(gym_env)"
    )
    if eval_patch not in run_text:
        if eval_anchor not in run_text:
            raise RuntimeError("run_exp.py test seed anchor not found")
        run_text = run_text.replace(eval_anchor, eval_patch, 1)
    run_exp.write_text(run_text, encoding="utf-8")

    after = {"exp_utils.py": sha256(exp_utils), "run_exp.py": sha256(run_exp)}
    return {
        "purpose": "deterministic actor and validation RNGs",
        "before_sha256": before,
        "after_sha256": after,
        "semantic_changes": [
            "actor_seed = experiment_seed * 1000003 + actor_index",
            "validation env/python/numpy/torch seed = experiment_seed",
        ],
    }


def parse_time_v(stderr: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    patterns = {
        "peak_rss_kib": r"Maximum resident set size \(kbytes\):\s*(\d+)",
        "user_seconds": r"User time \(seconds\):\s*([0-9.]+)",
        "system_seconds": r"System time \(seconds\):\s*([0-9.]+)",
        "exit_status": r"Exit status:\s*(\d+)",
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, stderr)
        if m:
            out[key] = int(m.group(1)) if key in {"peak_rss_kib", "exit_status"} else float(m.group(1))
    return out


def extract_final_model(savedir: Path, output_dir: Path, seed: int) -> dict[str, Any]:
    import torch

    candidates = sorted(savedir.rglob("job.tar"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        return {"completed": False, "error": f"no final job.tar under {savedir}"}
    checkpoint = candidates[-1]
    payload = torch.load(str(checkpoint), map_location="cpu")
    if not isinstance(payload, dict) or "model_state_dict" not in payload:
        return {"completed": False, "error": f"unexpected checkpoint schema: {type(payload).__name__}"}
    model_path = output_dir / f"SILG_RTFM_TRAINED_STATE_SEED_{seed}.pt"
    torch.save(payload["model_state_dict"], str(model_path))
    result = {
        "completed": True,
        "official_checkpoint": str(checkpoint),
        "official_checkpoint_bytes": checkpoint.stat().st_size,
        "official_checkpoint_sha256": sha256(checkpoint),
        "model_state_path": str(model_path),
        "model_state_bytes": model_path.stat().st_size,
        "model_state_sha256": sha256(model_path),
        "frames_in_checkpoint": int(payload.get("frames", -1)),
    }
    shutil.rmtree(savedir, ignore_errors=True)
    return result


def default_seed_timeout_seconds(frames: int) -> int:
    """Scale the process timeout with the declared training budget.

    The previous fixed 1,200-second limit was sufficient for 32,768 frames but
    killed the unchanged official learner at 131,072 frames before completion.
    This is a harness-only resource bound; it does not alter training behavior.
    """
    return max(1200, int(math.ceil(frames / 32768.0) * 600))


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def run_seed(
    root: Path,
    output_dir: Path,
    seed: int,
    frames: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    savedir = (output_dir / f"official_exp_seed_{seed}").resolve()
    xpid = f"rtfm-multi-r01-smoke-seed-{seed}"
    log_path = output_dir / f"SILG_RTFM_RECURRENT_SEED_{seed}.log"
    cmd = [
        "/usr/bin/time", "-v", sys.executable, str(root / "run_exp.py"),
        "--env", "silg:rtfm_train_s1-v0",
        "--val_env", "silg:rtfm_test_s1-v0",
        "--model", "multi",
        "--xpid", xpid,
        "--savedir", str(savedir),
        "--seed", str(seed),
        "--total_frames", str(frames),
        "--num_actors", "2",
        "--num_threads", "1",
        "--batch_size", "2",
        "--unroll_length", "20",
        "--disable_cuda",
        "--entropy_cost", "0.05",
    ]
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    started = time.perf_counter()
    timed_out = False
    timeout_error = None
    try:
        proc = subprocess.run(
            cmd,
            cwd=root,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = _as_text(exc.stdout)
        stderr = _as_text(exc.stderr)
        returncode = 124
        timeout_error = f"training process exceeded {timeout_seconds} seconds"
    wall = time.perf_counter() - started
    combined = stdout + "\n--- STDERR ---\n" + stderr
    if timeout_error:
        combined += "\n--- HARNESS ERROR ---\n" + timeout_error + "\n"
    log_path.write_text(combined, encoding="utf-8")
    checkpoint = extract_final_model(savedir, output_dir, seed) if returncode == 0 else {"completed": False}
    return {
        "seed": seed,
        "frames_requested": frames,
        "returncode": returncode,
        "wall_seconds": wall,
        "timeout_seconds": timeout_seconds,
        "timed_out": timed_out,
        "error": timeout_error,
        "resource": parse_time_v(stderr),
        "command": cmd,
        "log": str(log_path),
        "log_sha256": sha256(log_path),
        "checkpoint": checkpoint,
        "completed": returncode == 0 and checkpoint.get("completed", False),
    }


def inspect_model(root: Path, output_dir: Path) -> dict[str, Any]:
    code = r'''
import json, os, sys, time, torch
sys.path.insert(0, sys.argv[1])
import exp_utils
from silg import envs as _registered_envs
from model.multi import Model
flags = exp_utils.get_parser().parse_args([])
flags.env = "silg:rtfm_train_s1-v0"; flags.val_env = "silg:rtfm_test_s1-v0"
flags.model = "multi"; flags.disable_cuda = True
env = Model.create_env(flags); model = Model.make(flags, env).eval()
params = sum(p.numel() for p in model.parameters())
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
path = sys.argv[2]; torch.save(model.state_dict(), path)
obs = env.reset(); batch = {k: torch.as_tensor(v).unsqueeze(0).unsqueeze(0) for k,v in obs.items()}
batch.update({"reward":torch.zeros(1,1),"done":torch.zeros(1,1,dtype=torch.bool),"episode_return":torch.zeros(1,1),"episode_step":torch.zeros(1,1,dtype=torch.int32),"last_action":torch.zeros(1,1,dtype=torch.int64)})
state=model.initial_state(1)
with torch.no_grad():
  for _ in range(10): model(batch,state)
  t0=time.perf_counter_ns()
  for _ in range(100): model(batch,state)
  latency=(time.perf_counter_ns()-t0)/100/1e6
print(json.dumps({"parameters":params,"trainable_parameters":trainable,"state_dict_bytes":os.path.getsize(path),"cpu_forward_latency_ms_per_step":latency}))
env.close()
'''
    model_path = output_dir / "SILG_RTFM_MULTI_UNTRAINED_STATE_DICT.pt"
    proc = subprocess.run([sys.executable, "-c", code, str(root), str(model_path)], text=True, capture_output=True, timeout=180)
    if proc.returncode != 0:
        return {"completed": False, "error": proc.stderr[-4000:]}
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    payload.update({"completed": True, "state_dict_sha256": sha256(model_path)})
    return payload


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--silg-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seeds", type=int, nargs="+", default=[1, 7, 19])
    p.add_argument("--frames", type=int, default=2048)
    p.add_argument(
        "--seed-timeout-seconds",
        type=int,
        default=None,
        help="per-seed learner timeout; default scales with --frames",
    )
    args = p.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    timeout_seconds = args.seed_timeout_seconds or default_seed_timeout_seconds(args.frames)
    started = time.perf_counter()
    patch = deterministic_patch(args.silg_root)
    model = inspect_model(args.silg_root, args.output)
    runs = [
        run_seed(args.silg_root, args.output, seed, args.frames, timeout_seconds)
        for seed in args.seeds
    ]
    payload = {
        "status": "success" if all(r["completed"] for r in runs) else "failed",
        "classification": "official_recurrent_training_checkpoint_smoke_not_full_baseline_reproduction",
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
        "seed_timeout_seconds": timeout_seconds,
        "determinism_patch": patch,
        "model_audit": model,
        "runs": runs,
        "total_wall_seconds": time.perf_counter() - started,
        "official_full_baseline_completed": False,
        "matched_controls_completed": False,
        "capability_progress_claimed": False,
    }
    summary = args.output / "SILG_RTFM_RECURRENT_SMOKE_3SEED.json"
    summary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
