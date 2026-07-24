#!/usr/bin/env python3
"""Audit whether exported SILG trajectories are eligible for R0.2 comparison.

This is an evaluation guard, not a model. Environment-first and end-to-end
models must not be compared as evidence when the behavior policy has collapsed
or supplies essentially no successful task trajectories.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entropy(counter: collections.Counter[int]) -> float:
    total = sum(counter.values())
    if not total:
        return 0.0
    return -sum((n / total) * math.log2(n / total) for n in counter.values() if n)


def summarize(path: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"empty trajectory file: {path}")
    result: dict[str, Any] = {
        "path": str(path),
        "sha256": sha256(path),
        "seed": int(rows[0]["seed"]),
        "splits": {},
    }
    for split in ("train", "test"):
        subset = [row for row in rows if row.get("split") == split]
        actions = collections.Counter(int(row["action"]) for row in subset)
        terminal = [row for row in subset if bool(row.get("done", False))]
        successful = [row for row in terminal if float(row.get("reward", 0.0)) > 0]
        episodes = {str(row["episode_id"]) for row in subset}
        texts = {tuple(int(v) for v in row.get("text_tokens", [])) for row in subset}
        majority_share = max(actions.values(), default=0) / max(1, len(subset))
        active_actions = sum(1 for count in actions.values() if count / max(1, len(subset)) >= 0.05)
        result["splits"][split] = {
            "rows": len(subset),
            "episodes": len(episodes),
            "terminal_rows": len(terminal),
            "successful_episodes": len(successful),
            "success_rate": len(successful) / max(1, len(terminal)),
            "action_counts": {str(k): v for k, v in sorted(actions.items())},
            "action_entropy_bits": entropy(actions),
            "majority_action_share": majority_share,
            "actions_with_at_least_5pct_share": active_actions,
            "unique_language_observations": len(texts),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-majority-share", type=float, default=0.90)
    parser.add_argument("--min-successful-train-episodes", type=int, default=5)
    parser.add_argument("--min-active-actions", type=int, default=2)
    args = parser.parse_args()

    datasets = [summarize(path) for path in args.inputs]
    failures: list[dict[str, Any]] = []
    for dataset in datasets:
        seed = dataset["seed"]
        train = dataset["splits"]["train"]
        if train["majority_action_share"] > args.max_majority_share:
            failures.append({
                "seed": seed,
                "check": "behavior_policy_action_collapse",
                "observed": train["majority_action_share"],
                "limit": args.max_majority_share,
            })
        if train["successful_episodes"] < args.min_successful_train_episodes:
            failures.append({
                "seed": seed,
                "check": "insufficient_successful_train_episodes",
                "observed": train["successful_episodes"],
                "required": args.min_successful_train_episodes,
            })
        if train["actions_with_at_least_5pct_share"] < args.min_active_actions:
            failures.append({
                "seed": seed,
                "check": "insufficient_action_support",
                "observed": train["actions_with_at_least_5pct_share"],
                "required": args.min_active_actions,
            })

    eligible = not failures
    output = {
        "status": "eligible" if eligible else "ineligible_public_trajectory_for_r02_capability_comparison",
        "purpose": "guard environment-first comparison against failed or collapsed behavior-policy data",
        "thresholds": {
            "max_majority_action_share": args.max_majority_share,
            "min_successful_train_episodes_per_seed": args.min_successful_train_episodes,
            "min_actions_with_at_least_5pct_share": args.min_active_actions,
        },
        "datasets": datasets,
        "failures": failures,
        "r02_capability_claim_allowed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    raise SystemExit(0 if eligible else 2)


if __name__ == "__main__":
    main()
