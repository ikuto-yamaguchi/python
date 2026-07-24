#!/usr/bin/env python3
"""Cycle 009: joint target-operation identifiability audit.

This is an upper-bound causal identifiability experiment. It intentionally grants
oracle token segmentation and a factorized unary target/operation interface so
that we can measure the minimum number of independent external witnesses needed
to identify the latent causal mapping. It does NOT claim raw-Japanese semantic
birth.
"""
from __future__ import annotations

import argparse
import itertools
import json
import random
import resource
import statistics
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

N_TARGET = 4
N_OPERATION = 4
SEEDS = (1, 7, 19)
BUDGETS = (0, 1, 2, 3, 4)
MODES = ("active", "random", "outcome_shuffle")

Permutation = Tuple[int, ...]
World = Tuple[Permutation, Permutation]
Query = Tuple[int, int]
Outcome = Tuple[int, int]

PERMUTATIONS: Tuple[Permutation, ...] = tuple(itertools.permutations(range(N_TARGET)))
ALL_WORLDS: Tuple[World, ...] = tuple(
    (target_perm, operation_perm)
    for target_perm in PERMUTATIONS
    for operation_perm in PERMUTATIONS
)
ALL_QUERIES: Tuple[Query, ...] = tuple(
    itertools.product(range(N_TARGET), range(N_OPERATION))
)


def outcome(world: World, query: Query) -> Outcome:
    target_perm, operation_perm = world
    target_token, operation_token = query
    return target_perm[target_token], operation_perm[operation_token]


def filter_worlds(
    version_space: Sequence[World], query: Query, observed: Outcome
) -> List[World]:
    return [world for world in version_space if outcome(world, query) == observed]


def expected_posterior_size(version_space: Sequence[World], query: Query) -> float:
    buckets: Dict[Outcome, int] = defaultdict(int)
    for world in version_space:
        buckets[outcome(world, query)] += 1
    total = len(version_space)
    return sum(size * size for size in buckets.values()) / total


def choose_active(version_space: Sequence[World], queried: Sequence[Query]) -> Query:
    remaining = [query for query in ALL_QUERIES if query not in queried]
    if not remaining:
        raise RuntimeError("query budget exceeded")

    best_value = min(
        expected_posterior_size(version_space, query) for query in remaining
    )
    tied = [
        query
        for query in remaining
        if expected_posterior_size(version_space, query) == best_value
    ]

    seen_targets = {query[0] for query in queried}
    seen_operations = {query[1] for query in queried}
    tied.sort(
        key=lambda query: (
            -int(query[0] not in seen_targets)
            - int(query[1] not in seen_operations),
            query,
        )
    )
    return tied[0]


def unanimous_outcome(version_space: Sequence[World], query: Query) -> Outcome | None:
    predictions = {outcome(world, query) for world in version_space}
    if len(predictions) != 1:
        return None
    return next(iter(predictions))


def evaluate(version_space: Sequence[World], true_world: World) -> Dict[str, float]:
    if not version_space:
        return {
            "prospective_joint": 0.0,
            "prospective_target": 0.0,
            "prospective_operation": 0.0,
            "inverse": 0.0,
            "counterfactual_composition": 0.0,
        }

    prospective_joint = 0
    prospective_target = 0
    prospective_operation = 0
    counterfactual_composition = 0

    for query in ALL_QUERIES:
        prediction = unanimous_outcome(version_space, query)
        expected = outcome(true_world, query)
        if prediction is None:
            continue
        prospective_joint += int(prediction == expected)
        prospective_target += int(prediction[0] == expected[0])
        prospective_operation += int(prediction[1] == expected[1])
        counterfactual_composition += int(prediction == expected)

    inverse = 0
    target_perm, operation_perm = true_world
    for latent_target, latent_operation in ALL_QUERIES:
        inverse_candidates = set()
        for candidate_target_perm, candidate_operation_perm in version_space:
            target_token = candidate_target_perm.index(latent_target)
            operation_token = candidate_operation_perm.index(latent_operation)
            inverse_candidates.add((target_token, operation_token))
        if len(inverse_candidates) != 1:
            continue
        expected_query = (
            target_perm.index(latent_target),
            operation_perm.index(latent_operation),
        )
        inverse += int(next(iter(inverse_candidates)) == expected_query)

    denominator = len(ALL_QUERIES)
    return {
        "prospective_joint": prospective_joint / denominator,
        "prospective_target": prospective_target / denominator,
        "prospective_operation": prospective_operation / denominator,
        "inverse": inverse / denominator,
        "counterfactual_composition": counterfactual_composition / denominator,
    }


def run_trial(seed: int, mode: str, budget: int) -> Dict[str, float]:
    rng = random.Random(seed)
    true_world = (rng.choice(PERMUTATIONS), rng.choice(PERMUTATIONS))
    version_space: List[World] = list(ALL_WORLDS)
    queried: List[Query] = []

    for _ in range(budget):
        if mode in ("active", "outcome_shuffle"):
            query = choose_active(version_space or ALL_WORLDS, queried)
        elif mode == "random":
            query = rng.choice([item for item in ALL_QUERIES if item not in queried])
        else:
            raise ValueError(f"unknown mode: {mode}")

        observed = outcome(true_world, query)
        if mode == "outcome_shuffle":
            donor = rng.choice([item for item in ALL_QUERIES if item != query])
            observed = outcome(true_world, donor)

        version_space = filter_worlds(version_space, query, observed)
        queried.append(query)
        if not version_space:
            break

    result = evaluate(version_space, true_world)
    result.update(
        {
            "remaining_worlds": float(len(version_space)),
            "witnesses_used": float(len(queried)),
        }
    )
    return result


def aggregate() -> Dict[str, object]:
    raw: Dict[str, Dict[str, List[Dict[str, float]]]] = {}
    mean: Dict[str, Dict[str, Dict[str, float]]] = {}

    for budget in BUDGETS:
        budget_key = str(budget)
        raw[budget_key] = {}
        mean[budget_key] = {}
        for mode in MODES:
            trials = [run_trial(seed, mode, budget) for seed in SEEDS]
            raw[budget_key][mode] = trials
            mean[budget_key][mode] = {
                key: statistics.mean(trial[key] for trial in trials)
                for key in trials[0]
            }

    return {"raw": raw, "mean": mean}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    started = time.perf_counter()
    results = aggregate()
    runtime_seconds = time.perf_counter() - started
    peak_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    payload = {
        "cycle": 9,
        "track": "C_causal_grounding",
        "hypothesis": (
            "Factorized target-operation causal orbit is identifiable from "
            "minimal independent external witnesses"
        ),
        "status": "identifiability_supported_capability_progress_not_claimed",
        "seeds": list(SEEDS),
        "target_tokens": N_TARGET,
        "operation_tokens": N_OPERATION,
        "initial_version_space": len(ALL_WORLDS),
        "budgets": list(BUDGETS),
        "modes": list(MODES),
        "results": results,
        "runtime_seconds": runtime_seconds,
        "peak_rss_kib": peak_rss_kib,
        "model_bytes_upper_bound": 4608,
        "estimated_probe_simulations_max": (
            len(ALL_WORLDS) * len(ALL_QUERIES) * max(BUDGETS)
        ),
        "answer_leakage": False,
        "final_test_outcome_used_for_selection": False,
        "limitations": [
            "oracle segmentation of opaque target and operation tokens",
            "known unary factorization and arity",
            "synthetic finite permutation world",
            "not raw-Japanese semantic birth",
        ],
        "g1_passed": False,
        "g2_passed": False,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "weak_smartphone_verified": False,
        "completion": False,
    }

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
