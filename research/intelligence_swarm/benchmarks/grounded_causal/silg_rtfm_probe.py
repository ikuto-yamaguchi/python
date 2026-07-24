#!/usr/bin/env python3
"""Pinned SILG/RTFM environment and random-control reproduction probe.

This is not a new model. It checks that the public benchmark can be imported,
records the observation/action contract, and measures a matched random control
on three seeds before any recurrent baseline is accepted.
"""
from __future__ import annotations

import argparse
import json
import platform
import random
import resource
import statistics
import sys
import time
from pathlib import Path
from typing import Any


def shape_of(value: Any) -> Any:
    if hasattr(value, "shape"):
        return list(value.shape)
    if isinstance(value, dict):
        return {str(k): shape_of(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [len(value)]
    return type(value).__name__


def reset_compat(env: Any, seed: int) -> Any:
    try:
        out = env.reset(seed=seed)
    except TypeError:
        if hasattr(env, "seed"):
            env.seed(seed)
        out = env.reset()
    return out[0] if isinstance(out, tuple) and len(out) == 2 else out


def step_compat(env: Any, action: int) -> tuple[Any, float, bool, dict[str, Any]]:
    out = env.step(action)
    if len(out) == 5:
        obs, reward, terminated, truncated, info = out
        return obs, float(reward), bool(terminated or truncated), dict(info)
    obs, reward, done, info = out
    return obs, float(reward), bool(done), dict(info)


def sample_valid_action(obs: Any, action_n: int, rng: random.Random) -> int:
    if isinstance(obs, dict) and "valid" in obs:
        valid = obs["valid"]
        if hasattr(valid, "tolist"):
            valid = valid.tolist()
        indices = [i for i, flag in enumerate(valid) if float(flag) > 0]
        if indices:
            return rng.choice(indices)
    return rng.randrange(action_n)


def run_seed(env_id: str, seed: int, episodes: int, max_steps: int) -> dict[str, Any]:
    import gym
    import silg.envs  # noqa: F401; explicit registration side effect

    rng = random.Random(seed)
    env = gym.make(env_id)
    action_n = int(getattr(env.action_space, "n", len(env.action_space)))
    returns: list[float] = []
    wins = 0
    lengths: list[int] = []
    inference_ns: list[int] = []
    first_schema = None

    started = time.perf_counter()
    for episode in range(episodes):
        obs = reset_compat(env, seed * 1000 + episode)
        if first_schema is None:
            first_schema = {
                "observation_keys": sorted(obs.keys()) if isinstance(obs, dict) else None,
                "observation_shapes": shape_of(obs),
                "action_count": action_n,
            }
        total = 0.0
        won = False
        length = 0
        for step in range(max_steps):
            t0 = time.perf_counter_ns()
            action = sample_valid_action(obs, action_n, rng)
            inference_ns.append(time.perf_counter_ns() - t0)
            obs, reward, done, info = step_compat(env, action)
            total += reward
            length = step + 1
            won = won or bool(info.get("won", reward > 0.8))
            if done:
                break
        returns.append(total)
        lengths.append(length)
        wins += int(won)
    elapsed = time.perf_counter() - started
    env.close()
    return {
        "seed": seed,
        "episodes": episodes,
        "wins": wins,
        "win_rate": wins / episodes,
        "return_mean": statistics.fmean(returns),
        "episode_length_mean": statistics.fmean(lengths),
        "wall_seconds": elapsed,
        "action_selection_latency_us_mean": statistics.fmean(inference_ns) / 1000.0,
        "schema": first_schema,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="silg:rtfm_train_s1-v0")
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--max-steps", type=int, default=80)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    started = time.perf_counter()
    try:
        import gym
        import torch
        import silg
        import silg.envs  # noqa: F401
        import rtfm

        results = [run_seed(args.env, seed, args.episodes, args.max_steps) for seed in args.seeds]
        status = "success"
        error = None
        versions = {
            "python": sys.version,
            "platform": platform.platform(),
            "gym": getattr(gym, "__version__", "unknown"),
            "torch": getattr(torch, "__version__", "unknown"),
            "silg": getattr(silg, "__version__", "0.0.1-source"),
            "rtfm": getattr(rtfm, "__version__", "source"),
        }
    except Exception as exc:
        status = "failed"
        error = {"type": type(exc).__name__, "message": str(exc)}
        results = []
        versions = {"python": sys.version, "platform": platform.platform()}

    payload = {
        "status": status,
        "error": error,
        "environment": args.env,
        "condition": "random_valid_action",
        "seeds": args.seeds,
        "episodes_per_seed": args.episodes,
        "results": results,
        "versions": versions,
        "source_pins": {
            "silg": "2af07578e1264029a240fcfb78d4ac0aea16f5de",
            "rtfm": "58f17955595b5a127c96d045d896fcbcc7d4b570",
        },
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "total_wall_seconds": time.perf_counter() - started,
        "model_bytes": 0,
        "graph_or_candidate_size": 0,
        "answer_leakage": False,
        "official_recurrent_baseline_completed": False,
        "language_blind_completed": False,
        "state_only_completed": False,
        "capability_progress_claimed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if status != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
