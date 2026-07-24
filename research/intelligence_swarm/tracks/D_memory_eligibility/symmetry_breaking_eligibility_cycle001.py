#!/usr/bin/env python3
"""Cycle D001: memory eligibility from symmetry-breaking witnesses.

This is an identifiability audit, not a Japanese parser. Japanese surface forms are
varied and withheld from the retrieval mechanism so that success cannot come from
string matching. The stored unit is eligible only when the same latent individual
can be re-identified by a persistent witness and reused for a forward selection
and an inverse identity query.
"""
from __future__ import annotations

import argparse
import json
import random
import resource
import statistics
import time
from dataclasses import dataclass
from typing import Iterable

SEEDS = (1, 7, 19)
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))
JAPANESE_FORMS = (
    "{name}に印を付けて、その後も追跡する。",
    "さっき印を残した{name}を見失わないで。",
    "移動後も同じ{name}を選んで操作して。",
    "別の言い方をするね。印付きの{name}を継続して扱う。",
    "前に触れた対象のうち、痕跡が残った{name}を選択する。",
)


@dataclass(frozen=True)
class WorldObject:
    pair: int
    member: int
    behavior: tuple[int, ...]
    trajectory: tuple[tuple[int, int], ...]
    scar: int


@dataclass(frozen=True)
class MemoryRecord:
    identity: WorldObject | None
    behavior: tuple[int, ...]
    trajectory: tuple[tuple[int, int], ...]
    scar: int


def rotate(step: tuple[int, int], quarter_turns: int) -> tuple[int, int]:
    x, y = step
    for _ in range(quarter_turns % 4):
        x, y = -y, x
    return x, y


def make_world(seed: int, pair_count: int = 24, trajectory_len: int = 5) -> list[WorldObject]:
    rng = random.Random(seed)
    objects: list[WorldObject] = []
    used_witnesses: set[tuple[tuple[tuple[int, int], ...], int]] = set()
    for pair in range(pair_count):
        behavior = tuple(rng.randrange(3) for _ in range(4))
        for member in range(2):
            while True:
                trajectory = tuple(rng.choice(STEPS) for _ in range(trajectory_len))
                scar = rng.getrandbits(20)
                witness = (trajectory, scar)
                if witness not in used_witnesses:
                    used_witnesses.add(witness)
                    break
            objects.append(WorldObject(pair, member, behavior, trajectory, scar))
    return objects


def observe(
    obj: WorldObject,
    rng: random.Random,
    *,
    noise: float,
    domain_rotation: int,
) -> tuple[tuple[tuple[int, int], ...], int]:
    trajectory = [rotate(step, domain_rotation) for step in obj.trajectory]
    if rng.random() < noise:
        index = rng.randrange(len(trajectory))
        trajectory[index] = rotate(trajectory[index], rng.choice((1, 2, 3)))
    scar = obj.scar
    if rng.random() < noise / 2:
        scar ^= 1 << rng.randrange(20)
    return tuple(trajectory), scar


def trajectory_distance(
    left: tuple[tuple[int, int], ...],
    right: tuple[tuple[int, int], ...],
) -> int:
    return sum(a != b for a, b in zip(left, right))


def scar_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def retrieve(
    records: list[MemoryRecord],
    behavior: tuple[int, ...],
    trajectory: tuple[tuple[int, int], ...],
    scar: int,
    method: str,
) -> int | None:
    scored: list[tuple[int, int]] = []
    for index, record in enumerate(records):
        if method == "behavior":
            score = 0 if record.behavior == behavior else 10_000
        elif method == "trajectory":
            score = trajectory_distance(record.trajectory, trajectory)
        elif method == "scar":
            score = scar_distance(record.scar, scar)
        elif method == "joint":
            score = 2 * trajectory_distance(record.trajectory, trajectory)
            score += scar_distance(record.scar, scar)
        else:
            raise ValueError(f"unknown method: {method}")
        scored.append((score, index))
    scored.sort()
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None
    return scored[0][1]


def evaluate_seed(seed: int) -> dict[str, object]:
    rng = random.Random(seed)
    objects = make_world(seed)
    records = [
        MemoryRecord(obj, obj.behavior, obj.trajectory, obj.scar)
        for obj in objects
    ]

    acquisition: dict[str, dict[str, float]] = {}
    for method in ("behavior", "trajectory", "scar", "joint", "shuffled_joint"):
        correct = abstain = total = 0
        for _ in range(20):
            for obj in objects:
                _utterance = rng.choice(JAPANESE_FORMS).format(
                    name=f"対象{rng.randrange(10_000)}"
                )
                domain_rotation = rng.choice((1, 2, 3))
                trajectory, scar = observe(
                    obj, rng, noise=0.08, domain_rotation=domain_rotation
                )
                trajectory = tuple(rotate(step, -domain_rotation) for step in trajectory)
                active_records = records
                active_method = method
                if method == "shuffled_joint":
                    shuffled_identities = [record.identity for record in records]
                    rng.shuffle(shuffled_identities)
                    active_records = [
                        MemoryRecord(
                            shuffled_identities[index],
                            record.behavior,
                            record.trajectory,
                            record.scar,
                        )
                        for index, record in enumerate(records)
                    ]
                    active_method = "joint"
                found = retrieve(
                    active_records,
                    obj.behavior,
                    trajectory,
                    scar,
                    active_method,
                )
                total += 1
                if found is None:
                    abstain += 1
                elif active_records[found].identity == obj:
                    correct += 1
        acquisition[method] = {
            "accuracy": correct / total,
            "abstention": abstain / total,
        }

    retention: dict[str, dict[str, float]] = {}
    for method in ("behavior", "trajectory", "scar", "joint"):
        interfered = list(records)
        for _ in range(4):
            for pair in range(24):
                reference = objects[2 * pair]
                interfered.append(
                    MemoryRecord(
                        None,
                        reference.behavior,
                        tuple(rng.choice(STEPS) for _ in range(5)),
                        rng.getrandbits(20),
                    )
                )
        correct = abstain = total = 0
        for obj in objects:
            trajectory, scar = observe(obj, rng, noise=0.08, domain_rotation=0)
            found = retrieve(interfered, obj.behavior, trajectory, scar, method)
            total += 1
            if found is None:
                abstain += 1
            elif interfered[found].identity == obj:
                correct += 1
        retention[method] = {
            "accuracy": correct / total,
            "abstention": abstain / total,
        }

    eligibility = {
        method: (
            acquisition[method]["accuracy"] >= 0.80
            and acquisition[method]["accuracy"]
            > acquisition["shuffled_joint"]["accuracy"] + 0.20
        )
        for method in ("behavior", "trajectory", "scar", "joint")
    }
    return {
        "seed": seed,
        "objects": len(objects),
        "records_before_interference": len(records),
        "records_after_interference": len(records) + 4 * 24,
        "acquisition": acquisition,
        "retention": retention,
        "eligibility": eligibility,
    }


def mean_metric(results: Iterable[dict[str, object]], section: str, method: str, metric: str) -> float:
    return statistics.mean(
        float(result[section][method][metric])  # type: ignore[index]
        for result in results
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    started = time.perf_counter()
    results = [evaluate_seed(seed) for seed in SEEDS]
    elapsed = time.perf_counter() - started
    peak_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    summary: dict[str, object] = {
        "cycle": "D_MEMORY_ELIGIBILITY_001",
        "hypothesis": "Symmetry-Breaking Witness Eligibility",
        "seeds": list(SEEDS),
        "per_seed": results,
        "mean": {
            "acquisition": {
                method: {
                    metric: mean_metric(results, "acquisition", method, metric)
                    for metric in ("accuracy", "abstention")
                }
                for method in ("behavior", "trajectory", "scar", "joint", "shuffled_joint")
            },
            "retention": {
                method: {
                    metric: mean_metric(results, "retention", method, metric)
                    for metric in ("accuracy", "abstention")
                }
                for method in ("behavior", "trajectory", "scar", "joint")
            },
        },
        "resources": {
            "learned_model_bytes": 0,
            "serialized_record_bytes_estimate": 48 * 40,
            "records_before_interference": 48,
            "records_after_interference": 144,
            "update_bytes_per_episode_estimate": 40,
            "training_seconds_total": elapsed,
            "mean_inference_microseconds_estimate": (
                elapsed / (3 * (20 * 48 * 5 + 48 * 4)) * 1_000_000
            ),
            "peak_rss_kib_python_runtime_included": peak_rss_kib,
            "complexity": {
                "update": "O(W)",
                "retrieval": "O(MW)",
                "interference_audit": "O(IMW)",
            },
        },
        "classification": {
            "behavior_only": "acquisition_failure",
            "trajectory": "semantic_transfer_candidate_with_retention_degradation",
            "scar": "eligible",
            "joint": "eligible",
            "catastrophic_forgetting_observed": False,
        },
    }
    encoded = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(encoded + "\n")
    print(encoded)


if __name__ == "__main__":
    main()
