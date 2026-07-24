from __future__ import annotations

import itertools
import json
import math
import random
import resource
import statistics
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class World:
    n_objects: int = 4
    n_properties: int = 3


def transition(state: list[list[int]], action: tuple[int, int, int]) -> list[list[int]]:
    obj, prop, value = action
    result = [row[:] for row in state]
    result[obj][prop] = value
    return result


def permute_action(action: tuple[int, int, int], object_perm: dict[int, int], property_perm: dict[int, int]) -> tuple[int, int, int]:
    obj, prop, value = action
    return object_perm[obj], property_perm[prop], value


def permute_state(state: list[list[int]], object_perm: dict[int, int], property_perm: dict[int, int]) -> list[list[int]]:
    result = [[0] * len(state[0]) for _ in state]
    for obj in range(len(state)):
        for prop in range(len(state[0])):
            result[object_perm[obj]][property_perm[prop]] = state[obj][prop]
    return result


def protocol_observations(protocol: str, rng: random.Random, world: World):
    # 完全対称な初期worldを使い、観測プロトコル自身がどこまで対称性を壊せるかを監査する。
    base = [[0 for _ in range(world.n_properties)] for _ in range(world.n_objects)]
    actions = [
        (rng.randrange(world.n_objects), rng.randrange(world.n_properties), rng.randrange(2))
        for _ in range(8)
    ]
    observations = []

    if protocol == "passive":
        action = actions[0]
        observations.append((base, action, transition(base, action)))
    elif protocol == "repeat":
        for action in actions[:4]:
            observations.append((base, action, transition(base, action)))
    elif protocol == "object_swap":
        _, prop, value = actions[0]
        for obj in range(world.n_objects):
            action = (obj, prop, value)
            observations.append((base, action, transition(base, action)))
    elif protocol == "object_value":
        _, prop, _ = actions[0]
        for obj in range(world.n_objects):
            for value in (0, 1):
                action = (obj, prop, value)
                observations.append((base, action, transition(base, action)))
    elif protocol == "selective_full":
        for obj in range(world.n_objects):
            for prop in range(world.n_properties):
                for value in (0, 1):
                    action = (obj, prop, value)
                    observations.append((base, action, transition(base, action)))
    else:
        raise ValueError(f"unknown protocol: {protocol}")

    return observations


def automorphism_count(observations, world: World) -> int:
    count = 0
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
    original = sorted(map(canonical, observations))

    for object_tuple in itertools.permutations(range(world.n_objects)):
        object_perm = {index: object_tuple[index] for index in range(world.n_objects)}
        for property_tuple in itertools.permutations(range(world.n_properties)):
            property_perm = {index: property_tuple[index] for index in range(world.n_properties)}
            mapped = []
            for before, action, after in observations:
                mapped.append(
                    (
                        permute_state(before, object_perm, property_perm),
                        permute_action(action, object_perm, property_perm),
                        permute_state(after, object_perm, property_perm),
                    )
                )
            if sorted(map(canonical, mapped)) == original:
                count += 1
    return count


def run_seed(seed: int):
    rng = random.Random(seed)
    world = World()
    result = {}
    for protocol in ("passive", "repeat", "object_swap", "object_value", "selective_full"):
        observations = protocol_observations(protocol, rng, world)
        started = time.perf_counter()
        automorphisms = automorphism_count(observations, world)
        elapsed = time.perf_counter() - started
        result[protocol] = {
            "automorphisms": automorphisms,
            "residual_identity_bits": math.log2(automorphisms),
            "observations": len(observations),
            "audit_sec": elapsed,
        }
    return result


def main() -> None:
    seeds = (1, 7, 19)
    started = time.perf_counter()
    rows = {str(seed): run_seed(seed) for seed in seeds}
    mean = {}
    for protocol in ("passive", "repeat", "object_swap", "object_value", "selective_full"):
        mean[protocol] = {
            key: statistics.mean(rows[str(seed)][protocol][key] for seed in seeds)
            for key in ("automorphisms", "residual_identity_bits", "observations", "audit_sec")
        }

    print(
        json.dumps(
            {
                "seeds": rows,
                "mean": mean,
                "elapsed_sec": time.perf_counter() - started,
                "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "model_bytes": 0,
                "estimated_ops": "O(n_object! * n_property! * Q * n_object * n_property)",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
