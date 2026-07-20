from __future__ import annotations

import json, math, random, resource, statistics, time
from pathlib import Path
from minimal_predictive_lm.risk_bounded_semantic_version_space import Operation, Probe, RiskBoundedSemanticVersionSpace


def make_world(n: int, indistinguishable: bool):
    operations = [
        Operation(f"op{i}", ((i, 0, 0), (0, i % 3, 0), (0, 0, (i * 7) % 5)), 0.9 if i == n - 1 else 0.05 + 0.05 * (i % 4))
        for i in range(n)
    ]
    probes = [
        Probe(f"bit{bit}", tuple((i >> bit) & 1 for i in range(n)), 0.02 + bit * 0.005)
        for bit in range(max(1, math.ceil(math.log2(n))))
    ]
    probes.append(Probe("parity", tuple(i % 2 for i in range(n)), 0.005))
    if indistinguishable:
        probes = [Probe(p.name, tuple(list(p.outcomes[:-1]) + [p.outcomes[-2]]), p.cost) for p in probes]
    return operations, probes


def run_case(n: int, seed: int, episodes: int, indistinguishable: bool) -> dict:
    started = time.perf_counter_ns()
    operations, probes = make_world(n, indistinguishable)
    model = RiskBoundedSemanticVersionSpace(operations, probes)
    setup_ms = (time.perf_counter_ns() - started) / 1e6
    rng = random.Random(seed)
    correct = ambiguous = unsafe = 0
    latencies, probe_counts = [], []
    for episode in range(episodes):
        target = rng.choice((n - 2, n - 1)) if indistinguishable else rng.randrange(n)
        utterance = f"未知表現_{seed}_{episode}"
        model.begin(utterance)
        used: frozenset[str] = frozenset()
        begin = time.perf_counter_ns()
        while len(model.version_spaces[utterance]) > 1:
            probe = model.choose_probe(utterance, used)
            if probe is None:
                break
            before = len(model.version_spaces[utterance])
            model.observe_probe(utterance, probe, probe.outcomes[target])
            used = used | {probe.name}
            if len(model.version_spaces[utterance]) == before:
                break
        decision, index = model.safe_decision(utterance)
        latencies.append((time.perf_counter_ns() - begin) / 1e6)
        probe_counts.append(len(used))
        correct += int(index == target and decision in {"execute", "confirm"})
        ambiguous += int(index is None)
        unsafe += int(decision == "execute" and index is not None and operations[index].risk > model.risk_budget)
    return {
        "operations": n, "seed": seed, "episodes": episodes, "indistinguishable": indistinguishable,
        "identification_accuracy": correct / episodes, "ambiguity_preserved": ambiguous / episodes,
        "unsafe_execution_rate": unsafe / episodes, "setup_ms": setup_ms,
        "mean_infer_ms": statistics.mean(latencies), "p95_infer_ms": sorted(latencies)[max(0, int(episodes * 0.95) - 1)],
        "mean_probes": statistics.mean(probe_counts), "max_probes": max(probe_counts),
        "candidate_count": n, "model_bytes": model.serialized_bytes(),
        "mean_reads": (model.reads + model.probe_reads) / episodes,
    }


def main() -> None:
    wall = time.perf_counter()
    rows = [
        run_case(n, seed, episodes, indistinguishable)
        for n in (4, 8, 16, 32, 64)
        for seed in (1, 7, 19, 31, 43)
        for episodes in (16, 64, 256)
        for indistinguishable in (False, True)
    ]
    summary = {
        "identifiable_accuracy": statistics.mean(r["identification_accuracy"] for r in rows if not r["indistinguishable"]),
        "indistinguishable_ambiguity_preserved": statistics.mean(r["ambiguity_preserved"] for r in rows if r["indistinguishable"]),
        "max_unsafe_execution_rate": max(r["unsafe_execution_rate"] for r in rows),
        "max_model_bytes": max(r["model_bytes"] for r in rows),
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "max_setup_ms": max(r["setup_ms"] for r in rows),
        "mean_infer_ms": statistics.mean(r["mean_infer_ms"] for r in rows),
        "max_p95_infer_ms": max(r["p95_infer_ms"] for r in rows),
        "max_candidates": max(r["candidate_count"] for r in rows),
        "max_mean_reads": max(r["mean_reads"] for r in rows),
        "wall_seconds": time.perf_counter() - wall,
    }
    report = {
        "experiment": "risk-bounded-semantic-version-space-001", "rows": rows, "summary": summary,
        "integrated_gate": {name: False for name in ("free_dialogue", "instruction_following", "reading", "reasoning", "planning", "causal_counterfactual", "free_writing", "long_dialogue", "continual_learning")},
        "highschool_level_passed": False, "native_japanese_communication_passed": False, "completion": False,
        "claim_boundary": "The principle identifies externally supplied operations through externally supplied probes. It does not infer Japanese semantics or generate native Japanese responses."
    }
    Path("risk_bounded_semantic_version_space_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
