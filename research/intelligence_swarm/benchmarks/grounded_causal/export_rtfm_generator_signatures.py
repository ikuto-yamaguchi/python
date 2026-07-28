#!/usr/bin/env python3
"""Export pre-outcome RTFM generator signatures for qualified R0.2 splits.

The fixed SILG RTFM S1 train/test pair uses disjoint dynamics assignments, while
sharing the same entity vocabulary and canonical language form.  This exporter
reads only generator state immediately after reset; it never reads actions,
rewards, outcomes, completed trajectories, or model predictions.
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

CANONICAL_SEEDS = (1, 7, 19)
TRAIN_ENV = "silg:rtfm_train_s1-v0"
TEST_ENV = "silg:rtfm_test_s1-v0"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _signature(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _describe_element(value: Any) -> str:
    describe = getattr(value, "describe", None)
    return str(describe() if callable(describe) else value)


def _task_from_wrapper(gym_env: Any) -> Any:
    task = getattr(gym_env, "rtfm_env", None)
    if task is None:
        raise RuntimeError("SILG RTFM wrapper does not expose .rtfm_env")
    required = ("group_assignment", "modifier_assignment", "target_group")
    missing = [name for name in required if not hasattr(task, name)]
    if missing:
        raise RuntimeError(f"RTFM generator metadata missing: {missing}")
    return task


def extract_generator_metadata(gym_env: Any, split: str, seed: int, episode: int) -> dict[str, Any]:
    """Read only pre-outcome generator state from a reset RTFM episode."""
    task = _task_from_wrapper(gym_env)

    group_assignment = [
        {"group": str(group), "monsters": sorted(str(x) for x in monsters)}
        for group, monsters in task.group_assignment
    ]
    group_assignment.sort(key=lambda item: (item["group"], item["monsters"]))

    modifier_assignment = [
        {"element": _describe_element(element), "modifiers": sorted(str(x) for x in modifiers)}
        for element, modifiers in task.modifier_assignment
    ]
    modifier_assignment.sort(key=lambda item: (item["element"], item["modifiers"]))

    # S1 train/dev classes share one fixed ontology.  Recording that ontology
    # makes the absence of an entity holdout explicit instead of fabricating one
    # from sampled episode occupants.
    entity_ontology = {
        "monsters": sorted(str(x) for x in getattr(task, "monsters", ())),
        "groups": sorted(str(x) for x in getattr(task, "groups", ())),
        "modifiers": sorted(str(x) for x in getattr(task, "modifiers", ())),
        "items": sorted(str(x) for x in getattr(task, "items", ())),
    }

    dynamics_payload = {
        "group_assignment": group_assignment,
        "modifier_assignment": modifier_assignment,
    }
    language_form_payload = {
        "family": "rtfm-groups-canonical-literal-v1",
        "natural_language_template_sampling": False,
    }
    episode_seed = seed * 1_000_003 + episode
    return {
        "domain": TRAIN_ENV if split == "train" else TEST_ENV,
        "split": split,
        "seed": seed,
        "episode": episode,
        "episode_id": f"{split}-{seed}-{episode}",
        "episode_seed": episode_seed,
        "entity_signature": _signature(entity_ontology),
        "dynamics_signature": _signature(dynamics_payload),
        "language_form_signature": _signature(language_form_payload),
        "entity_holdout": False,
        "dynamics_holdout": split == "test",
        "language_holdout": False,
        "holdout_support": {
            "entity": False,
            "dynamics": True,
            "language_form": False,
        },
        "generator_metadata": {
            "entity_ontology": entity_ontology,
            "dynamics": dynamics_payload,
            "language_form": language_form_payload,
            "target_group": str(task.target_group),
        },
        "provenance": {
            "source": "RTFM generator state immediately after reset",
            "uses_action": False,
            "uses_reward": False,
            "uses_outcome": False,
            "uses_prediction": False,
            "uses_completed_trajectory": False,
        },
    }


def export_split(silg_root: Path, env_name: str, split: str, seed: int, episodes: int) -> list[dict[str, Any]]:
    sys.path.insert(0, str(silg_root))
    import exp_utils
    from model.multi import Model
    from silg import envs as _registered_envs  # noqa: F401

    flags = exp_utils.get_parser().parse_args([])
    flags.env = env_name
    flags.val_env = env_name
    flags.model = "multi"
    flags.disable_cuda = True
    flags.seed = seed

    rows: list[dict[str, Any]] = []
    for episode in range(episodes):
        episode_seed = seed * 1_000_003 + episode
        random.seed(episode_seed)
        np.random.seed(episode_seed)
        torch.manual_seed(episode_seed)
        env = Model.create_env(flags)
        env.seed(episode_seed)
        env.reset()
        rows.append(extract_generator_metadata(env, split, seed, episode))
        env.close()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silg-root", type=Path, required=True)
    parser.add_argument("--seed", type=int, choices=CANONICAL_SEEDS, required=True)
    parser.add_argument("--train-episodes", type=int, default=40)
    parser.add_argument("--test-episodes", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    rows = export_split(args.silg_root, TRAIN_ENV, "train", args.seed, args.train_episodes)
    rows += export_split(args.silg_root, TEST_ENV, "test", args.seed, args.test_episodes)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(_canonical(row) for row in rows) + "\n", encoding="utf-8")
    train_dynamics = {row["dynamics_signature"] for row in rows if row["split"] == "train"}
    test_dynamics = {row["dynamics_signature"] for row in rows if row["split"] == "test"}
    summary = {
        "status": "success",
        "seed": args.seed,
        "rows": len(rows),
        "dataset_sha256": hashlib.sha256(args.out.read_bytes()).hexdigest(),
        "holdout_support": {"entity": False, "dynamics": True, "language_form": False},
        "train_test_dynamics_overlap": sorted(train_dynamics & test_dynamics),
        "classification": "rtfm_s1_supports_dynamics_transfer_only",
        "out": str(args.out),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if train_dynamics & test_dynamics:
        raise SystemExit("RTFM S1 train/test dynamics signatures overlap")


if __name__ == "__main__":
    main()
