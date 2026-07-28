#!/usr/bin/env python3
"""Export typed SILG/RTFM policy trajectories for the faithful R0.2 baseline.

This is a dataset adapter only. It preserves field boundaries and integer
semantics that the legacy flat exporter discarded. Reward, termination and
completed-trajectory values remain labels/provenance and are never included in
``state_before_fields``.

Holdout assignments are not inferred by this exporter. They are attached later
from the pre-outcome generator manifest. Raw rows therefore carry only false
placeholder values, preventing the RTFM S1 test split from being mislabeled as
a language-form holdout.
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
# RTFM exposes inventory as token IDs, but inventory is part of the physical
# environment state rather than instruction language. Only exogenous
# instruction channels and SILG's concatenated text aliases are language-only.
LANGUAGE_ONLY_FIELDS = {"wiki", "wiki_len", "task", "task_len", "text", "text_len"}
POST_TREATMENT_FIELDS = {"reward", "done", "episode_return", "episode_step", "last_action"}
CANONICAL_SEEDS = (1, 7, 19)


def _tensor_values(value: torch.Tensor) -> list[Any]:
    tensor = value.detach().cpu().contiguous()
    if tensor.dtype.is_floating_point:
        return tensor.to(torch.float32).view(-1).tolist()
    return tensor.to(torch.int64).view(-1).tolist()


def _shape(value: torch.Tensor) -> list[int]:
    return [int(x) for x in value.shape]


def text_tokens(obs: dict[str, torch.Tensor]) -> list[int]:
    tokens: list[int] = []
    for key in LANGUAGE_FIELDS:
        if key not in obs:
            continue
        values = obs[key].detach().cpu().contiguous().view(-1).tolist()
        tokens.extend(int(v) for v in values if int(v) != 0)
        tokens.append(0)
    return tokens


def observation_fingerprint(obs: dict[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for key in sorted(k for k in obs if k not in POST_TREATMENT_FIELDS):
        value = obs[key].detach().cpu().contiguous()
        digest.update(key.encode("utf-8"))
        digest.update(str(tuple(value.shape)).encode("ascii"))
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def state_fields(obs: dict[str, torch.Tensor]) -> dict[str, list[Any]]:
    fields: dict[str, list[Any]] = {}
    for key in sorted(obs):
        if key in LANGUAGE_ONLY_FIELDS or key in POST_TREATMENT_FIELDS:
            continue
        value = obs[key]
        if torch.is_tensor(value):
            fields[key] = _tensor_values(value)
    return fields


def build_schema(env: Any, sample: dict[str, torch.Tensor]) -> list[dict[str, Any]]:
    """Build an RTFM schema only from pinned public environment metadata."""
    vocab_size = len(env.vocab)
    if vocab_size < 2:
        raise RuntimeError("invalid public tokenizer vocabulary")
    metadata = {
        "name": ("categorical", vocab_size),
        "name_len": ("categorical", int(env.max_name) + 1),
        "inv": ("categorical", vocab_size),
        "inv_len": ("categorical", int(env.max_inv) + 1),
        "valid": ("binary", None),
        "rel_pos": ("continuous", None),
        "pos": ("continuous", None),
    }
    schema: list[dict[str, Any]] = []
    for key in sorted(sample):
        if key in LANGUAGE_ONLY_FIELDS or key in POST_TREATMENT_FIELDS:
            continue
        value = sample[key]
        if not torch.is_tensor(value):
            continue
        if key not in metadata:
            raise RuntimeError(
                f"unmapped RTFM state field {key!r}; classify it from official metadata "
                "instead of inferring semantics from evaluation rows"
            )
        kind, cardinality = metadata[key]
        item: dict[str, Any] = {"name": key, "kind": kind, "shape": _shape(value)}
        if cardinality is not None:
            item["cardinality"] = cardinality
        schema.append(item)
    if not schema:
        raise RuntimeError("empty typed state schema")
    return schema


def _validate_fields(fields: dict[str, list[Any]], schema: list[dict[str, Any]]) -> None:
    for spec in schema:
        name = str(spec["name"])
        if name not in fields:
            raise RuntimeError(f"missing field {name!r}")
        expected = int(np.prod(spec["shape"], dtype=np.int64))
        if len(fields[name]) != expected:
            raise RuntimeError(f"field {name!r} width changed: {len(fields[name])} != {expected}")
        if spec["kind"] == "binary" and any(int(v) not in (0, 1) for v in fields[name]):
            raise RuntimeError(f"binary field {name!r} contains a non-binary value")
        if spec["kind"] == "categorical":
            cardinality = int(spec["cardinality"])
            if any(int(v) < 0 or int(v) >= cardinality for v in fields[name]):
                raise RuntimeError(f"categorical field {name!r} exceeds cardinality {cardinality}")


def export_split(
    silg_root: Path,
    checkpoint: Path,
    env_name: str,
    split: str,
    seed: int,
    episodes: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
    model.load_state_dict(torch.load(str(checkpoint), map_location="cpu"))

    rows: list[dict[str, Any]] = []
    schema: list[dict[str, Any]] | None = None
    for episode in range(episodes):
        episode_seed = seed * 1_000_003 + episode
        random.seed(episode_seed)
        np.random.seed(episode_seed)
        torch.manual_seed(episode_seed)

        gym_env = Model.create_env(flags)
        gym_env.seed(episode_seed)
        env = environment.Environment(gym_env)
        obs = env.initial()
        if schema is None:
            schema = build_schema(gym_env, obs)
        agent_state = model.initial_state(batch_size=1)
        done = False
        step = 0
        while not done:
            before = state_fields(obs)
            _validate_fields(before, schema)
            with torch.no_grad():
                output, agent_state = model(obs, agent_state)
            action = output["action"]
            nxt = env.step(action)
            after = state_fields(nxt)
            _validate_fields(after, schema)
            rows.append(
                {
                    "instance_id": f"{split}-{seed}-{episode}-{step}",
                    "episode_id": f"{split}-{seed}-{episode}",
                    "episode_seed": episode_seed,
                    "domain": env_name,
                    "seed": seed,
                    "split": split,
                    "observation_fingerprint": observation_fingerprint(obs),
                    "text_tokens": text_tokens(obs),
                    "state_before_fields": before,
                    "state_after_fields": after,
                    "state_schema": schema,
                    "action": int(action.item()),
                    "reward": float(nxt["reward"].item()),
                    "done": bool(nxt["done"].item()),
                    "entity_holdout": False,
                    "dynamics_holdout": False,
                    "language_holdout": False,
                    "holdout_assignment_source": "pending_pre_outcome_generator_manifest",
                }
            )
            obs = nxt
            step += 1
            done = bool(obs["done"].item())
        env.close()
    template.close()
    assert schema is not None
    return rows, schema


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silg-root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--seed", type=int, choices=CANONICAL_SEEDS, required=True)
    parser.add_argument("--train-episodes", type=int, default=40)
    parser.add_argument("--test-episodes", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    train, train_schema = export_split(
        args.silg_root, args.checkpoint, "silg:rtfm_train_s1-v0", "train", args.seed, args.train_episodes
    )
    test, test_schema = export_split(
        args.silg_root, args.checkpoint, "silg:rtfm_test_s1-v0", "test", args.seed, args.test_episodes
    )
    if train_schema != test_schema:
        raise RuntimeError("train/test typed schemas differ")

    rows = train + test
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(json.dumps(row, separators=(",", ":")) for row in rows) + "\n")
    digest = hashlib.sha256(args.out.read_bytes()).hexdigest()
    schema_digest = hashlib.sha256(
        json.dumps(train_schema, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print(
        json.dumps(
            {
                "status": "success",
                "seed": args.seed,
                "train_rows": len(train),
                "test_rows": len(test),
                "fields": [item["name"] for item in train_schema],
                "dataset_sha256": digest,
                "schema_sha256": schema_digest,
                "holdout_assignment_source": "pending_pre_outcome_generator_manifest",
                "out": str(args.out),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
