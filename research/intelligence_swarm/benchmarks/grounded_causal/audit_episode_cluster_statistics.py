#!/usr/bin/env python3
"""Episode-clustered paired statistics for grounded-causal R0 evaluations."""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from evaluation_contract import (
    REQUIRED_CONTROL_METHODS,
    adapt_dataset,
    instance_fingerprint,
    read_jsonl,
)


def _cell(row: dict[str, Any]) -> tuple[int, str, str, str]:
    return (int(row["seed"]), str(row["domain"]), str(row["split"]).lower(), str(row["condition"]))


def _percentile(values: list[float], q: float) -> float:
    values = sorted(values)
    if not values:
        return math.nan
    return values[min(len(values) - 1, max(0, int(q * len(values))))]


def _hierarchical_bootstrap(
    clusters: dict[tuple[int, str, str, str], dict[str, list[float]]],
    trials: int = 5000,
    seed: int = 20260725,
) -> tuple[float, float]:
    cells = sorted(clusters)
    if not cells:
        return math.nan, math.nan
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(trials):
        sampled_values: list[float] = []
        for cell in [cells[rng.randrange(len(cells))] for _ in cells]:
            episodes = sorted(clusters[cell])
            if not episodes:
                continue
            for episode in [episodes[rng.randrange(len(episodes))] for _ in episodes]:
                values = clusters[cell][episode]
                sampled_values.extend(values)
        if sampled_values:
            estimates.append(statistics.mean(sampled_values))
    return _percentile(estimates, .025), _percentile(estimates, .975)


def _episode_signflip_p(episode_means: list[float], trials: int = 20000, seed: int = 20260725) -> float:
    values = [value for value in episode_means if value != 0]
    if not values:
        return 1.0
    observed = abs(statistics.mean(values))
    rng = random.Random(seed)
    if len(values) <= 18:
        total = 1 << len(values)
        extreme = 0
        for mask in range(total):
            estimate = abs(statistics.mean(value if (mask >> i) & 1 else -value for i, value in enumerate(values)))
            extreme += estimate >= observed - 1e-15
        return extreme / total
    extreme = 0
    for _ in range(trials):
        estimate = abs(statistics.mean(value if rng.random() < .5 else -value for value in values))
        extreme += estimate >= observed - 1e-15
    return (extreme + 1) / (trials + 1)


def audit(data: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    rows = adapt_dataset(data)
    by_id = {str(row["instance_id"]): row for row in rows}
    eval_ids = {iid for iid, row in by_id.items() if str(row["split"]).lower() != "train"}
    errors: list[str] = []

    missing_episode = sorted(iid for iid in eval_ids if not by_id[iid].get("episode_id"))
    if missing_episode:
        errors.append(f"evaluation rows missing episode_id: {len(missing_episode)}")

    outcomes: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)
    seen: set[tuple[str, str]] = set()
    for index, pred in enumerate(predictions, 1):
        iid = str(pred.get("instance_id", ""))
        method = str(pred.get("method", ""))
        if iid not in eval_ids:
            continue
        if (iid, method) in seen:
            errors.append(f"prediction row {index}: duplicate {iid}/{method}")
            continue
        seen.add((iid, method))
        gold = by_id[iid]
        if str(pred.get("instance_fingerprint", "")) != instance_fingerprint(gold):
            errors.append(f"prediction row {index}: fingerprint mismatch {iid}/{method}")
        outcomes[method][iid] = {
            "action": float(pred.get("pred_action") == gold["gold_action"]),
            "prospective": float(pred.get("pred_state_after") == gold["gold_state_after"]),
        }

    required = {"correct"} | REQUIRED_CONTROL_METHODS
    for method in sorted(required):
        missing = eval_ids - set(outcomes.get(method, {}))
        if missing:
            errors.append(f"method {method}: incomplete coverage ({len(missing)} missing)")

    comparisons: dict[str, Any] = {}
    for control in sorted(REQUIRED_CONTROL_METHODS):
        comparisons[control] = {}
        shared = sorted(eval_ids & set(outcomes.get("correct", {})) & set(outcomes.get(control, {})))
        for metric in ("action", "prospective"):
            clusters: dict[tuple[int, str, str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
            for iid in shared:
                row = by_id[iid]
                episode = str(row.get("episode_id", ""))
                if not episode:
                    continue
                clusters[_cell(row)][episode].append(outcomes["correct"][iid][metric] - outcomes[control][iid][metric])
            episode_means = [statistics.mean(values) for episodes in clusters.values() for values in episodes.values()]
            cell_means = [statistics.mean([v for values in episodes.values() for v in values]) for episodes in clusters.values()]
            low, high = _hierarchical_bootstrap(clusters)
            comparisons[control][metric] = {
                "paired_cells": len(clusters),
                "paired_episodes": len(episode_means),
                "paired_steps": sum(len(values) for episodes in clusters.values() for values in episodes.values()),
                "step_weighted_mean_gap": statistics.mean([v for episodes in clusters.values() for values in episodes.values() for v in values]) if clusters else math.nan,
                "episode_equal_weight_mean_gap": statistics.mean(episode_means) if episode_means else math.nan,
                "minimum_cell_gap": min(cell_means) if cell_means else math.nan,
                "episode_cluster_bootstrap_ci95_low": low,
                "episode_cluster_bootstrap_ci95_high": high,
                "episode_signflip_p_two_sided": _episode_signflip_p(episode_means),
                "passes_episode_cluster_ci_excludes_zero": low > 0 if not math.isnan(low) else False,
            }

    return {
        "valid": not errors,
        "errors": errors,
        "classification": "episode_cluster_statistics_valid" if not errors else "initial_reproduction_failure",
        "episode_id_required": True,
        "same_instance_required": True,
        "comparisons_vs_correct": comparisons,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(read_jsonl(args.data), read_jsonl(args.predictions))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
