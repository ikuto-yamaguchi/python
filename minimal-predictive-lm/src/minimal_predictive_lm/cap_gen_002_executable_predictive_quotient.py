from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import ceil, log2
from typing import Iterable, Mapping, Sequence


Pair = tuple[str, str]


@dataclass(frozen=True)
class Probe:
    name: str
    executable_bits: int
    operations: int
    peak_memory: int

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("probe name must not be empty")
        if min(self.executable_bits, self.operations, self.peak_memory) < 0:
            raise ValueError("probe resources must be non-negative")

    @property
    def cost_tuple(self) -> tuple[int, int, int]:
        return self.executable_bits, self.operations, self.peak_memory


@dataclass(frozen=True)
class ExperienceTable:
    histories: tuple[str, ...]
    probes: tuple[Probe, ...]
    responses: Mapping[Pair, str]
    successors: Mapping[Pair, str]

    def __post_init__(self) -> None:
        if len(set(self.histories)) != len(self.histories):
            raise ValueError("histories must be unique")
        probe_names = tuple(probe.name for probe in self.probes)
        if len(set(probe_names)) != len(probe_names):
            raise ValueError("probe names must be unique")
        history_set = set(self.histories)
        for history in self.histories:
            for probe in self.probes:
                key = history, probe.name
                if key not in self.responses or key not in self.successors:
                    raise ValueError(f"missing response or successor for {key}")
                if self.successors[key] not in history_set:
                    raise ValueError("successor must be a declared history")

    @property
    def probe_map(self) -> dict[str, Probe]:
        return {probe.name: probe for probe in self.probes}


@dataclass(frozen=True)
class QuotientMachine:
    classes: tuple[tuple[str, ...], ...]
    state_of_history: Mapping[str, int]
    responses: Mapping[tuple[int, str], str]
    successors: Mapping[tuple[int, str], int]

    @property
    def state_count(self) -> int:
        return len(self.classes)

    @property
    def minimum_fixed_state_bits(self) -> int:
        if self.state_count <= 1:
            return 0
        return ceil(log2(self.state_count))


@dataclass(frozen=True, order=True)
class ResourceVector:
    executable_bits: int
    induction_operations: int
    inference_operations: int
    peak_memory: int
    identifying_support: int

    def __post_init__(self) -> None:
        if min(
            self.executable_bits,
            self.induction_operations,
            self.inference_operations,
            self.peak_memory,
            self.identifying_support,
        ) < 0:
            raise ValueError("resource coordinates must be non-negative")

    def dominates(self, other: ResourceVector) -> bool:
        mine = tuple(self)
        theirs = tuple(other)
        return all(left <= right for left, right in zip(mine, theirs)) and any(
            left < right for left, right in zip(mine, theirs)
        )

    def weighted_score(self, weights: ResourceVector) -> int:
        return sum(left * right for left, right in zip(tuple(self), tuple(weights)))

    def __iter__(self):
        yield self.executable_bits
        yield self.induction_operations
        yield self.inference_operations
        yield self.peak_memory
        yield self.identifying_support


@dataclass(frozen=True)
class ResourceCandidate:
    identifier: str
    resources: ResourceVector

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError("candidate identifier must not be empty")


@dataclass(frozen=True)
class ProbeSelection:
    probes: tuple[str, ...]
    total_cost: int
    separated_pairs: frozenset[Pair]
    all_pairs: frozenset[Pair]

    @property
    def complete(self) -> bool:
        return self.separated_pairs == self.all_pairs


@dataclass(frozen=True)
class CanonicalDecision:
    selected: str | None
    score: int | None
    runner_up_score: int | None
    gap: int | None
    abstained: bool
    reason: str


@dataclass(frozen=True)
class UnseenWorldPair:
    training_histories: tuple[str, ...]
    unseen_history: str
    probes: tuple[str, ...]
    world_a_responses: Mapping[Pair, str]
    world_b_responses: Mapping[Pair, str]

    def training_views_equal(self) -> bool:
        for history in self.training_histories:
            for probe in self.probes:
                key = history, probe
                if self.world_a_responses[key] != self.world_b_responses[key]:
                    return False
        return True

    def unseen_views_differ(self) -> bool:
        return any(
            self.world_a_responses[(self.unseen_history, probe)]
            != self.world_b_responses[(self.unseen_history, probe)]
            for probe in self.probes
        )


def _probe_names(table: ExperienceTable, probe_names: Sequence[str] | None) -> tuple[str, ...]:
    available = table.probe_map
    if probe_names is None:
        return tuple(probe.name for probe in table.probes)
    names = tuple(probe_names)
    if len(set(names)) != len(names):
        raise ValueError("probe selection contains duplicates")
    unknown = set(names) - set(available)
    if unknown:
        raise ValueError(f"unknown probes: {sorted(unknown)}")
    return names


def behavioral_partition(
    table: ExperienceTable,
    probe_names: Sequence[str] | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Compute the coarsest response-and-successor congruence.

    Partition refinement starts with one block and repeatedly splits histories by their
    immediate responses and the current blocks of every successor. This is the finite
    deterministic greatest-fixed-point construction used only as a correctness oracle.
    """

    names = _probe_names(table, probe_names)
    blocks: tuple[tuple[str, ...], ...] = (tuple(sorted(table.histories)),)
    while True:
        block_of = {
            history: block_index
            for block_index, block in enumerate(blocks)
            for history in block
        }
        grouped: dict[tuple[tuple[str, int], ...], list[str]] = {}
        for history in table.histories:
            signature = tuple(
                (
                    table.responses[(history, probe)],
                    block_of[table.successors[(history, probe)]],
                )
                for probe in names
            )
            grouped.setdefault(signature, []).append(history)
        refined = tuple(
            sorted(
                (tuple(sorted(group)) for group in grouped.values()),
                key=lambda block: block,
            )
        )
        if refined == blocks:
            return refined
        blocks = refined


def quotient_machine(
    table: ExperienceTable,
    probe_names: Sequence[str] | None = None,
) -> QuotientMachine:
    names = _probe_names(table, probe_names)
    classes = behavioral_partition(table, names)
    state_of = {
        history: state
        for state, block in enumerate(classes)
        for history in block
    }
    responses: dict[tuple[int, str], str] = {}
    successors: dict[tuple[int, str], int] = {}
    for state, block in enumerate(classes):
        representative = block[0]
        for probe in names:
            responses[(state, probe)] = table.responses[(representative, probe)]
            successors[(state, probe)] = state_of[
                table.successors[(representative, probe)]
            ]
    return QuotientMachine(classes, state_of, responses, successors)


def partition_is_exact(
    table: ExperienceTable,
    partition: Sequence[Sequence[str]],
    probe_names: Sequence[str] | None = None,
) -> bool:
    names = _probe_names(table, probe_names)
    blocks = tuple(tuple(block) for block in partition)
    flattened = [history for block in blocks for history in block]
    if set(flattened) != set(table.histories) or len(flattened) != len(set(flattened)):
        return False
    block_of = {
        history: block_index
        for block_index, block in enumerate(blocks)
        for history in block
    }
    for block in blocks:
        representative = block[0]
        for history in block[1:]:
            for probe in names:
                if table.responses[(history, probe)] != table.responses[(representative, probe)]:
                    return False
                if block_of[table.successors[(history, probe)]] != block_of[
                    table.successors[(representative, probe)]
                ]:
                    return False
    return True


def all_class_pairs(classes: Sequence[str]) -> frozenset[Pair]:
    return frozenset(tuple(sorted(pair)) for pair in combinations(sorted(classes), 2))


def probe_separated_pairs(
    classes: Sequence[str],
    response_rows: Mapping[Pair, str],
    probe_name: str,
) -> frozenset[Pair]:
    separated: set[Pair] = set()
    for left, right in combinations(sorted(classes), 2):
        if response_rows[(left, probe_name)] != response_rows[(right, probe_name)]:
            separated.add((left, right))
    return frozenset(separated)


def exact_minimum_probe_selection(
    classes: Sequence[str],
    probes: Sequence[Probe],
    response_rows: Mapping[Pair, str],
    *,
    cost_coordinate: str = "executable_bits",
) -> ProbeSelection:
    """Exact exponential oracle for small finite theory cases."""

    if not probes:
        raise ValueError("at least one probe is required")
    if not hasattr(probes[0], cost_coordinate):
        raise ValueError("unknown cost coordinate")
    all_pairs = all_class_pairs(classes)
    coverage = {
        probe.name: probe_separated_pairs(classes, response_rows, probe.name)
        for probe in probes
    }
    best: tuple[int, int, tuple[str, ...], frozenset[Pair]] | None = None
    for subset_size in range(len(probes) + 1):
        for subset in combinations(probes, subset_size):
            names = tuple(sorted(probe.name for probe in subset))
            separated = frozenset().union(*(coverage[name] for name in names)) if names else frozenset()
            if separated != all_pairs:
                continue
            cost = sum(int(getattr(probe, cost_coordinate)) for probe in subset)
            candidate = cost, len(names), names, separated
            if best is None or candidate[:3] < best[:3]:
                best = candidate
    if best is None:
        return ProbeSelection((), 0, frozenset(), all_pairs)
    return ProbeSelection(best[2], best[0], best[3], all_pairs)


def greedy_probe_selection(
    classes: Sequence[str],
    probes: Sequence[Probe],
    response_rows: Mapping[Pair, str],
    *,
    cost_coordinate: str = "executable_bits",
) -> ProbeSelection:
    if not probes:
        raise ValueError("at least one probe is required")
    if not hasattr(probes[0], cost_coordinate):
        raise ValueError("unknown cost coordinate")
    all_pairs = all_class_pairs(classes)
    coverage = {
        probe.name: probe_separated_pairs(classes, response_rows, probe.name)
        for probe in probes
    }
    selected: list[Probe] = []
    separated: set[Pair] = set()
    remaining = list(probes)
    while frozenset(separated) != all_pairs and remaining:
        scored: list[tuple[float, int, str, Probe, frozenset[Pair]]] = []
        for probe in remaining:
            new_pairs = coverage[probe.name] - separated
            cost = int(getattr(probe, cost_coordinate))
            denominator = max(cost, 1)
            scored.append(
                (
                    -(len(new_pairs) / denominator),
                    cost,
                    probe.name,
                    probe,
                    new_pairs,
                )
            )
        _ratio, _cost, _name, chosen, new_pairs = min(scored)
        if not new_pairs:
            break
        selected.append(chosen)
        separated.update(new_pairs)
        remaining.remove(chosen)
    names = tuple(sorted(probe.name for probe in selected))
    total_cost = sum(int(getattr(probe, cost_coordinate)) for probe in selected)
    return ProbeSelection(names, total_cost, frozenset(separated), all_pairs)


def pareto_frontier(candidates: Iterable[ResourceCandidate]) -> tuple[ResourceCandidate, ...]:
    items = tuple(candidates)
    identifiers = [candidate.identifier for candidate in items]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("candidate identifiers must be unique")
    frontier = tuple(
        candidate
        for candidate in items
        if not any(
            other.resources.dominates(candidate.resources)
            for other in items
            if other.identifier != candidate.identifier
        )
    )
    return tuple(sorted(frontier, key=lambda candidate: candidate.identifier))


def canonical_decision(
    candidates: Sequence[ResourceCandidate],
    weights: ResourceVector,
    *,
    minimum_gap: int = 1,
) -> CanonicalDecision:
    if minimum_gap < 0:
        raise ValueError("minimum gap must be non-negative")
    frontier = pareto_frontier(candidates)
    if not frontier:
        return CanonicalDecision(None, None, None, None, True, "no candidates")
    scored = sorted(
        (
            candidate.resources.weighted_score(weights),
            candidate.identifier,
        )
        for candidate in frontier
    )
    best_score, best_identifier = scored[0]
    if len(scored) == 1:
        return CanonicalDecision(
            best_identifier,
            best_score,
            None,
            None,
            False,
            "unique Pareto candidate",
        )
    runner_up_score = scored[1][0]
    gap = runner_up_score - best_score
    if gap < minimum_gap:
        return CanonicalDecision(
            None,
            best_score,
            runner_up_score,
            gap,
            True,
            "resource gap is insufficient; internal representative is not stable",
        )
    return CanonicalDecision(
        best_identifier,
        best_score,
        runner_up_score,
        gap,
        False,
        "declared weighted resource policy has a strict gap",
    )


def observational_program_quotient(
    program_outputs: Mapping[str, Sequence[str]],
    program_resources: Mapping[str, ResourceVector],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Known synthesis optimization: quotient programs by observed behavior.

    The representative is selected from each exact output-signature class by Pareto
    filtering, then executable bits, inference operations, and identifier. This function
    is not a novelty claim and does not infer behavior outside the supplied probes.
    """

    if set(program_outputs) != set(program_resources):
        raise ValueError("outputs and resources must name the same programs")
    groups: dict[tuple[str, ...], list[str]] = {}
    for identifier, outputs in program_outputs.items():
        groups.setdefault(tuple(outputs), []).append(identifier)
    result: list[tuple[str, tuple[str, ...]]] = []
    for signature, identifiers in groups.items():
        candidates = [
            ResourceCandidate(identifier, program_resources[identifier])
            for identifier in identifiers
        ]
        frontier = pareto_frontier(candidates)
        representative = min(
            frontier,
            key=lambda candidate: (
                candidate.resources.executable_bits,
                candidate.resources.inference_operations,
                candidate.identifier,
            ),
        )
        result.append((representative.identifier, tuple(sorted(identifiers))))
    return tuple(sorted(result))


def make_unseen_surface_counterexample() -> UnseenWorldPair:
    training = ("known-role-0", "known-role-1")
    unseen = "new-surface"
    probes = ("probe-a", "probe-b")
    world_a = {
        ("known-role-0", "probe-a"): "0",
        ("known-role-0", "probe-b"): "0",
        ("known-role-1", "probe-a"): "1",
        ("known-role-1", "probe-b"): "1",
        (unseen, "probe-a"): "0",
        (unseen, "probe-b"): "0",
    }
    world_b = dict(world_a)
    world_b[(unseen, "probe-a")] = "1"
    world_b[(unseen, "probe-b")] = "1"
    return UnseenWorldPair(training, unseen, probes, world_a, world_b)


def build_theory_fixture() -> ExperienceTable:
    probes = (
        Probe("immediate", 5, 1, 1),
        Probe("follow", 8, 2, 1),
    )
    histories = ("a0", "a1", "b", "sink0", "sink1")
    responses = {
        ("a0", "immediate"): "same",
        ("a1", "immediate"): "same",
        ("b", "immediate"): "same",
        ("sink0", "immediate"): "zero",
        ("sink1", "immediate"): "one",
        ("a0", "follow"): "go",
        ("a1", "follow"): "go",
        ("b", "follow"): "go",
        ("sink0", "follow"): "zero",
        ("sink1", "follow"): "one",
    }
    successors = {
        ("a0", "immediate"): "sink0",
        ("a1", "immediate"): "sink0",
        ("b", "immediate"): "sink1",
        ("sink0", "immediate"): "sink0",
        ("sink1", "immediate"): "sink1",
        ("a0", "follow"): "sink0",
        ("a1", "follow"): "sink0",
        ("b", "follow"): "sink1",
        ("sink0", "follow"): "sink0",
        ("sink1", "follow"): "sink1",
    }
    return ExperienceTable(histories, probes, responses, successors)


def run_theory_gate() -> dict[str, object]:
    fixture = build_theory_fixture()
    quotient = quotient_machine(fixture)
    unseen = make_unseen_surface_counterexample()

    classes = ("r0", "r1", "r2", "r3")
    probes = (
        Probe("high-bit", 1, 1, 1),
        Probe("low-bit", 1, 1, 1),
        Probe("parity", 3, 1, 1),
    )
    rows = {
        ("r0", "high-bit"): "0",
        ("r1", "high-bit"): "0",
        ("r2", "high-bit"): "1",
        ("r3", "high-bit"): "1",
        ("r0", "low-bit"): "0",
        ("r1", "low-bit"): "1",
        ("r2", "low-bit"): "0",
        ("r3", "low-bit"): "1",
        ("r0", "parity"): "0",
        ("r1", "parity"): "1",
        ("r2", "parity"): "1",
        ("r3", "parity"): "0",
    }
    exact = exact_minimum_probe_selection(classes, probes, rows)
    greedy = greedy_probe_selection(classes, probes, rows)

    resource_candidates = (
        ResourceCandidate("short-recompute", ResourceVector(10, 80, 100, 4, 8)),
        ResourceCandidate("large-lookup", ResourceVector(100, 120, 1, 80, 8)),
        ResourceCandidate("dominated", ResourceVector(120, 150, 120, 100, 10)),
    )
    frontier = pareto_frontier(resource_candidates)
    tie = canonical_decision(
        (
            ResourceCandidate("left", ResourceVector(10, 10, 10, 10, 10)),
            ResourceCandidate("right", ResourceVector(10, 10, 10, 10, 10)),
        ),
        ResourceVector(1, 1, 1, 1, 1),
    )
    strict = canonical_decision(
        resource_candidates,
        ResourceVector(10, 1, 1, 1, 1),
    )

    program_quotient = observational_program_quotient(
        {
            "inc-dec": ("a", "b"),
            "identity": ("a", "b"),
            "reverse": ("z", "y"),
        },
        {
            "inc-dec": ResourceVector(20, 0, 4, 1, 2),
            "identity": ResourceVector(8, 0, 2, 1, 2),
            "reverse": ResourceVector(9, 0, 3, 1, 2),
        },
    )

    checks = {
        "quotient_merges_only_behaviorally_equal_histories": quotient.classes
        == (("a0", "a1"), ("b",), ("sink0",), ("sink1",)),
        "quotient_partition_is_exact": partition_is_exact(fixture, quotient.classes),
        "illegal_merge_is_rejected": not partition_is_exact(
            fixture,
            (("a0", "a1", "b"), ("sink0",), ("sink1",)),
        ),
        "unseen_worlds_match_on_training": unseen.training_views_equal(),
        "unseen_worlds_disagree_only_where_unobserved": unseen.unseen_views_differ(),
        "exact_minimum_probes_separate_all_classes": exact.complete
        and exact.probes == ("high-bit", "low-bit")
        and exact.total_cost == 2,
        "greedy_reaches_same_small_fixture_solution": greedy.complete
        and greedy.total_cost == exact.total_cost,
        "resource_frontier_keeps_code_compute_tradeoff": tuple(
            candidate.identifier for candidate in frontier
        )
        == ("large-lookup", "short-recompute"),
        "resource_tie_abstains": tie.abstained and tie.selected is None,
        "strict_declared_policy_selects_one": not strict.abstained
        and strict.selected == "short-recompute",
        "observational_program_quotient_uses_smallest_representative": program_quotient
        == (("identity", ("identity", "inc-dec")), ("reverse", ("reverse",))),
    }
    return {
        "capability_id": "CAP-GEN-002-EPQ-001",
        "claim": (
            "finite theorem gate for executable predictive quotients, separating probes, "
            "resource Pareto frontiers, and unseen-surface non-identifiability"
        ),
        "claim_boundary": (
            "the quotient, bisimulation refinement, minimum-test formulation, and observational "
            "program quotient are known-style constructions; only the joint lifetime-resource "
            "acquisition hypothesis remains an unverified novelty candidate"
        ),
        "quotient": {
            "classes": quotient.classes,
            "state_count": quotient.state_count,
            "minimum_fixed_state_bits": quotient.minimum_fixed_state_bits,
        },
        "probe_selection": {
            "exact": exact.probes,
            "exact_cost": exact.total_cost,
            "greedy": greedy.probes,
            "greedy_cost": greedy.total_cost,
            "class_pairs": len(exact.all_pairs),
        },
        "resource_frontier": [
            {
                "identifier": candidate.identifier,
                "resources": tuple(candidate.resources),
            }
            for candidate in frontier
        ],
        "canonical_tie": {
            "abstained": tie.abstained,
            "reason": tie.reason,
        },
        "canonical_strict": {
            "selected": strict.selected,
            "gap": strict.gap,
        },
        "unseen_surface_counterexample": {
            "training_views_equal": unseen.training_views_equal(),
            "unseen_views_differ": unseen.unseen_views_differ(),
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_theory_gate(), ensure_ascii=False, indent=2, sort_keys=True))
