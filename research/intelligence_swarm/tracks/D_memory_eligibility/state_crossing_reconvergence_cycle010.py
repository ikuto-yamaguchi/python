from __future__ import annotations

import itertools
import json
import random
import resource
import time
from pathlib import Path

FUNCS = {
    "const0": lambda x: 0,
    "const1": lambda x: 1,
    "identity": lambda x: x,
    "negation": lambda x: 1 - x,
}
TOKENS = ("ka", "mi", "ru")
SEEDS = (1, 7, 19)
WORLDS = [dict(zip(TOKENS, fs)) for fs in itertools.permutations(FUNCS, 3)]


def survivors(witnesses):
    return [
        world
        for world in WORLDS
        if all(FUNCS[world[token]](before) == after for token, before, after in witnesses)
    ]


def prospective_accuracy(candidates, truth):
    if not candidates:
        return 0.0
    correct = 0
    for token in TOKENS:
        for before in (0, 1):
            votes = [FUNCS[c[token]](before) for c in candidates]
            prediction = int(sum(votes) > len(votes) / 2)
            correct += prediction == FUNCS[truth[token]](before)
    return correct / 6


def mapping_accuracy(candidates, truth):
    if not candidates:
        return 0.0
    correct = 0
    for token in TOKENS:
        counts = {}
        for candidate in candidates:
            counts[candidate[token]] = counts.get(candidate[token], 0) + 1
        prediction = max(sorted(counts), key=counts.get)
        correct += prediction == truth[token]
    return correct / 3


def run_seed(seed):
    rng = random.Random(seed)
    truth = rng.choice(WORLDS)
    complete = [(t, x, FUNCS[truth[t]](x)) for t in TOKENS for x in (0, 1)]

    # Independent episodes with identical causal coverage but disjoint episode identities.
    set1 = complete.copy()
    set2 = complete.copy()
    rng.shuffle(set1)
    rng.shuffle(set2)

    random1 = []
    random2 = []
    for target in (random1, random2):
        for _ in range(6):
            token = rng.choice(TOKENS)
            before = rng.choice((0, 1))
            target.append((token, before, FUNCS[truth[token]](before)))

    static1 = [(t, 0, FUNCS[truth[t]](0)) for t in TOKENS for _ in range(2)]
    static2 = [(t, 0, FUNCS[truth[t]](0)) for t in TOKENS for _ in range(2)]

    active1, active2 = survivors(set1), survivors(set2)
    random_candidates1, random_candidates2 = survivors(random1), survivors(random2)
    random_intersection = [w for w in random_candidates1 if w in random_candidates2]
    static_candidates1, static_candidates2 = survivors(static1), survivors(static2)
    static_intersection = [w for w in static_candidates1 if w in static_candidates2]

    conflict = set1.copy()
    token, before, after = conflict[0]
    conflict[0] = (token, before, 1 - after)
    conflict_candidates = survivors(conflict)
    conflict_union = survivors(conflict + set2)

    return {
        "seed": seed,
        "active_set1_survivors": len(active1),
        "active_set2_survivors": len(active2),
        "active_same_unique": int(len(active1) == len(active2) == 1 and active1[0] == active2[0]),
        "active_prospective": prospective_accuracy(active1, truth),
        "active_program_mapping": mapping_accuracy(active1, truth),
        "random_set1_survivors": len(random_candidates1),
        "random_set2_survivors": len(random_candidates2),
        "random_intersection_survivors": len(random_intersection),
        "random_prospective": prospective_accuracy(random_intersection, truth),
        "random_program_mapping": mapping_accuracy(random_intersection, truth),
        "state_static_set1_survivors": len(static_candidates1),
        "state_static_intersection_survivors": len(static_intersection),
        "state_static_prospective": prospective_accuracy(static_candidates1, truth),
        "state_static_program_mapping": mapping_accuracy(static_candidates1, truth),
        "conflict_set_survivors": len(conflict_candidates),
        "conflict_union_survivors": len(conflict_union),
        "conflict_detected": int(len(conflict_union) == 0),
    }


def main():
    started = time.perf_counter()
    per_seed = [run_seed(seed) for seed in SEEDS]
    keys = [key for key in per_seed[0] if key != "seed"]
    mean = {key: sum(row[key] for row in per_seed) / len(per_seed) for key in keys}
    result = {
        "hypothesis": "Independent State-Crossing Reconvergence before Operation Memory Eligibility",
        "seeds": list(SEEDS),
        "candidate_worlds": len(WORLDS),
        "witnesses_per_independent_set": 6,
        "per_seed": per_seed,
        "mean": mean,
        "runtime_seconds": time.perf_counter() - started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "model_upper_bound_bytes": len(WORLDS) * len(TOKENS) * 8,
        "estimated_probe_evaluations": len(SEEDS) * 2 * 6 * len(WORLDS),
        "formal_memory_eligible_units": 0,
        "gate_reason": "operation-family/state-interface/unary-scope oracle remains",
    }
    output = Path(__file__).with_name("MEASUREMENTS_CYCLE_010.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
