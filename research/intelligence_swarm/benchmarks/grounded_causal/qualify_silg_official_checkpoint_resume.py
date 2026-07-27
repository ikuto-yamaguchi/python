#!/usr/bin/env python3
"""Qualify SILG RTFM's official checkpoint/resume path without claiming capability.

This is deliberately an infrastructure test, not a public benchmark run. It
uses the pinned official model and parser defaults, runs two learner updates,
clones the complete experiment directory, resumes both clones for at least one
additional update, and checks checkpoint schema and state advancement. The
complete ``job.tar`` files are preserved for immutable artifact upload.

The official profile uses 30 actor processes and four learner threads. Their
queue/thread interleaving is not guaranteed to be bitwise deterministic, even
when actor RNG seeds are fixed. Therefore exact A/B tensor equality is recorded
as a diagnostic, but is not an infrastructure qualification requirement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import torch

OFFICIAL = {
    "env": "silg:rtfm_train_s1-v0",
    "val_env": "silg:rtfm_test_s1-v0",
    "model": "multi",
    "stateful": False,
    "num_actors": 30,
    "num_threads": 4,
    "batch_size": 24,
    "unroll_length": 80,
    "learning_rate": 0.0005,
    "entropy_cost": 0.05,
    "total_frames": 100_000_000,
}
FRAMES_PER_UPDATE = OFFICIAL["batch_size"] * OFFICIAL["unroll_length"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def patch_deterministic_seed(root: Path) -> dict[str, Any]:
    exp_utils = root / "exp_utils.py"
    run_exp = root / "run_exp.py"
    before = {p.name: sha256(p) for p in (exp_utils, run_exp)}
    parser_text = exp_utils.read_text(encoding="utf-8")
    seed_arg = "    parser.add_argument('--seed', default=0, type=int, help='deterministic experiment seed')\n"
    anchor = "    parser.add_argument('--random_agent', action='store_true',\n"
    if "--seed" not in parser_text:
        if anchor not in parser_text:
            raise RuntimeError("exp_utils.py seed parser anchor not found")
        exp_utils.write_text(parser_text.replace(anchor, seed_arg + anchor, 1), encoding="utf-8")
    run_text = run_exp.read_text(encoding="utf-8")
    old = "seed = i ^ int.from_bytes(os.urandom(4), byteorder='little')"
    new = "seed = int(flags.seed) * 1000003 + i"
    if new not in run_text:
        if old not in run_text:
            raise RuntimeError("run_exp.py actor seed anchor not found")
        run_exp.write_text(run_text.replace(old, new, 1), encoding="utf-8")
    after = {p.name: sha256(p) for p in (exp_utils, run_exp)}
    return {
        "before_sha256": before,
        "after_sha256": after,
        "semantic_change": "actor_seed = experiment_seed * 1000003 + actor_index",
    }


def parse_time_v(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, pattern, cast in (
        ("peak_rss_kib", r"Maximum resident set size \(kbytes\):\s*(\d+)", int),
        ("user_seconds", r"User time \(seconds\):\s*([0-9.]+)", float),
        ("system_seconds", r"System time \(seconds\):\s*([0-9.]+)", float),
        ("exit_status", r"Exit status:\s*(\d+)", int),
    ):
        m = re.search(pattern, text)
        if m:
            out[key] = cast(m.group(1))
    return out


def command(root: Path, savedir: Path, xpid: str, seed: int, total_frames: int) -> list[str]:
    return [
        "/usr/bin/time", "-v", sys.executable, str(root / "run_exp.py"),
        "--env", OFFICIAL["env"], "--val_env", OFFICIAL["val_env"],
        "--model", OFFICIAL["model"], "--xpid", xpid, "--savedir", str(savedir),
        "--seed", str(seed), "--total_frames", str(total_frames),
        "--num_actors", str(OFFICIAL["num_actors"]),
        "--num_threads", str(OFFICIAL["num_threads"]),
        "--batch_size", str(OFFICIAL["batch_size"]),
        "--unroll_length", str(OFFICIAL["unroll_length"]),
        "--learning_rate", str(OFFICIAL["learning_rate"]),
        "--entropy_cost", str(OFFICIAL["entropy_cost"]), "--disable_cuda",
    ]


def run(cmd: list[str], cwd: Path, log: Path, timeout: int) -> dict[str, Any]:
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    started = time.perf_counter()
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)
        stdout, stderr, code, timed_out = proc.stdout, proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else (exc.stdout or b"").decode(errors="replace")
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else (exc.stderr or b"").decode(errors="replace")
        code, timed_out = 124, True
    wall = time.perf_counter() - started
    log.write_text(stdout + "\n--- STDERR ---\n" + stderr, encoding="utf-8")
    return {
        "command": cmd,
        "returncode": code,
        "timed_out": timed_out,
        "wall_seconds": wall,
        "resource": parse_time_v(stderr),
        "log": str(log),
        "log_sha256": sha256(log),
    }


def locate_job(savedir: Path) -> Path:
    jobs = sorted(savedir.rglob("job.tar"), key=lambda p: p.stat().st_mtime)
    if len(jobs) != 1:
        raise RuntimeError(f"expected exactly one job.tar under {savedir}, found {len(jobs)}")
    return jobs[0]


def tensor_digest(value: Any) -> str:
    h = hashlib.sha256()
    if isinstance(value, dict):
        for key in sorted(value):
            h.update(str(key).encode())
            h.update(tensor_digest(value[key]).encode())
    elif isinstance(value, (list, tuple)):
        for item in value:
            h.update(tensor_digest(item).encode())
    elif torch.is_tensor(value):
        h.update(str(value.dtype).encode())
        h.update(str(tuple(value.shape)).encode())
        h.update(value.detach().cpu().contiguous().numpy().tobytes())
    else:
        h.update(repr(value).encode())
    return h.hexdigest()


def structure_digest(value: Any) -> str:
    """Digest container topology, tensor dtype and shape, but not tensor values."""
    h = hashlib.sha256()
    if isinstance(value, dict):
        h.update(b"dict")
        for key in sorted(value):
            h.update(str(key).encode())
            h.update(structure_digest(value[key]).encode())
    elif isinstance(value, (list, tuple)):
        h.update(type(value).__name__.encode())
        h.update(str(len(value)).encode())
        for item in value:
            h.update(structure_digest(item).encode())
    elif torch.is_tensor(value):
        h.update(b"tensor")
        h.update(str(value.dtype).encode())
        h.update(str(tuple(value.shape)).encode())
    else:
        h.update(type(value).__name__.encode())
    return h.hexdigest()


def inspect_checkpoint(path: Path) -> dict[str, Any]:
    payload = torch.load(str(path), map_location="cpu")
    if not isinstance(payload, dict):
        raise RuntimeError(f"checkpoint is {type(payload).__name__}, expected dict")
    required = ["model_state_dict", "optimizer_state_dict", "scheduler_state_dict", "frames"]
    missing = [k for k in required if k not in payload]
    result = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "keys": sorted(payload),
        "required_keys": required,
        "missing_keys": missing,
        "frames": int(payload.get("frames", -1)),
    }
    for key in ("model_state_dict", "optimizer_state_dict", "scheduler_state_dict"):
        if key in payload:
            result[f"{key}_digest"] = tensor_digest(payload[key])
            result[f"{key}_structure_digest"] = structure_digest(payload[key])
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silg-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    args = parser.parse_args()
    root, out = args.silg_root.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    patch = patch_deterministic_seed(root)

    first_frames = FRAMES_PER_UPDATE * 2
    resumed_frames = FRAMES_PER_UPDATE * 3
    base_dir, xpid = out / "official_checkpoint_base", "rtfm-official-resume-qualification"
    first = run(
        command(root, base_dir, xpid, args.seed, first_frames),
        root,
        out / "SILG_OFFICIAL_CHECKPOINT_INITIAL.log",
        args.timeout_seconds,
    )
    if first["returncode"] != 0:
        payload = {
            "qualified": False,
            "stage": "initial_training",
            "official_contract": OFFICIAL,
            "frames_per_update": FRAMES_PER_UPDATE,
            "patch": patch,
            "initial_run": first,
        }
        (out / "SILG_OFFICIAL_CHECKPOINT_RESUME_QUALIFICATION.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        raise SystemExit(1)

    initial_job = locate_job(base_dir)
    initial = inspect_checkpoint(initial_job)
    shutil.copy2(initial_job, out / "SILG_RTFM_OFFICIAL_INITIAL_JOB.tar")

    resumes = []
    for label in ("A", "B"):
        clone = out / f"official_checkpoint_resume_{label}"
        shutil.copytree(base_dir, clone)
        record = run(
            command(root, clone, xpid, args.seed, resumed_frames),
            root,
            out / f"SILG_OFFICIAL_CHECKPOINT_RESUME_{label}.log",
            args.timeout_seconds,
        )
        if record["returncode"] == 0:
            job = locate_job(clone)
            record["checkpoint"] = inspect_checkpoint(job)
            shutil.copy2(job, out / f"SILG_RTFM_OFFICIAL_RESUMED_{label}_JOB.tar")
        resumes.append(record)

    completed = all(r["returncode"] == 0 and "checkpoint" in r for r in resumes)
    schema_ok = not initial["missing_keys"] and completed and all(
        not r["checkpoint"]["missing_keys"] for r in resumes
    )
    frame_ok = (
        initial["frames"] >= first_frames
        and completed
        and all(r["checkpoint"]["frames"] >= resumed_frames for r in resumes)
        and all(r["checkpoint"]["frames"] > initial["frames"] for r in resumes)
    )
    topology_ok = completed and all(
        r["checkpoint"][f"{key}_structure_digest"] == initial[f"{key}_structure_digest"]
        for r in resumes
        for key in ("model_state_dict", "optimizer_state_dict", "scheduler_state_dict")
    )
    state_advanced = completed and all(
        r["checkpoint"]["model_state_dict_digest"] != initial["model_state_dict_digest"]
        and r["checkpoint"]["optimizer_state_dict_digest"] != initial["optimizer_state_dict_digest"]
        and r["checkpoint"]["scheduler_state_dict_digest"] != initial["scheduler_state_dict_digest"]
        for r in resumes
    )

    same_model = completed and resumes[0]["checkpoint"]["model_state_dict_digest"] == resumes[1]["checkpoint"]["model_state_dict_digest"]
    same_optimizer = completed and resumes[0]["checkpoint"]["optimizer_state_dict_digest"] == resumes[1]["checkpoint"]["optimizer_state_dict_digest"]
    same_scheduler = completed and resumes[0]["checkpoint"]["scheduler_state_dict_digest"] == resumes[1]["checkpoint"]["scheduler_state_dict_digest"]
    bitwise_resume_equivalent = bool(same_model and same_optimizer and same_scheduler)

    qualified = bool(completed and schema_ok and frame_ok and topology_ok and state_advanced)
    payload = {
        "qualified": qualified,
        "classification": "infrastructure_qualification_only",
        "capability_claim_allowed": False,
        "official_contract": OFFICIAL,
        "qualification_budget": {
            "initial_frames": first_frames,
            "resumed_frames": resumed_frames,
            "frames_per_update": FRAMES_PER_UPDATE,
            "seed": args.seed,
        },
        "determinism_note": (
            "The official 30-actor/4-learner-thread profile has nondeterministic queue and thread "
            "interleaving. Exact A/B tensor equality is diagnostic and is not required for checkpoint "
            "load/advance integrity qualification."
        ),
        "patch": patch,
        "initial_run": first,
        "initial_checkpoint": initial,
        "resume_runs": resumes,
        "checks": {
            "completed": completed,
            "schema_ok": schema_ok,
            "frame_counter_advanced": frame_ok,
            "state_topology_preserved": topology_ok,
            "model_optimizer_scheduler_state_advanced": state_advanced,
            "bitwise_resume_equivalence_diagnostic": bitwise_resume_equivalent,
            "deterministic_model_equivalence_diagnostic": same_model,
            "deterministic_optimizer_equivalence_diagnostic": same_optimizer,
            "deterministic_scheduler_equivalence_diagnostic": same_scheduler,
        },
    }
    target = out / "SILG_OFFICIAL_CHECKPOINT_RESUME_QUALIFICATION.json"
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["checks"], sort_keys=True))
    if not qualified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
