#!/usr/bin/env python3
"""Fail-closed three-seed aggregation for the R0.2 SILG baseline.

This is evaluation plumbing only.  It combines the immutable per-seed
Environment-first, End-to-end, and State-only artifacts, verifies matched
coverage, and reports task success, next-state loss, valid-action-masked action
accuracy, resources, and paired uncertainty without introducing a model or toy
mechanism.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path
from typing import Any

SEEDS = (1, 7, 19)
METHODS = ("environment_first", "end_to_end", "state_only")
CONDITIONS = ("all", "dynamics_holdout")


def read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def weighted(rows: list[tuple[int, float | None]]) -> float | None:
    valid = [(n, value) for n, value in rows if n > 0 and value is not None]
    if not valid:
        return None
    return sum(n * float(value) for n, value in valid) / sum(n for n, _ in valid)


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("empty percentile input")
    position = (len(ordered) - 1) * p
    lo = int(position)
    hi = min(lo + 1, len(ordered) - 1)
    fraction = position - lo
    return ordered[lo] * (1.0 - fraction) + ordered[hi] * fraction


def bootstrap_ci(values: list[float], seed: int = 20260726, draws: int = 10000) -> list[float] | None:
    if not values:
        return None
    rng = random.Random(seed)
    means = [statistics.fmean(rng.choice(values) for _ in values) for _ in range(draws)]
    return [percentile(means, 0.025), percentile(means, 0.975)]


def by_method(evaluations: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {str(row["method"]): row for row in evaluations}
    if set(result) != set(METHODS):
        raise ValueError(f"method topology mismatch: {sorted(result)}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    comparison: dict[int, dict[str, Any]] = {}
    policy: dict[int, dict[str, Any]] = {}
    online: dict[int, dict[str, Any]] = {}
    for seed in SEEDS:
        comparison[seed] = read(args.results / f"SILG_RTFM_R02_TYPED_COMPARISON_SEED_{seed}.json")
        policy[seed] = read(args.results / f"SILG_RTFM_R02_OFFLINE_POLICY_METRICS_SEED_{seed}.json")
        online[seed] = read(args.results / f"SILG_RTFM_R02_ONLINE_SEED_{seed}.json")
        for payload, label in ((comparison[seed], "comparison"), (policy[seed], "policy"), (online[seed], "online")):
            if int(payload.get("seed", -1)) != seed:
                raise ValueError(f"{label} seed mismatch for {seed}")

    configs = [comparison[seed]["config"] for seed in SEEDS]
    if any(config != configs[0] for config in configs[1:]):
        raise ValueError("R0.2 configuration changed across seeds")
    dataset_counts = [(comparison[seed]["dataset"]["n_train"], comparison[seed]["dataset"]["n_test"]) for seed in SEEDS]
    if len(set(dataset_counts)) != 1:
        raise ValueError(f"data amount changed across seeds: {dataset_counts}")

    summary: dict[str, Any] = {}
    for method in METHODS:
        next_state: dict[str, list[tuple[int, float | None]]] = {condition: [] for condition in CONDITIONS}
        action: dict[str, list[tuple[int, float | None]]] = {condition: [] for condition in CONDITIONS}
        training_seconds: list[float] = []
        peak_rss: list[int] = []
        checkpoint_bytes: list[int] = []
        inference_ms: list[float] = []
        online_runs: list[dict[str, Any]] = []

        for seed in SEEDS:
            comp_methods = by_method(comparison[seed]["evaluations"])
            policy_methods = by_method(policy[seed]["evaluations"])
            online_methods = by_method(online[seed]["runs"])
            comp = comp_methods[method]
            pol = policy_methods[method]
            run = online_methods[method]
            online_runs.append(run)
            for condition in CONDITIONS:
                comp_cell = comp["conditions"][condition]
                pol_cell = pol["conditions"][condition]
                next_state[condition].append((int(comp_cell["n"]), comp_cell["typed_next_state_loss"]))
                action[condition].append((int(pol_cell["n"]), pol_cell["policy_action_accuracy_valid_masked"]))
            training = comparison[seed]["training"]
            if method == "environment_first":
                training_seconds.append(float(training["environment_pretraining_seconds"]) + float(training["environment_first_language_seconds"]))
            elif method == "end_to_end":
                training_seconds.append(float(training["end_to_end_seconds"]))
            else:
                training_seconds.append(float(training["state_only_seconds"]))
            peak_rss.append(int(training["peak_rss_kib"]))
            checkpoint_bytes.append(int(pol["checkpoint"]["bytes"]))
            inference_ms.append(float(run["cpu_inference_ms_per_step"]))

        summary[method] = {
            "task_success_mean": statistics.fmean(float(run["win_rate"]) for run in online_runs),
            "return_mean": statistics.fmean(float(run["return_mean"]) for run in online_runs),
            "next_state_loss": {condition: weighted(next_state[condition]) for condition in CONDITIONS},
            "valid_action_masked_accuracy": {condition: weighted(action[condition]) for condition in CONDITIONS},
            "model_checkpoint_bytes_by_seed": checkpoint_bytes,
            "training_seconds_by_seed": training_seconds,
            "training_seconds_mean": statistics.fmean(training_seconds),
            "peak_rss_kib_by_seed": peak_rss,
            "peak_rss_kib_max": max(peak_rss),
            "cpu_inference_ms_per_step_by_seed": inference_ms,
            "cpu_inference_ms_per_step_mean": statistics.fmean(inference_ms),
        }

    paired: dict[str, Any] = {}
    for control in ("end_to_end", "state_only"):
        win_differences: list[float] = []
        return_differences: list[float] = []
        seed_win_gaps: list[float] = []
        seed_return_gaps: list[float] = []
        for seed in SEEDS:
            runs = by_method(online[seed]["runs"])
            env_records = {int(row["episode_seed"]): row for row in runs["environment_first"]["episode_records"]}
            ctl_records = {int(row["episode_seed"]): row for row in runs[control]["episode_records"]}
            if set(env_records) != set(ctl_records):
                raise ValueError(f"incomplete paired coverage for seed={seed}, control={control}")
            local_win = [float(env_records[key]["win"]) - float(ctl_records[key]["win"]) for key in sorted(env_records)]
            local_return = [float(env_records[key]["return"]) - float(ctl_records[key]["return"]) for key in sorted(env_records)]
            win_differences.extend(local_win)
            return_differences.extend(local_return)
            seed_win_gaps.append(statistics.fmean(local_win))
            seed_return_gaps.append(statistics.fmean(local_return))
        paired[control] = {
            "paired_instances": len(win_differences),
            "task_success_mean_gap": statistics.fmean(win_differences),
            "task_success_bootstrap_95ci": bootstrap_ci(win_differences),
            "task_success_min_seed_gap": min(seed_win_gaps),
            "return_mean_gap": statistics.fmean(return_differences),
            "return_bootstrap_95ci": bootstrap_ci(return_differences, seed=20260727),
            "return_min_seed_gap": min(seed_return_gaps),
        }

    payload = {
        "status": "r02_three_seed_aggregation_complete",
        "classification": "R0.2 matched public-environment adaptation; not a novelty or capability-progress claim",
        "seeds": list(SEEDS),
        "methods": list(METHODS),
        "config": configs[0],
        "data_amount_per_seed": {"train_rows": dataset_counts[0][0], "test_rows": dataset_counts[0][1]},
        "metrics": summary,
        "paired_environment_first_minus_control": paired,
        "holdout_scope": {
            "dynamics": "reported when generator-manifest-assigned cells are non-empty",
            "entity": "inapplicable for RTFM S1",
            "language_form": "inapplicable for RTFM S1",
        },
        "claims": {"new_architecture": False, "novelty": False, "intelligence_principle": False, "capability_progress": False},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
