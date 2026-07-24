#!/usr/bin/env python3
"""Run a deterministic, resource-audited smoke reproduction of SILG's official
`multi` recurrent baseline on RTFM S1.

This script does not introduce a new model. It applies the smallest explicit
reproducibility patch to the pinned public SILG source: actor RNG seeds are
made a deterministic function of an experiment seed instead of os.urandom().
The original and patched file hashes are recorded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
        run_exp.write_text(run_text, encoding="utf-8")

    after = {"exp_utils.py": sha256(exp_utils), "run_exp.py": sha256(run_exp)}
    return {
        "purpose": "replace actor os.urandom seed with deterministic experiment seed",
        "before_sha256": before,
        "after_sha256": after,
        "semantic_change": "actor_seed = experiment_seed * 1000003 + actor_index",
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


def run_seed(root: Path, output_dir: Path, seed: int, frames: int) -> dict[str, Any]:
    savedir = output_dir / "checkpoints"
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
        "--disable_checkpoint",
        "--entropy_cost", "0.05",
    ]
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=root, env=env, text=True, capture_output=True, timeout=1200)
    wall = time.perf_counter() - started
    combined = proc.stdout + "\n--- STDERR ---\n" + proc.stderr
    log_path.write_text(combined, encoding="utf-8")
    return {
        "seed": seed,
        "frames_requested": frames,
        "returncode": proc.returncode,
        "wall_seconds": wall,
        "resource": parse_time_v(proc.stderr),
        "command": cmd,
        "log": str(log_path),
        "log_sha256": sha256(log_path),
        "completed": proc.returncode == 0,
    }


def inspect_model(root: Path, output_dir: Path) -> dict[str, Any]:
    code = r'''
import json, sys, torch
sys.path.insert(0, sys.argv[1])
import exp_utils
from model.multi import Model
flags = exp_utils.get_parser().parse_args([])
flags.env = "silg:rtfm_train_s1-v0"
flags.val_env = "silg:rtfm_test_s1-v0"
flags.model = "multi"
flags.disable_cuda = True
env = Model.create_env(flags)
model = Model.make(flags, env)
params = sum(p.numel() for p in model.parameters())
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
path = sys.argv[2]
torch.save(model.state_dict(), path)
print(json.dumps({"parameters": params, "trainable_parameters": trainable, "state_dict_bytes": __import__('os').path.getsize(path)}))
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
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    patch = deterministic_patch(args.silg_root)
    model = inspect_model(args.silg_root, args.output)
    runs = [run_seed(args.silg_root, args.output, seed, args.frames) for seed in args.seeds]
    payload = {
        "status": "success" if all(r["completed"] for r in runs) else "failed",
        "classification": "official_recurrent_training_smoke_not_full_baseline_reproduction",
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
