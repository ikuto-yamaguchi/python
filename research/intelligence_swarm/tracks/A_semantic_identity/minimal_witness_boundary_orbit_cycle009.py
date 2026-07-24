from __future__ import annotations

import itertools
import json
import random
import resource
import statistics
import time
from dataclasses import dataclass

SEEDS = (1, 7, 19)
OBJECTS = (0, 1, 2, 3)
OPS = (0, 1, 2, 3)
OBJ_TOKENS = ("ガル", "ネプ", "ソマ", "リク")
OP_TOKENS = ("フセル", "マワス", "ズラス", "ヒラク")


@dataclass(frozen=True)
class Hypothesis:
    split: int
    orientation: int  # 0: left=object, 1: left=operation
    object_map: tuple[int, ...]
    operation_map: tuple[int, ...]


def raw_command(object_id: int, operation_id: int, reverse: bool = False) -> str:
    if reverse:
        return OP_TOKENS[operation_id] + OBJ_TOKENS[object_id]
    return OBJ_TOKENS[object_id] + OP_TOKENS[operation_id]


def parse(command: str, split: int, orientation: int) -> tuple[str, str]:
    left, right = command[:split], command[split:]
    return (left, right) if orientation == 0 else (right, left)


def discover_schemes(corpus: list[str]) -> list[tuple[int, int, tuple[str, ...], tuple[str, ...]]]:
    schemes = []
    for split in range(1, len(corpus[0])):
        for orientation in (0, 1):
            parses = [parse(command, split, orientation) for command in corpus]
            object_tokens = tuple(sorted({obj for obj, _ in parses}))
            operation_tokens = tuple(sorted({op for _, op in parses}))
            if len(object_tokens) == 4 and len(operation_tokens) == 4:
                schemes.append((split, orientation, object_tokens, operation_tokens))
    return schemes


def enumerate_hypotheses(corpus: list[str]) -> list[Hypothesis]:
    hypotheses = []
    for split, orientation, _, _ in discover_schemes(corpus):
        for object_map in itertools.permutations(OBJECTS):
            for operation_map in itertools.permutations(OPS):
                hypotheses.append(Hypothesis(split, orientation, object_map, operation_map))
    return hypotheses


def predict(hypothesis: Hypothesis, command: str, corpus: list[str]) -> tuple[int, int] | None:
    scheme = None
    for split, orientation, object_tokens, operation_tokens in discover_schemes(corpus):
        if split == hypothesis.split and orientation == hypothesis.orientation:
            scheme = object_tokens, operation_tokens
            break
    if scheme is None:
        return None
    object_tokens, operation_tokens = scheme
    object_token, operation_token = parse(command, hypothesis.split, hypothesis.orientation)
    if object_token not in object_tokens or operation_token not in operation_tokens:
        return None
    return (
        hypothesis.object_map[object_tokens.index(object_token)],
        hypothesis.operation_map[operation_tokens.index(operation_token)],
    )


def filter_hypotheses(
    hypotheses: list[Hypothesis], command: str, outcome: tuple[int, int], corpus: list[str]
) -> list[Hypothesis]:
    return [hypothesis for hypothesis in hypotheses if predict(hypothesis, command, corpus) == outcome]


def choose_active(hypotheses: list[Hypothesis], candidates: list[str], corpus: list[str]) -> str:
    best = None
    for command in candidates:
        buckets: dict[tuple[int, int] | None, int] = {}
        for hypothesis in hypotheses:
            value = predict(hypothesis, command, corpus)
            buckets[value] = buckets.get(value, 0) + 1
        expected_remaining = sum(count * count for count in buckets.values()) / max(1, len(hypotheses))
        key = expected_remaining, command
        if best is None or key < best[0]:
            best = key, command
    assert best is not None
    return best[1]


def consensus_predict(hypotheses: list[Hypothesis], command: str, corpus: list[str]) -> tuple[int, int] | None:
    values = [predict(hypothesis, command, corpus) for hypothesis in hypotheses]
    values = [value for value in values if value is not None]
    if not values:
        return None
    counts = {value: values.count(value) for value in set(values)}
    maximum = max(counts.values())
    return sorted(value for value, count in counts.items() if count == maximum)[0]


def run(seed: int, mode: str, budget: int = 3) -> dict[str, object]:
    rng = random.Random(seed)
    corpus = [raw_command(obj, op) for obj in OBJECTS for op in OPS]
    hypotheses = enumerate_hypotheses(corpus)
    remaining = corpus.copy()
    witnesses: list[str] = []

    shuffled_outcomes = list(itertools.product(OBJECTS, OPS))
    rng.shuffle(shuffled_outcomes)
    shuffle_map = {corpus[index]: shuffled_outcomes[index] for index in range(len(corpus))}

    for _ in range(budget):
        command = choose_active(hypotheses, remaining, corpus) if mode in ("active", "outcome_shuffle") else rng.choice(remaining)
        remaining.remove(command)
        true_outcome = (OBJ_TOKENS.index(command[:2]), OP_TOKENS.index(command[2:]))
        outcome = shuffle_map[command] if mode == "outcome_shuffle" else true_outcome
        hypotheses = filter_hypotheses(hypotheses, command, outcome, corpus)
        witnesses.append(command)
        if not hypotheses:
            break

    tests = [command for command in corpus if command not in witnesses]
    prospective = sum(
        consensus_predict(hypotheses, command, corpus)
        == (OBJ_TOKENS.index(command[:2]), OP_TOKENS.index(command[2:]))
        for command in tests
    ) / max(1, len(tests))

    # Unknown-order evaluation uses the learned token sets but does not reveal labels.
    reverse_correct = 0
    for obj, op in itertools.product(OBJECTS, OPS):
        reverse_command = raw_command(obj, op, reverse=True)
        canonical = reverse_command[3:] + reverse_command[:3]
        if consensus_predict(hypotheses, canonical, corpus) == (obj, op):
            reverse_correct += 1

    return {
        "remaining_hypotheses": len(hypotheses),
        "witnesses": witnesses,
        "prospective_unseen": prospective,
        "unknown_order": reverse_correct / 16,
        "inverse": prospective,
    }


def main() -> None:
    start = time.perf_counter()
    per_mode = {
        mode: [run(seed, mode) for seed in SEEDS]
        for mode in ("active", "random", "outcome_shuffle")
    }
    summary = {
        mode: {
            metric: statistics.mean(float(result[metric]) for result in results)
            for metric in ("remaining_hypotheses", "prospective_unseen", "unknown_order", "inverse")
        }
        for mode, results in per_mode.items()
    }
    output = {
        "hypothesis": "Minimal-witness joint boundary-orbit identification from raw concatenated opaque commands",
        "seeds": SEEDS,
        "budget": 3,
        "initial_hypotheses": len(enumerate_hypotheses([raw_command(obj, op) for obj in OBJECTS for op in OPS])),
        "summary": summary,
        "per_seed": per_mode,
        "runtime_sec": time.perf_counter() - start,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "model_bytes_upper_bound": 18_432,
        "estimated_ops_per_selector_round": 18_432,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
