from __future__ import annotations

import hashlib
import itertools
import json
import resource
import time
from typing import Iterable


def transition(state: tuple[int, ...], target: int) -> tuple[int, ...]:
    result = list(state)
    result[target] = 1 - result[target]
    return tuple(result)


def observable_table(n_variables: int) -> list[tuple[tuple[int, ...], str, tuple[int, ...]]]:
    utterances = [f"u{i}" for i in range(n_variables)]
    states = list(itertools.product((0, 1), repeat=n_variables))
    return [
        (state, utterance, transition(state, utterance_index))
        for utterance_index, utterance in enumerate(utterances)
        for state in states
    ]


def jointly_relabel(
    rows: Iterable[tuple[tuple[int, ...], str, tuple[int, ...]]],
    permutation: tuple[int, ...],
) -> list[tuple[tuple[int, ...], str, tuple[int, ...]]]:
    inverse = {old: new for new, old in enumerate(permutation)}
    relabelled = []
    for state, utterance, next_state in rows:
        utterance_index = int(utterance[1:])
        relabelled.append(
            (
                tuple(state[index] for index in permutation),
                f"u{inverse[utterance_index]}",
                tuple(next_state[index] for index in permutation),
            )
        )
    return sorted(relabelled)


def run(n_variables: int = 3) -> dict[str, object]:
    started = time.perf_counter()
    rows = observable_table(n_variables)
    permutations = list(itertools.permutations(range(n_variables)))
    table_hashes = {
        hashlib.sha256(repr(jointly_relabel(rows, permutation)).encode("utf-8")).hexdigest()
        for permutation in permutations
    }
    return {
        "latent_variables": n_variables,
        "joint_permutations": len(permutations),
        "distinct_observable_tables_after_joint_relabeling": len(table_hashes),
        "exact_latent_names_identifiable": False,
        "exact_utterance_target_names_identifiable": False,
        "identifiable_up_to_joint_permutation": len(table_hashes) == 1,
        "runtime_seconds": time.perf_counter() - started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "model_bytes": 0,
        "seeds_required": False,
        "reason_seeds_not_applicable": "exact finite enumeration, no stochastic estimator",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
