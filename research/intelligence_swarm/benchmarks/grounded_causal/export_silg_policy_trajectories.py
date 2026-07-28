#!/usr/bin/env python3
"""Export public SILG/RTFM trajectories from the pinned official recurrent model.

This is a dataset adapter, not a new model. It records only current observation,
chosen action and next observation. Future rewards/terminal state are retained as
labels but are never included in model inputs by environment_first_baseline.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

LANGUAGE_FIELDS = ("wiki", "task")
EXCLUDED_STATE_FIELDS = {
    "wiki", "task", "reward", "done", "episode_return", "episode_step", "last_action"
}


def flatten_tensor(value: torch.Tensor) -> list[float]:
    return value.detach().cpu().to(torch.float32).contiguous().view(-1).tolist()


def state_vector(obs: dict[str, torch.Tensor]) -> list[float]:
    out: list[float] = []
    for key in sorted(obs):
        if key in EXCLUDED_STATE_FIELDS:
            continue
        value = obs[key]
        if torch.is_tensor(value):
            out.extend(flatten_tensor(value))
    return out


def text_tokens(obs: dict[str, torch.Tensor]) -> list[int]:
    out: list[int] = []
    for key in LANGUAGE_FIELDS:
        if key not in obs:
            continue
        values = obs[key].detach().cpu().contiguous().view(-1).tolist()
        out.extend(int(v) for v in values if int(v) != 0)
        out.append(0)  # field separator / padding token
    return out


def fingerprint(obs: dict[str, torch.Tensor]) -> str:
    h = hashlib.sha256()
    for key in sorted(k for k in obs if k not in {"reward", "done", "episode_return", "episode_step"}):
        value = obs[key].detach().cpu().contiguous()
        h.update(key.encode("utf-8"))
        h.update(str(tuple(value.shape)).encode("ascii"))
        h.update(value.numpy().tobytes())
    return h.hexdigest()


def export_split(
    silg_root: Path,
    checkpoint: Path,
    env_name: str,
    split: str,
    seed: int,
    episodes: int,
) -> list[dict[str, Any]]:
    sys.path.insert(0, str(silg_root))
    import exp_utils
    from core import environment
    from model.multi import Model
    from silg import envs as _registered_envs  # noqa: F401

    flags = exp_utils.get_parser().parse_args([])
    flags.env = env_name
    flags.val_env = env_name
    flags.model = "multi"
    flags.disable_cuda = True
    flags.seed = seed

    template = Model.create_env(flags)
    model = Model.make(flags, template).eval()
    template.close()
    model.load_state_dict(torch.load(str(checkpoint), map_location="cpu"))

    rows: list[dict[str, Any]] = []
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
        done = False
        step = 0
        while not done:
            before = state_vector(obs)
            tokens = text_tokens(obs)
            with torch.no_grad():
                output, agent_state = model(obs, agent_state)
            action = output["action"]
            nxt = env.step(action)
            after = state_vector(nxt)
            if len(before) != len(after):
                raise RuntimeError(f"state dimension changed: {len(before)} -> {len(after)}")
            rows.append(
                {
                    "instance_id": f"{split}-{seed}-{episode}-{step}",
                    "episode_id": f"{split}-{seed}-{episode}",
                    "episode_seed": episode_seed,
                    "domain": env_name,
                    "seed": seed,
                    "split": split,
                    "observation_fingerprint": fingerprint(obs),
                    "text_tokens": tokens,
                    "state_before": before,
                    "state_after": after,
                    "action": int(action.item()),
                    "reward": float(nxt["reward"].item()),
                    "done": bool(nxt["done"].item()),
                    "entity_holdout": False,
                    "dynamics_holdout": False,
                    "language_holdout": split == "test",
                }
            )
            obs = nxt
            step += 1
            done = bool(obs["done"].item())
        env.close()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silg-root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--train-episodes", type=int, default=40)
    parser.add_argument("--test-episodes", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    train = export_split(
        args.silg_root,
        args.checkpoint,
        "silg:rtfm_train_s1-v0",
        "train",
        args.seed,
        args.train_episodes,
    )
    test = export_split(
        args.silg_root,
        args.checkpoint,
        "silg:rtfm_test_s1-v0",
        "test",
        args.seed,
        args.test_episodes,
    )
    rows = train + test
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(json.dumps(row, separators=(",", ":")) for row in rows) + "\n")
    digest = hashlib.sha256(args.out.read_bytes()).hexdigest()
    print(
        json.dumps(
            {
                "status": "success",
                "seed": args.seed,
                "train_rows": len(train),
                "test_rows": len(test),
                "state_dim": len(rows[0]["state_before"]),
                "max_text_tokens": max(len(row["text_tokens"]) for row in rows),
                "dataset_sha256": digest,
                "out": str(args.out),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
