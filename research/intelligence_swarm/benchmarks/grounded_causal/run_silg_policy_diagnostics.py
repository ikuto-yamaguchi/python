#!/usr/bin/env python3
"""Diagnose an official SILG recurrent checkpoint without changing the policy.

Records action usage, valid-action interaction, masked policy entropy, recurrent
state norms, and terminal outcomes on fixed RTFM test instances. This is a
reproduction diagnostic, not a new model or training mechanism.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

SILG_SHA = "2af07578e1264029a240fcfb78d4ac0aea16f5de"
RTFM_SHA = "58f17955595b5a127c96d045d896fcbcc7d4b570"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def state_l2(state: tuple[torch.Tensor, ...]) -> float:
    if not state:
        return 0.0
    return math.sqrt(sum(float(x.detach().float().pow(2).sum().item()) for x in state))


def scalar(obs: dict[str, torch.Tensor], key: str, default: float = 0.0) -> float:
    value = obs.get(key)
    return default if value is None else float(value.detach().cpu().reshape(-1)[0].item())


def run_seed(root: Path, checkpoint: Path, seed: int, episodes: int) -> dict[str, Any]:
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

    actions: collections.Counter[int] = collections.Counter()
    terminal_rewards: collections.Counter[str] = collections.Counter()
    entropies: list[float] = []
    valid_counts: list[int] = []
    chosen_valid: list[bool] = []
    state_norm_before: list[float] = []
    state_norm_after: list[float] = []
    episodes_out: list[dict[str, Any]] = []
    inference_ns: list[int] = []

    for episode in range(episodes):
        episode_seed = seed * 1_000_003 + episode
        random.seed(episode_seed)
        np.random.seed(episode_seed)
        torch.manual_seed(episode_seed)
        gym_env = Model.create_env(flags)
        gym_env.seed(episode_seed)
        env = environment.Environment(gym_env)
        obs = env.initial()
        agent_state = model.initial_state(batch_size=1)
        initial_state_norm = state_l2(agent_state)
        steps = 0

        while not bool(obs["done"].item()):
            valid = obs["valid"].detach().bool().reshape(-1)
            if not bool(valid.any().item()):
                raise RuntimeError(f"episode {episode_seed}: no valid action")
            valid_counts.append(int(valid.sum().item()))
            state_norm_before.append(state_l2(agent_state))
            t0 = time.perf_counter_ns()
            with torch.no_grad():
                output, next_state = model(obs, agent_state)
            inference_ns.append(time.perf_counter_ns() - t0)
            logits = output.get("policy_logits")
            if logits is None:
                raise RuntimeError("official model output lacks policy_logits")
            flat_logits = logits.detach().float().reshape(-1)
            if flat_logits.numel() != valid.numel():
                raise RuntimeError("policy/action-mask dimension mismatch")
            probs = torch.softmax(flat_logits[valid], dim=0)
            entropy = float((-(probs * probs.clamp_min(1e-30).log()).sum()).item())
            if not math.isfinite(entropy):
                raise RuntimeError("non-finite policy entropy")
            entropies.append(entropy)
            action = int(output["action"].detach().cpu().reshape(-1)[0].item())
            if not 0 <= action < valid.numel():
                raise RuntimeError(f"action {action} outside official schema")
            actions[action] += 1
            chosen_valid.append(bool(valid[action].item()))
            state_norm_after.append(state_l2(next_state))
            agent_state = next_state
            obs = env.step(torch.tensor([[action]], dtype=torch.int64))
            steps += 1

        reward = scalar(obs, "reward")
        episode_return = scalar(obs, "episode_return")
        terminal_key = "positive" if reward > 0.5 else "negative" if reward < -0.5 else "zero"
        terminal_rewards[terminal_key] += 1
        episodes_out.append({
            "episode_index": episode,
            "episode_seed": episode_seed,
            "steps": steps,
            "terminal_reward": reward,
            "episode_return": episode_return,
            "win": reward > 0.5,
            "initial_recurrent_state_l2": initial_state_norm,
            "final_recurrent_state_l2": state_l2(agent_state),
        })
        env.close()

    if not actions or not entropies or not chosen_valid:
        raise RuntimeError("empty diagnostic stream")
    return {
        "seed": seed,
        "episodes": episodes,
        "checkpoint": {"path": checkpoint.name, "bytes": checkpoint.stat().st_size, "sha256": sha256(checkpoint)},
        "action_histogram": {str(k): v for k, v in sorted(actions.items())},
        "unique_actions_used": len(actions),
        "terminal_reward_classes": dict(sorted(terminal_rewards.items())),
        "valid_action_count_mean": float(np.mean(valid_counts)),
        "valid_action_count_min": min(valid_counts),
        "valid_action_count_max": max(valid_counts),
        "chosen_action_valid_fraction": float(np.mean(chosen_valid)),
        "masked_policy_entropy_mean": float(np.mean(entropies)),
        "masked_policy_entropy_min": min(entropies),
        "masked_policy_entropy_max": max(entropies),
        "recurrent_state_l2_before_mean": float(np.mean(state_norm_before)),
        "recurrent_state_l2_after_mean": float(np.mean(state_norm_after)),
        "cpu_inference_ms_per_step": float(np.mean(inference_ns)) / 1e6,
        "episodes_detail": episodes_out,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silg-root", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 7, 19])
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds != [1, 7, 19]:
        raise SystemExit("diagnostic seed topology must be exactly 1 7 19")
    if args.episodes <= 0:
        raise SystemExit("episodes must be positive")

    runs = []
    for seed in args.seeds:
        checkpoint = args.results / f"SILG_RTFM_TRAINED_STATE_SEED_{seed}.pt"
        if not checkpoint.is_file():
            raise FileNotFoundError(checkpoint)
        runs.append(run_seed(args.silg_root.resolve(), checkpoint.resolve(), seed, args.episodes))

    payload = {
        "status": "success",
        "classification": "r01_official_policy_diagnostic_only",
        "environment": "silg:rtfm_test_s1-v0",
        "source_pins": {"silg": SILG_SHA, "rtfm": RTFM_SHA},
        "seeds": args.seeds,
        "pretrained_language_model": False,
        "new_architecture": False,
        "capability_progress_claimed": False,
        "runs": runs,
    }
    out = args.out or (args.results / "SILG_RTFM_POLICY_DIAGNOSTICS_3SEED.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
