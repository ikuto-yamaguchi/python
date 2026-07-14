from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, permutations
from math import ceil, log
from typing import Iterable, Sequence


Permutation = tuple[int, ...]
Adjacency = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class GroundingProfile:
    name: str
    executable_bits: int
    automorphisms: tuple[Permutation, ...]
    direct_anchor_bits: int
    inference_operations: int
    peak_memory_bits: int

    @property
    def action_count(self) -> int:
        return len(self.automorphisms[0]) if self.automorphisms else 0

    @property
    def symmetry_group_size(self) -> int:
        return len(self.automorphisms)

    @property
    def direct_anchor_count(self) -> int:
        return minimum_base_size(self.automorphisms, self.action_count)

    @property
    def symmetry_tax_bits(self) -> int:
        return self.direct_anchor_count * self.direct_anchor_bits

    @property
    def grounded_total_bits(self) -> int:
        return self.executable_bits + self.symmetry_tax_bits

    @property
    def resource_vector(self) -> tuple[int, int, int, int, int]:
        return (
            self.executable_bits,
            self.symmetry_tax_bits,
            self.direct_anchor_count,
            self.inference_operations,
            self.peak_memory_bits,
        )


@dataclass(frozen=True)
class GroundingDecision:
    profile: str
    executable_bits: int
    symmetry_tax_bits: int
    grounded_total_bits: int
    direct_anchor_count: int
    group_size: int


def validate_adjacency(adjacency: Adjacency) -> None:
    n = len(adjacency)
    if n == 0:
        raise ValueError("adjacency must be non-empty")
    if any(len(row) != n for row in adjacency):
        raise ValueError("adjacency must be square")
    if any(value not in (0, 1) for row in adjacency for value in row):
        raise ValueError("adjacency entries must be binary")
    if any(adjacency[i][j] != adjacency[j][i] for i in range(n) for j in range(n)):
        raise ValueError("only undirected relation structures are supported")


def graph_automorphisms(
    adjacency: Adjacency,
    vertex_colors: Sequence[int] | None = None,
) -> tuple[Permutation, ...]:
    """Enumerate automorphisms of a finite latent-action relation structure.

    `vertex_colors` represent independently observed auxiliary signatures. They are not
    invented names: assigning a unique color is legitimate only when a stable observable
    channel actually supplies that distinction.
    """

    validate_adjacency(adjacency)
    n = len(adjacency)
    colors = tuple(vertex_colors) if vertex_colors is not None else (0,) * n
    if len(colors) != n:
        raise ValueError("vertex color count must match the graph")

    output: list[Permutation] = []
    for permutation in permutations(range(n)):
        if any(colors[index] != colors[permutation[index]] for index in range(n)):
            continue
        if all(
            adjacency[i][j] == adjacency[permutation[i]][permutation[j]]
            for i in range(n)
            for j in range(n)
        ):
            output.append(tuple(permutation))
    return tuple(output)


def pointwise_stabilizer(
    group: Sequence[Permutation],
    anchored_points: Iterable[int],
) -> tuple[Permutation, ...]:
    anchors = tuple(anchored_points)
    return tuple(
        permutation
        for permutation in group
        if all(permutation[index] == index for index in anchors)
    )


def is_grounding_base(
    group: Sequence[Permutation],
    anchored_points: Iterable[int],
) -> bool:
    return len(pointwise_stabilizer(group, anchored_points)) == 1


def minimum_bases(
    group: Sequence[Permutation],
    action_count: int,
) -> tuple[tuple[int, ...], ...]:
    if not group:
        raise ValueError("group must contain at least the identity")
    if any(len(permutation) != action_count for permutation in group):
        raise ValueError("permutation size mismatch")
    for size in range(action_count + 1):
        bases = tuple(
            subset
            for subset in combinations(range(action_count), size)
            if is_grounding_base(group, subset)
        )
        if bases:
            return bases
    raise AssertionError("the full point set must be a base")


def minimum_base_size(group: Sequence[Permutation], action_count: int) -> int:
    return len(minimum_bases(group, action_count)[0])


def grounding_information_lower_bound(
    group_size: int,
    maximum_outcomes_per_interaction: int,
) -> int:
    if group_size < 1:
        raise ValueError("group size must be positive")
    if maximum_outcomes_per_interaction < 2:
        raise ValueError("each informative interaction needs at least two outcomes")
    if group_size == 1:
        return 0
    return ceil(log(group_size, maximum_outcomes_per_interaction))


def pareto_frontier(
    profiles: Sequence[GroundingProfile],
) -> tuple[GroundingProfile, ...]:
    frontier: list[GroundingProfile] = []
    for candidate in profiles:
        dominated = False
        for other in profiles:
            if candidate is other:
                continue
            no_worse = all(
                left <= right
                for left, right in zip(other.resource_vector, candidate.resource_vector)
            )
            strictly_better = any(
                left < right
                for left, right in zip(other.resource_vector, candidate.resource_vector)
            )
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            frontier.append(candidate)
    return tuple(sorted(frontier, key=lambda row: row.name))


def choose_by_grounded_bits(
    profiles: Sequence[GroundingProfile],
) -> GroundingDecision:
    if not profiles:
        raise ValueError("at least one profile is required")
    selected = min(
        profiles,
        key=lambda row: (
            row.grounded_total_bits,
            row.executable_bits,
            row.direct_anchor_count,
            row.name,
        ),
    )
    return GroundingDecision(
        selected.name,
        selected.executable_bits,
        selected.symmetry_tax_bits,
        selected.grounded_total_bits,
        selected.direct_anchor_count,
        selected.symmetry_group_size,
    )


def complete_graph(size: int) -> Adjacency:
    if size < 1:
        raise ValueError("size must be positive")
    return tuple(
        tuple(int(i != j) for j in range(size))
        for i in range(size)
    )


def cycle_graph(size: int) -> Adjacency:
    if size < 3:
        raise ValueError("cycle size must be at least three")
    return tuple(
        tuple(int((i - j) % size in (1, size - 1)) for j in range(size))
        for i in range(size)
    )


def _profile(
    *,
    name: str,
    adjacency: Adjacency,
    executable_bits: int,
    direct_anchor_bits: int,
    inference_operations: int,
    peak_memory_bits: int,
    colors: Sequence[int] | None = None,
) -> GroundingProfile:
    return GroundingProfile(
        name,
        executable_bits,
        graph_automorphisms(adjacency, colors),
        direct_anchor_bits,
        inference_operations,
        peak_memory_bits,
    )


def run_experiment() -> dict[str, object]:
    symmetric_four = _profile(
        name="fully-symmetric-four",
        adjacency=complete_graph(4),
        executable_bits=6,
        direct_anchor_bits=4,
        inference_operations=4,
        peak_memory_bits=8,
    )
    cyclic_eight = _profile(
        name="transition-only-cycle",
        adjacency=cycle_graph(8),
        executable_bits=8,
        direct_anchor_bits=7,
        inference_operations=8,
        peak_memory_bits=16,
    )
    auxiliary_eight = _profile(
        name="observable-auxiliary-cycle",
        adjacency=cycle_graph(8),
        colors=tuple(range(8)),
        executable_bits=20,
        direct_anchor_bits=7,
        inference_operations=10,
        peak_memory_bits=24,
    )
    cheap_grounding_cycle = GroundingProfile(
        "transition-only-cycle-cheap-grounding",
        cyclic_eight.executable_bits,
        cyclic_eight.automorphisms,
        3,
        cyclic_eight.inference_operations,
        cyclic_eight.peak_memory_bits,
    )

    s4_bases = minimum_bases(
        symmetric_four.automorphisms,
        symmetric_four.action_count,
    )
    d8_bases = minimum_bases(
        cyclic_eight.automorphisms,
        cyclic_eight.action_count,
    )
    no_anchor_ambiguity = cyclic_eight.symmetry_group_size > 1
    one_anchor_stabilizer = pointwise_stabilizer(cyclic_eight.automorphisms, (0,))
    two_anchor_stabilizer = pointwise_stabilizer(cyclic_eight.automorphisms, d8_bases[0])

    expensive_choice = choose_by_grounded_bits((cyclic_eight, auxiliary_eight))
    cheap_choice = choose_by_grounded_bits((cheap_grounding_cycle, auxiliary_eight))
    frontier = pareto_frontier((cyclic_eight, auxiliary_eight))

    checks = {
        "full_symmetric_group_is_s4": symmetric_four.symmetry_group_size == 24,
        "s4_direct_base_size_is_three": symmetric_four.direct_anchor_count == 3,
        "cycle_group_is_dihedral_d8": cyclic_eight.symmetry_group_size == 16,
        "d8_direct_base_size_is_two": cyclic_eight.direct_anchor_count == 2,
        "observable_auxiliary_breaks_all_symmetry": auxiliary_eight.symmetry_group_size == 1,
        "observable_auxiliary_needs_no_direct_anchor": auxiliary_eight.direct_anchor_count == 0,
        "passive_alignment_is_ambiguous_without_anchor": no_anchor_ambiguity,
        "one_cycle_anchor_leaves_reflection": len(one_anchor_stabilizer) == 2,
        "two_cycle_anchors_ground_uniquely": len(two_anchor_stabilizer) == 1,
        "direct_base_condition_is_exact": is_grounding_base(cyclic_eight.automorphisms, d8_bases[0]),
        "information_lower_bound_for_binary_outcomes": (
            grounding_information_lower_bound(cyclic_eight.symmetry_group_size, 2) == 4
        ),
        "passive_shortest_is_not_lifetime_optimal_when_interaction_expensive": (
            cyclic_eight.executable_bits < auxiliary_eight.executable_bits
            and expensive_choice.profile == auxiliary_eight.name
        ),
        "passive_shortest_returns_when_interaction_is_cheap": (
            cheap_choice.profile == cheap_grounding_cycle.name
        ),
        "resource_frontier_preserves_both_tradeoffs": (
            {row.name for row in frontier}
            == {cyclic_eight.name, auxiliary_eight.name}
        ),
    }

    return {
        "capability_id": "CAP-GEN-002-GAS-001",
        "claim": (
            "finite grounding-symmetry accounting for latent action classes: passive "
            "automorphisms determine the direct-anchor base size, and representation "
            "selection must include the cost of breaking residual action symmetry"
        ),
        "claim_boundary": (
            "permutation-group bases, automorphism ambiguity, information lower bounds, "
            "and active identification are prior art. The unverified novelty candidate is "
            "joint raw acquisition of parser, action quotient, auxiliary invariants, and "
            "a resource-minimal symmetry-breaking interaction policy."
        ),
        "fully_symmetric_four": {
            "group_size": symmetric_four.symmetry_group_size,
            "minimum_direct_anchors": symmetric_four.direct_anchor_count,
            "minimum_bases": [list(base) for base in s4_bases],
        },
        "cycle_eight": {
            "group_size": cyclic_eight.symmetry_group_size,
            "minimum_direct_anchors": cyclic_eight.direct_anchor_count,
            "minimum_bases": [list(base) for base in d8_bases],
            "binary_information_lower_bound": grounding_information_lower_bound(
                cyclic_eight.symmetry_group_size,
                2,
            ),
            "one_anchor_remaining_alignments": len(one_anchor_stabilizer),
            "two_anchor_remaining_alignments": len(two_anchor_stabilizer),
        },
        "representation_tradeoff": {
            "transition_only": {
                "executable_bits": cyclic_eight.executable_bits,
                "symmetry_tax_bits": cyclic_eight.symmetry_tax_bits,
                "grounded_total_bits": cyclic_eight.grounded_total_bits,
            },
            "observable_auxiliary": {
                "executable_bits": auxiliary_eight.executable_bits,
                "symmetry_tax_bits": auxiliary_eight.symmetry_tax_bits,
                "grounded_total_bits": auxiliary_eight.grounded_total_bits,
            },
            "expensive_grounding_choice": expensive_choice.profile,
            "cheap_grounding_choice": cheap_choice.profile,
            "pareto_frontier": [row.name for row in frontier],
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2, sort_keys=True))
