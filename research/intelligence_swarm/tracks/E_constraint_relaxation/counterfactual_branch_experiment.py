from __future__ import annotations
import json, random, time, tracemalloc, resource, statistics
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from typing import List, Tuple, Dict

@dataclass(frozen=True)
class Transition:
    before: str
    command: str
    after: str
    noop: str
    reverse_command: str
    reverse_after: str
    other_before: str
    other_command: str
    other_after: str

@dataclass(frozen=True)
class Program:
    prefix: str
    suffix: str
    old: str
    new: str
    cmd_signature: str

    def apply(self, state: str) -> str | None:
        needle = self.prefix + self.old + self.suffix
        if needle not in state:
            return None
        return state.replace(needle, self.prefix + self.new + self.suffix, 1)

    def inverse(self) -> "Program":
        return Program(self.prefix, self.suffix, self.new, self.old, self.cmd_signature)


def longest_common_affixes(a: str, b: str) -> Tuple[str, str, str, str]:
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    j = 0
    while j < min(len(a) - i, len(b) - i) and a[-1 - j] == b[-1 - j]:
        j += 1
    return a[:i], (a[i:len(a)-j] if j else a[i:]), (b[i:len(b)-j] if j else b[i:]), (a[len(a)-j:] if j else "")


def normalize_cmd(cmd: str, spans: List[str]) -> str:
    out = cmd
    for span in sorted([x for x in spans if x], key=len, reverse=True):
        out = out.replace(span, "<>")
    return out


def induce_program(t: Transition) -> Program | None:
    prefix, old, new, suffix = longest_common_affixes(t.before, t.after)
    if not old or not new:
        return None
    return Program(prefix, suffix, old, new, normalize_cmd(t.command, [old, new]))


def decoys(p: Program) -> List[Program]:
    candidates: List[Program] = []
    if p.prefix:
        candidates.append(Program(p.prefix[:-1], p.prefix[-1:] + p.suffix, p.old, p.new, p.cmd_signature))
    if p.suffix:
        candidates.append(Program(p.prefix + p.suffix[:1], p.suffix[1:], p.old, p.new, p.cmd_signature))
    candidates.append(Program(p.prefix, p.suffix, p.new, p.old, p.cmd_signature))
    candidates.append(Program(p.prefix, p.suffix, p.old, p.old, p.cmd_signature))
    return list(dict.fromkeys(candidates))


def execute_branches(p: Program, t: Transition) -> Dict[str, str | None]:
    first = p.apply(t.before)
    return {
        "action": first,
        "noop": t.before,
        "reverse": p.inverse().apply(t.after),
        "other": p.apply(t.other_before),
        "compose": p.apply(first) if first is not None else None,
    }


def scalar_score(p: Program, t: Transition) -> float:
    pred = p.apply(t.before)
    similarity = SequenceMatcher(None, p.cmd_signature, normalize_cmd(t.command, [p.old, p.new])).ratio()
    return (1.0 if pred is not None else -2.0) + similarity


def branch_energy(p: Program, t: Transition) -> float:
    branches = execute_branches(p, t)
    energy = 0.0
    energy += 0 if branches["action"] == t.after else 3
    energy += 0 if branches["noop"] == t.noop else 2
    energy += 0 if branches["reverse"] == t.reverse_after else 2
    energy += 0 if branches["other"] == t.other_after else 2
    energy += 0 if branches["compose"] is not None else 1
    return energy


def choose(candidates: List[Program], t: Transition, mode: str) -> Tuple[Program | None, int, float]:
    if not candidates:
        return None, 0, float("inf")
    scores = [-scalar_score(p, t) for p in candidates] if mode == "scalar" else [branch_energy(p, t) for p in candidates]
    current = 0
    sweeps = 0
    for _ in range(8):
        sweeps += 1
        best = min(range(len(candidates)), key=lambda i: scores[i])
        if best == current:
            break
        current = best
    return candidates[current], sweeps, scores[current]


def make_episode(rng: random.Random, syntax: int = 0, confound: bool = False) -> Transition:
    entity = "対象" + "".join(rng.choice("甲乙丙丁戊己庚辛壬癸") for _ in range(2))
    other = "対象" + "".join(rng.choice("春夏秋冬東西南北") for _ in range(2))
    old = "区画" + str(rng.randrange(10, 99))
    new = "区画" + str(rng.randrange(100, 999))
    other_old = "区画" + str(rng.randrange(10, 99))
    before = f"{entity}の配置先は{old}です。"
    after = before if confound else f"{entity}の配置先は{new}です。"
    other_before = f"{other}の配置先は{other_old}です。"
    other_after = f"{other}の配置先は{new}です。"
    if syntax == 0:
        command = f"{entity}を{new}へ移してください。"
        reverse = f"{entity}を{old}へ戻してください。"
        other_command = f"{other}を{new}へ移してください。"
    elif syntax == 1:
        command = f"{new}へ、{entity}の配置を変更。"
        reverse = f"{old}へ、{entity}の配置を戻す。"
        other_command = f"{new}へ、{other}の配置を変更。"
    else:
        command = f"配置変更対象={entity}、変更後={new}。"
        reverse = f"配置変更対象={entity}、変更後={old}。"
        other_command = f"配置変更対象={other}、変更後={new}。"
    return Transition(before, command, after, before, reverse, before, other_before, other_command, other_after)


def evaluate(seed: int, n: int) -> dict:
    rng = random.Random(seed)
    train = [make_episode(rng, syntax=rng.choice([0, 1])) for _ in range(n)]
    signatures = {normalize_cmd(t.command, []) for t in train}
    tests = {
        "seen": [make_episode(rng, syntax=rng.choice([0, 1])) for _ in range(40)],
        "unseen": [make_episode(rng, syntax=2) for _ in range(40)],
        "confound": [make_episode(rng, syntax=rng.choice([0, 1]), confound=True) for _ in range(40)],
    }
    output = {}
    for mode in ["scalar", "branch"]:
        metrics = {}
        all_sweeps, active, margins = [], [], []
        for split, items in tests.items():
            correct = abstained = 0
            for transition in items:
                oracle = induce_program(transition)
                candidates = [] if oracle is None else [oracle] + decoys(oracle)
                choice, sweeps, best = choose(candidates, transition, mode)
                all_sweeps.append(sweeps)
                active.append(len(candidates))
                values = sorted((-scalar_score(p, transition)) if mode == "scalar" else branch_energy(p, transition) for p in candidates)
                margin = values[1] - values[0] if len(values) > 1 else 0
                margins.append(margin)
                should_abstain = (best > 0 or margin <= 0) if mode == "branch" else (margin <= 0)
                if should_abstain:
                    abstained += 1
                elif choice and choice.apply(transition.before) == transition.after:
                    correct += 1
            metrics[split + "_accuracy"] = correct / len(items)
            metrics[split + "_abstention"] = abstained / len(items)
        metrics["mean_sweeps"] = statistics.mean(all_sweeps)
        metrics["mean_active_candidates"] = statistics.mean(active)
        metrics["mean_margin"] = statistics.mean(margins)
        output[mode] = metrics
    model_bytes = len(json.dumps(sorted(signatures), ensure_ascii=False).encode())
    return {"seed": seed, "n": n, "programs": len(signatures), "model_bytes": model_bytes, "metrics": output}


def main() -> None:
    tracemalloc.start()
    start = time.perf_counter()
    rows = [evaluate(seed, n) for n in [48, 192, 768] for seed in [1, 7, 19]]
    summary = {}
    for n in [48, 192, 768]:
        subset = [row for row in rows if row["n"] == n]
        summary[str(n)] = {
            "model_bytes": statistics.mean(row["model_bytes"] for row in subset),
            "programs": statistics.mean(row["programs"] for row in subset),
        }
        for mode in ["scalar", "branch"]:
            keys = subset[0]["metrics"][mode].keys()
            summary[str(n)][mode] = {key: statistics.mean(row["metrics"][mode][key] for row in subset) for key in keys}
    payload = {
        "hypothesis": "Counterfactual World-Branch Proposal with Executable Relaxation",
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
