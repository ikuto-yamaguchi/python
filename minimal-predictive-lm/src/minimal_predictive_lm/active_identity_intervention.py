from __future__ import annotations

import itertools
import json
import math
import random
import resource
import statistics
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class InterventionWorld:
    signatures: tuple[tuple[int, ...], ...]


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    object_count: int
    seed: int
    duplicated_signature: bool
    remaining_versions: int
    intervention_count: int
    candidate_reads: int
    elapsed_ms: float
    model_bytes: int


class ActiveIdentityVersionSpace:
    """Choose interventions that maximally split a finite identity version space.

    This is a non-neural active-identification operator. It does not receive
    object labels, semantic names, task IDs, answer candidates, or a privileged
    identity mapping. The retained state is only the surviving permutation set
    and the probes already executed.
    """

    def __init__(self, world: InterventionWorld) -> None:
        self.world = world
        self.object_count = len(world.signatures)
        self.versions = list(itertools.permutations(range(self.object_count)))
        self.used: set[tuple[int, int]] = set()
        self.candidate_reads = 0

    def choose_intervention(self) -> tuple[int, int] | None:
        if not self.versions:
            return None
        probe_count = len(self.world.signatures[0])
        best: tuple[tuple[float, int, int, int], int, int] | None = None
        for observed_object in range(self.object_count):
            for probe in range(probe_count):
                if (observed_object, probe) in self.used:
                    continue
                buckets: dict[int, int] = {}
                for version in self.versions:
                    outcome = self.world.signatures[version[observed_object]][probe]
                    buckets[outcome] = buckets.get(outcome, 0) + 1
                self.candidate_reads += len(self.versions)
                expected_remaining = sum(count * count for count in buckets.values()) / len(self.versions)
                worst_case = max(buckets.values())
                key = (expected_remaining, worst_case, observed_object, probe)
                if best is None or key < best[0]:
                    best = (key, observed_object, probe)
        if best is None:
            return None
        return best[1], best[2]

    def observe(self, observed_object: int, probe: int, outcome: int) -> None:
        self.used.add((observed_object, probe))
        self.versions = [
            version
            for version in self.versions
            if self.world.signatures[version[observed_object]][probe] == outcome
        ]

    def serialized_bytes(self) -> int:
        payload = {
            "format": "active-identity-version-space-v1",
            "signatures": [list(row) for row in self.world.signatures],
            "versions": [list(row) for row in self.versions],
            "used": [list(row) for row in sorted(self.used)],
        }
        return len(json.dumps(payload, separators=(",", ":")).encode("utf-8"))


def make_world(object_count: int, seed: int, *, duplicated_signature: bool) -> InterventionWorld:
    probe_count = max(1, math.ceil(math.log2(object_count)))
    signatures = [
        tuple((identity >> bit) & 1 for bit in range(probe_count))
        for identity in range(object_count)
    ]
    if duplicated_signature and object_count >= 2:
        signatures[-1] = signatures[-2]
    random.Random(seed).shuffle(signatures)
    return InterventionWorld(tuple(signatures))


def run_identity_experiment(object_count: int, seed: int, *, duplicated_signature: bool) -> ExperimentResult:
    world = make_world(object_count, seed, duplicated_signature=duplicated_signature)
    model = ActiveIdentityVersionSpace(world)
    true_mapping = tuple(range(object_count))
    interventions = 0
    started = time.perf_counter()
    while len(model.versions) > 1:
        selected = model.choose_intervention()
        if selected is None:
            break
        observed_object, probe = selected
        outcome = world.signatures[true_mapping[observed_object]][probe]
        model.observe(observed_object, probe, outcome)
        interventions += 1
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return ExperimentResult(
        object_count=object_count,
        seed=seed,
        duplicated_signature=duplicated_signature,
        remaining_versions=len(model.versions),
        intervention_count=interventions,
        candidate_reads=model.candidate_reads,
        elapsed_ms=elapsed_ms,
        model_bytes=model.serialized_bytes(),
    )


def integrated_japanese_gate() -> dict[str, bool]:
    # The active identity operator has no Japanese parser, world inducer, planner,
    # or realizer. All capability claims therefore remain false by construction.
    return {
        "free_dialogue": False,
        "instruction_following": False,
        "reading_comprehension": False,
        "reasoning": False,
        "planning": False,
        "causal_counterfactual": False,
        "free_form_generation": False,
        "long_dialogue": False,
        "continual_learning": False,
    }


def build_report() -> dict:
    results: list[ExperimentResult] = []
    for object_count in (2, 3, 4, 5, 6, 7, 8):
        for seed in (1, 7, 19):
            results.append(run_identity_experiment(object_count, seed, duplicated_signature=False))
            results.append(run_identity_experiment(object_count, seed, duplicated_signature=True))

    identifiable = [row for row in results if not row.duplicated_signature]
    unidentifiable = [row for row in results if row.duplicated_signature]
    gate = integrated_japanese_gate()
    peak_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report = {
        "experiment": "Active Identity Intervention 001",
        "hypothesis": "select the lowest-cost intervention that maximally splits persistent identity hypotheses",
        "result": "partially_supported_but_not_general_intelligence",
        "identifiable_unique_rate": statistics.mean(row.remaining_versions == 1 for row in identifiable),
        "duplicate_ambiguity_preserved_rate": statistics.mean(row.remaining_versions > 1 for row in unidentifiable),
        "max_remaining_versions_identifiable": max(row.remaining_versions for row in identifiable),
        "min_remaining_versions_duplicate": min(row.remaining_versions for row in unidentifiable),
        "max_interventions": max(row.intervention_count for row in results),
        "max_candidate_reads": max(row.candidate_reads for row in results),
        "max_model_bytes": max(row.model_bytes for row in results),
        "max_elapsed_ms": max(row.elapsed_ms for row in results),
        "mean_elapsed_ms": statistics.mean(row.elapsed_ms for row in results),
        "peak_rss_kib": peak_rss_kib,
        "candidate_count_max": math.factorial(8),
        "data_scaling_object_counts": [2, 3, 4, 5, 6, 7, 8],
        "seeds": [1, 7, 19],
        "integrated_japanese_gate": gate,
        "integrated_gate_score": statistics.mean(gate.values()),
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "mobile_resource_gate_static": max(row.model_bytes for row in results) < 1_000_000_000,
        "completion": False,
        "structural_counterexample": (
            "Two latent objects with identical intervention signatures remain exchangeable after every available probe. "
            "Active experimentation can break observational symmetry only when the environment exposes a separating intervention."
        ),
        "next_bottleneck": (
            "induce useful intervention dimensions and executable probes from raw Japanese interaction, rather than receiving a probe table"
        ),
        "rows": [row.__dict__ for row in results],
    }
    return report


def main() -> None:
    report = build_report()
    Path("active_identity_intervention_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
