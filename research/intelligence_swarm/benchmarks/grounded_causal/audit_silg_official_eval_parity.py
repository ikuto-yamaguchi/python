#!/usr/bin/env python3
"""Audit parity between SILG's official test loop and the matched R0.1 evaluator.

This script does not alter training or architecture.  It evaluates the same pinned
checkpoint under two explicitly separated protocols:

1. ``official_continuous_stream`` mirrors ``vzhong/silg@2af0757:run_exp.test``:
   one seeded environment, automatic episode continuation, recurrent state reset
   only after terminal observations.
2. ``fresh_seeded_instances`` mirrors the R0 matched-control protocol:
   a fresh environment per preregistered episode seed.

A difference is evaluation-protocol evidence, not capability progress.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

SILG_SHA = "2af07578e1264029a240fcfb78d4ac0aea16f5de"
RTFM_SHA = "58f17955595b5a127c96d045d896fcbcc7d4b570"
OFFICIAL_TEST_SOURCE = "run_exp.py:test"
CANONICAL_SEEDS = [1, 7, 19]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def set_all_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def load_runtime(root: Path, checkpoint: Path, seed: int):
    sys.path.insert(0, str(root))
    import exp_utils
    from core import environment
    from model.multi import Model
    from silg import envs as _registered_envs  # noqa: F401

    flags = exp_utils.get_parser().parse_args([])
    flags.env = "silg:rtfm_test_s1-v0"
    flags.val_env = flags.env
    flags.model = "multi"
    flags.disable_cuda = True
    flags.seed = seed

    template = Model.create_env(flags)
    model = Model.make(flags, template).eval()
    template.close()
    state_dict = torch.load(str(checkpoint), map_location="cpu")
    model.load_state_dict(state_dict, strict=True)
    return flags, Model, environment, model


def summarize(records: list[dict[str, Any]], inference_ns: list[int]) -> dict[str, Any]:
    if not records or not inference_ns:
        raise RuntimeError("empty evaluation stream")
    return {
        "episodes": len(records),
        "win_rate": statistics.fmean(float(r["win"]) for r in records),
        "return_mean": statistics.fmean(float(r["return"]) for r in records),
        "episode_length_mean": statistics.fmean(int(r["length"]) for r in records),
        "cpu_inference_ms_per_step": statistics.fmean(inference_ns) / 1e6,
        "records": records,
    }


def official_continuous_stream(root: Path, checkpoint: Path, seed: int, episodes: int) -> dict[str, Any]:
    flags, Model, environment, model = load_runtime(root, checkpoint, seed)
    set_all_seeds(seed)
    gym_env = Model.create_env(flags)
    gym_env.seed(seed)
    env = environment.Environment(gym_env)
    observation = env.initial()
    agent_state = model.initial_state(batch_size=1)
    records: list[dict[str, Any]] = []
    inference_ns: list[int] = []
    steps = 0

    while len(records) < episodes:
        t0 = time.perf_counter_ns()
        with torch.no_grad():
            output, agent_state = model(observation, agent_state)
        inference_ns.append(time.perf_counter_ns() - t0)
        observation = env.step(output["action"])
        steps += 1
        if bool(observation["done"].item()):
            reward = float(observation["reward"][0][0].item())
            records.append({
                "episode_index": len(records),
                "win": reward > 0.5,
                "return": float(observation["episode_return"].item()),
                "length": steps,
            })
            steps = 0
            agent_state = model.initial_state(batch_size=1)

    env.close()
    out = summarize(records, inference_ns)
    out["protocol"] = "official_continuous_stream"
    out["environment_seed"] = seed
    out["recurrent_reset"] = "after_terminal_only"
    return out


def fresh_seeded_instances(root: Path, checkpoint: Path, seed: int, episodes: int) -> dict[str, Any]:
    flags, Model, environment, model = load_runtime(root, checkpoint, seed)
    records: list[dict[str, Any]] = []
    inference_ns: list[int] = []

    for episode in range(episodes):
        episode_seed = seed * 1_000_003 + episode
        set_all_seeds(episode_seed)
        gym_env = Model.create_env(flags)
        gym_env.seed(episode_seed)
        env = environment.Environment(gym_env)
        observation = env.initial()
        agent_state = model.initial_state(batch_size=1)
        steps = 0
        while not bool(observation["done"].item()):
            t0 = time.perf_counter_ns()
            with torch.no_grad():
                output, agent_state = model(observation, agent_state)
            inference_ns.append(time.perf_counter_ns() - t0)
            observation = env.step(output["action"])
            steps += 1
        reward = float(observation["reward"][0][0].item())
        records.append({
            "episode_index": episode,
            "episode_seed": episode_seed,
            "win": reward > 0.5,
            "return": float(observation["episode_return"].item()),
            "length": steps,
        })
        env.close()

    out = summarize(records, inference_ns)
    out["protocol"] = "fresh_seeded_instances"
    out["episode_seed_formula"] = "experiment_seed * 1000003 + episode_index"
    out["recurrent_reset"] = "fresh_environment_and_state_per_episode"
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silg-root", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=CANONICAL_SEEDS)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds != CANONICAL_SEEDS:
        raise SystemExit("evaluation-parity seed topology must be exactly 1 7 19")
    if args.episodes <= 0:
        raise SystemExit("episodes must be positive")

    runs: list[dict[str, Any]] = []
    for seed in args.seeds:
        checkpoint = args.results / f"SILG_RTFM_TRAINED_STATE_SEED_{seed}.pt"
        if not checkpoint.is_file():
            raise FileNotFoundError(checkpoint)
        official = official_continuous_stream(args.silg_root.resolve(), checkpoint.resolve(), seed, args.episodes)
        matched = fresh_seeded_instances(args.silg_root.resolve(), checkpoint.resolve(), seed, args.episodes)
        runs.append({
            "seed": seed,
            "checkpoint": {
                "path": checkpoint.name,
                "bytes": checkpoint.stat().st_size,
                "sha256": sha256(checkpoint),
            },
            "official_continuous_stream": official,
            "fresh_seeded_instances": matched,
            "protocol_gap": {
                "win_rate": official["win_rate"] - matched["win_rate"],
                "return_mean": official["return_mean"] - matched["return_mean"],
                "episode_length_mean": official["episode_length_mean"] - matched["episode_length_mean"],
            },
        })

    payload = {
        "status": "success",
        "classification": "r01_evaluation_protocol_parity_audit_only",
        "source_pins": {"silg": SILG_SHA, "rtfm": RTFM_SHA},
        "official_reference": OFFICIAL_TEST_SOURCE,
        "environment": "silg:rtfm_test_s1-v0",
        "seeds": args.seeds,
        "episodes_per_protocol_seed": args.episodes,
        "new_architecture": False,
        "capability_progress_claimed": False,
        "interpretation": "A protocol gap diagnoses evaluation/default mismatch; it does not establish or refute learned capability by itself.",
        "runs": runs,
        "aggregate_protocol_gap": {
            key: statistics.fmean(run["protocol_gap"][key] for run in runs)
            for key in ("win_rate", "return_mean", "episode_length_mean")
        },
    }
    out = args.out or (args.results / "SILG_RTFM_OFFICIAL_EVAL_PARITY_3SEED.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
