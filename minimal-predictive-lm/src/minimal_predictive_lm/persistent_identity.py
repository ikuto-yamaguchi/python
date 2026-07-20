from __future__ import annotations

import json
import math
import random
import resource
import time
from dataclasses import dataclass
from itertools import permutations
from pathlib import Path


@dataclass(frozen=True)
class Observation:
    surface: str
    color: str
    place: str
    action: str | None = None


class PredictiveIdentityVersionSpace:
    """Retain every object matching tied under predictive description length."""

    def __init__(self, max_hypotheses: int = 64) -> None:
        self.max_hypotheses = max_hypotheses
        self.last_reads = 0

    def _cost(self, previous, current, permutation) -> float:
        cost = 0.0
        for source_index, target_index in enumerate(permutation):
            before = previous[source_index]
            after = current[target_index]
            self.last_reads += 3
            cost += float(before.color != after.color) * 3.0
            cost += float(before.place != after.place) * 0.25
            if after.action == "移動" and before.place != after.place:
                cost -= 0.25
        return cost

    def infer(self, previous, current):
        self.last_reads = 0
        scored = []
        for permutation in permutations(range(len(current)), len(previous)):
            scored.append((self._cost(previous, current, permutation), permutation))
        scored.sort()
        best_cost = scored[0][0]
        hypotheses = [
            permutation
            for cost, permutation in scored
            if abs(cost - best_cost) < 1e-12
        ][: self.max_hypotheses]
        return hypotheses, self.last_reads, best_cost

    def serialized_bytes(self) -> int:
        payload = json.dumps(
            {"max_hypotheses": self.max_hypotheses}, separators=(",", ":")
        )
        return len(payload.encode("utf-8"))


def make_case(rng: random.Random, object_count: int, informative: bool, intervention: bool = False):
    colors = ["赤", "青", "緑", "黄", "白", "黒"][:object_count]
    if not informative:
        colors = ["灰"] * object_count
    previous = [
        Observation(
            f"物体{index}",
            colors[index],
            "同じ場所" if not informative else f"場所{index}",
        )
        for index in range(object_count)
    ]
    permutation = list(range(object_count))
    rng.shuffle(permutation)
    current = []
    for new_index, old_index in enumerate(permutation):
        place = f"場所{new_index}" if intervention else previous[old_index].place
        current.append(
            Observation(
                f"対象{new_index}",
                colors[old_index],
                place,
                "移動" if intervention else None,
            )
        )
    truth = tuple(permutation.index(index) for index in range(object_count))
    return previous, current, truth


def integrated_outputs() -> dict[str, str]:
    axes = (
        "自由対話", "指示遂行", "読解", "推論", "計画", "因果・反実仮想",
        "自由記述", "長期対話", "継続学習",
    )
    return {axis: "未解決の要求を構成できません。" for axis in axes}


def run_experiment(output_path: str | Path = "persistent_identity_report.json") -> dict:
    seeds = (1, 7, 19)
    sizes = (2, 3, 4, 5, 6)
    rows = []
    wall_start = time.perf_counter()
    for object_count in sizes:
        for seed in seeds:
            rng = random.Random(seed)
            model = PredictiveIdentityVersionSpace()
            started = time.perf_counter()
            trials = max(12, object_count * 8)
            exact = 0
            ambiguous = 0
            max_reads = 0
            latencies = []
            for trial in range(trials):
                previous, current, truth = make_case(
                    rng,
                    object_count,
                    informative=trial % 2 == 0,
                    intervention=trial % 3 == 0,
                )
                infer_start = time.perf_counter()
                hypotheses, reads, _ = model.infer(previous, current)
                latencies.append((time.perf_counter() - infer_start) * 1000.0)
                exact += int(len(hypotheses) == 1 and hypotheses[0] == truth)
                ambiguous += int(len(hypotheses) > 1)
                max_reads = max(max_reads, reads)
            rows.append(
                {
                    "objects": object_count,
                    "seed": seed,
                    "trials": trials,
                    "exact_unique_rate": exact / trials,
                    "ambiguous_rate": ambiguous / trials,
                    "model_bytes": model.serialized_bytes(),
                    "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    "train_and_eval_ms": (time.perf_counter() - started) * 1000.0,
                    "mean_inference_ms": sum(latencies) / len(latencies),
                    "p95_inference_ms": sorted(latencies)[max(0, int(0.95 * len(latencies)) - 1)],
                    "max_candidates": math.factorial(object_count),
                    "max_reads": max_reads,
                    "integrated_gate_score": 0.0,
                    "outputs": integrated_outputs(),
                }
            )
    summary = {
        "max_model_bytes": max(row["model_bytes"] for row in rows),
        "max_peak_rss_kib": max(row["peak_rss_kib"] for row in rows),
        "max_train_and_eval_ms": max(row["train_and_eval_ms"] for row in rows),
        "max_mean_inference_ms": max(row["mean_inference_ms"] for row in rows),
        "max_candidates": max(row["max_candidates"] for row in rows),
        "max_reads": max(row["max_reads"] for row in rows),
        "mean_exact_unique_rate": sum(row["exact_unique_rate"] for row in rows) / len(rows),
        "mean_ambiguous_rate": sum(row["ambiguous_rate"] for row in rows) / len(rows),
        "integrated_gate_mean": 0.0,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "candidate_supported": False,
        "wall_seconds": time.perf_counter() - wall_start,
    }
    report = {
        "experiment": "Persistent Predictive Identity Version Space 001",
        "hypothesis": "identity is the version space of object matchings minimizing future predictive description length",
        "rows": rows,
        "summary": summary,
        "structural_falsification": (
            "When objects share predictive properties, all permutations have identical MDL cost. "
            "Passive temporal consistency cannot identify persistent identity; forcing one mapping fabricates identity."
        ),
        "next_bottleneck": (
            "learn interventions that break identity symmetries, then bind causal invariants "
            "to unrestricted Japanese without hand-supplied attributes"
        ),
    }
    Path(output_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run_experiment()["summary"], ensure_ascii=False, indent=2))
