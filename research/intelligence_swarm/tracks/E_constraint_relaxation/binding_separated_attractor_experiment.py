from __future__ import annotations

import json
import random
import re
import resource
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Episode:
    before: str
    command: str
    after: str
    blocked: bool


@dataclass(frozen=True)
class OpNode:
    command_skeleton: str
    state_prefix: str
    state_suffix: str
    support: int


@dataclass(frozen=True)
class Binding:
    entity: str
    old: str
    new: str


@dataclass(frozen=True)
class Candidate:
    operation: OpNode
    binding: Binding


def longest_common_substring(a: str, b: str) -> str:
    match = SequenceMatcher(None, a, b).find_longest_match(0, len(a), 0, len(b))
    return a[match.a : match.a + match.size]


def affix_diff(a: str, b: str) -> Tuple[str, str, str, str]:
    left = 0
    while left < min(len(a), len(b)) and a[left] == b[left]:
        left += 1
    right = 0
    while right < min(len(a) - left, len(b) - left) and a[-1 - right] == b[-1 - right]:
        right += 1
    a_mid = a[left : len(a) - right if right else len(a)]
    b_mid = b[left : len(b) - right if right else len(b)]
    suffix = a[len(a) - right :] if right else ""
    return a[:left], a_mid, b_mid, suffix


def normalize(text: str, spans: List[str]) -> str:
    out = text
    for span in sorted({x for x in spans if x}, key=len, reverse=True):
        out = out.replace(span, "<>")
    return out


def induce_operation(ep: Episode) -> Optional[OpNode]:
    if ep.blocked or ep.before == ep.after:
        return None
    prefix, old, new, suffix = affix_diff(ep.before, ep.after)
    entity = longest_common_substring(ep.before, ep.command).strip("、。=へをのは ")
    if not entity or not old or not new:
        return None
    skeleton = normalize(ep.command, [entity, old, new])
    return OpNode(skeleton, prefix.replace(entity, "<>"), suffix, 1)


def learn(train: List[Episode]) -> Tuple[List[OpNode], Dict[str, int]]:
    counts: Dict[Tuple[str, str, str], int] = {}
    blocked_markers: Dict[str, int] = {}
    for ep in train:
        if ep.blocked:
            for marker in ("固定中", "保護中"):
                if marker in ep.before:
                    blocked_markers[marker] = blocked_markers.get(marker, 0) + 1
            continue
        op = induce_operation(ep)
        if op is not None:
            key = (op.command_skeleton, op.state_prefix, op.state_suffix)
            counts[key] = counts.get(key, 0) + 1
    operations = [OpNode(key[0], key[1], key[2], support) for key, support in counts.items()]
    return operations, blocked_markers


def propose_bindings(before: str, command: str) -> List[Binding]:
    matcher = SequenceMatcher(None, before, command)
    shared = [before[m.a : m.a + m.size] for m in matcher.get_matching_blocks() if m.size >= 2]
    entities = []
    for span in shared:
        cleaned = span.strip("、。=へをのは ")
        if len(cleaned) >= 2:
            entities.append(cleaned)
    command_only = [
        x for x in re.split(r"[、。=へをのは\s]+", command) if len(x) >= 2 and x not in before
    ]
    before_only = [
        x for x in re.split(r"[、。=へをのは\s]+", before) if len(x) >= 2 and x not in command
    ]
    proposals = [Binding(e, old, new) for e in entities[:4] for old in before_only[:4] for new in command_only[:4]]
    return list(dict.fromkeys(proposals))[:32]


def apply(candidate: Candidate, state: str) -> Optional[str]:
    op = candidate.operation
    bind = candidate.binding
    prefix = op.state_prefix.replace("<>", bind.entity)
    needle = prefix + bind.old + op.state_suffix
    replacement = prefix + bind.new + op.state_suffix
    if needle not in state:
        return None
    return state.replace(needle, replacement, 1)


def inverse(candidate: Candidate) -> Candidate:
    bind = candidate.binding
    return Candidate(candidate.operation, Binding(bind.entity, bind.new, bind.old))


def local_energy(candidate: Candidate, ep: Episode) -> float:
    bind = candidate.binding
    signature = normalize(ep.command, [bind.entity, bind.old, bind.new])
    similarity = SequenceMatcher(None, candidate.operation.command_skeleton, signature).ratio()
    applicability = 0.0 if apply(candidate, ep.before) is not None else 3.0
    return applicability + 2.0 * (1.0 - similarity) - min(candidate.operation.support, 5) * 0.02


def branch_energy(candidate: Candidate, ep: Episode, blocked_markers: Dict[str, int]) -> float:
    action = apply(candidate, ep.before)
    restored = apply(inverse(candidate), action) if action is not None else None
    bind = candidate.binding
    other_entity = bind.entity + "別"
    other_before = ep.before.replace(bind.entity, other_entity)
    rebound = Candidate(candidate.operation, Binding(other_entity, bind.old, bind.new))
    other_after = apply(rebound, other_before)
    composed = apply(candidate, action) if action is not None else None

    energy = local_energy(candidate, ep)
    energy += 0.0 if restored == ep.before else 2.5
    energy += 0.0 if other_after is not None and bind.entity not in other_after else 1.5
    energy += 0.0 if composed is not None else 0.5
    if any(marker in ep.before for marker in blocked_markers):
        energy += 4.0
    return energy


def propose_candidates(operations: List[OpNode], ep: Episode) -> List[Candidate]:
    bindings = propose_bindings(ep.before, ep.command)
    return [Candidate(op, binding) for op in operations for binding in bindings][:64]


def choose(
    candidates: List[Candidate], ep: Episode, blocked_markers: Dict[str, int], mode: str
) -> Tuple[Optional[Candidate], int, float, float]:
    if not candidates:
        return None, 0, float("inf"), 0.0
    scorer = (lambda c: local_energy(c, ep)) if mode == "local" else (
        lambda c: branch_energy(c, ep, blocked_markers)
    )
    energies = [scorer(candidate) for candidate in candidates]
    current = 0
    sweeps = 0
    for _ in range(8):
        sweeps += 1
        best = min(range(len(candidates)), key=lambda index: energies[index])
        if best == current:
            break
        current = best
    ordered = sorted(energies)
    margin = ordered[1] - ordered[0] if len(ordered) > 1 else 0.0
    return candidates[current], sweeps, ordered[0], margin


def make_episode(rng: random.Random, syntax: int, blocked: bool = False, rename: bool = False) -> Episode:
    alphabet = "春夏秋冬東西南北天地" if rename else "甲乙丙丁戊己庚辛壬癸"
    entity = "対象" + "".join(rng.choice(alphabet) for _ in range(2))
    old = "区画" + str(rng.randrange(10, 99))
    new = "区画" + str(rng.randrange(100, 999))
    marker = "（固定中）" if blocked else ""
    before = f"{entity}の配置先は{old}です。{marker}"
    after = before if blocked else f"{entity}の配置先は{new}です。{marker}"
    if syntax == 0:
        command = f"{entity}を{new}へ移してください。"
    elif syntax == 1:
        command = f"{new}へ、{entity}の配置を変更。"
    else:
        command = f"配置変更対象={entity}、変更後={new}。"
    return Episode(before, command, after, blocked)


def evaluate(seed: int, training_size: int) -> dict:
    rng = random.Random(seed)
    train = [
        make_episode(rng, rng.choice([0, 1]), blocked=(rng.random() < 0.25))
        for _ in range(training_size)
    ]
    operations, blocked_markers = learn(train)
    tests = {
        "seen": [make_episode(rng, rng.choice([0, 1])) for _ in range(20)],
        "rename": [make_episode(rng, rng.choice([0, 1]), rename=True) for _ in range(20)],
        "unseen": [make_episode(rng, 2) for _ in range(20)],
        "blocked": [make_episode(rng, rng.choice([0, 1]), blocked=True) for _ in range(20)],
    }
    output = {}
    for mode in ("local", "branch"):
        metrics = {}
        all_sweeps, active_counts, margins = [], [], []
        for split, items in tests.items():
            correct = 0
            abstained = 0
            for ep in items:
                candidates = propose_candidates(operations, ep)
                selected, sweeps, best, margin = choose(candidates, ep, blocked_markers, mode)
                all_sweeps.append(sweeps)
                active_counts.append(len(candidates))
                margins.append(margin)
                prediction = apply(selected, ep.before) if selected is not None else None
                should_abstain = margin <= 1e-9 or (mode == "branch" and best > 3.5)
                if should_abstain:
                    abstained += 1
                elif prediction == ep.after:
                    correct += 1
            metrics[f"{split}_accuracy"] = correct / len(items)
            metrics[f"{split}_abstention"] = abstained / len(items)
        metrics["mean_sweeps"] = statistics.mean(all_sweeps)
        metrics["mean_active_candidates"] = statistics.mean(active_counts)
        metrics["mean_margin"] = statistics.mean(margins)
        output[mode] = metrics

    serialized = json.dumps(
        {"operations": [op.__dict__ for op in operations], "blocked_markers": blocked_markers},
        ensure_ascii=False,
    ).encode()
    return {
        "seed": seed,
        "training_size": training_size,
        "operations": len(operations),
        "model_bytes": len(serialized),
        "metrics": output,
    }


def main() -> None:
    tracemalloc.start()
    start = time.perf_counter()
    sizes = [48, 192, 384]
    seeds = [1, 7, 19]
    rows = [evaluate(seed, size) for size in sizes for seed in seeds]
    summary = {}
    for size in sizes:
        subset = [row for row in rows if row["training_size"] == size]
        summary[str(size)] = {
            "model_bytes": statistics.mean(row["model_bytes"] for row in subset),
            "operations": statistics.mean(row["operations"] for row in subset),
        }
        for mode in ("local", "branch"):
            keys = subset[0]["metrics"][mode].keys()
            summary[str(size)][mode] = {
                key: statistics.mean(row["metrics"][mode][key] for row in subset) for key in keys
            }
    payload = {
        "hypothesis": "Binding-Separated Counterfactual Attractor Programs",
        "rows": rows,
        "summary": summary,
        "elapsed_seconds": time.perf_counter() - start,
        "python_peak_bytes": tracemalloc.get_traced_memory()[1],
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "weak_smartphone_verified": False,
        "completion": False,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
