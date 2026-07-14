from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import log2
from typing import Iterable, Sequence

from .cap_gen_002_grounded_actuation_symmetry import (
    GroundingProfile,
    Permutation,
    cycle_graph,
    graph_automorphisms,
    minimum_base_size,
)


Signature = int | str | tuple[object, ...]
EnvironmentSignatures = tuple[tuple[Signature, ...], ...]


@dataclass(frozen=True)
class AuxiliaryChannel:
    name: str
    environment_signatures: EnvironmentSignatures
    executable_bits: int
    validation_operations: int
    inference_operations: int
    peak_memory_bits: int

    def validate(self, action_count: int) -> None:
        if not self.environment_signatures:
            raise ValueError("at least one environment is required")
        if any(len(row) != action_count for row in self.environment_signatures):
            raise ValueError("every environment must cover every latent action")
        if min(
            self.executable_bits,
            self.validation_operations,
            self.inference_operations,
            self.peak_memory_bits,
        ) < 0:
            raise ValueError("resource costs must be non-negative")

    @property
    def observed_environment_count(self) -> int:
        return len(self.environment_signatures)

    @property
    def invariant_on_observed_environments(self) -> bool:
        first = self.environment_signatures[0]
        return all(row == first for row in self.environment_signatures[1:])

    @property
    def invariant_signature(self) -> tuple[Signature, ...] | None:
        if not self.invariant_on_observed_environments:
            return None
        return self.environment_signatures[0]


@dataclass(frozen=True)
class AuxiliaryBundleResult:
    channel_names: tuple[str, ...]
    executable_bits: int
    validation_operations: int
    inference_operations: int
    peak_memory_bits: int
    certified_channels: tuple[str, ...]
    rejected_channels: tuple[str, ...]
    residual_group: tuple[Permutation, ...]
    direct_anchor_count: int
    symmetry_tax_bits: int
    grounded_total_bits: int
    deterministic_information_bits: float

    @property
    def residual_group_size(self) -> int:
        return len(self.residual_group)

    @property
    def resource_vector(self) -> tuple[int, int, int, int, int]:
        return (
            self.grounded_total_bits,
            self.validation_operations,
            self.inference_operations,
            self.peak_memory_bits,
            self.direct_anchor_count,
        )


def deterministic_information_bits(signatures: Sequence[Signature]) -> float:
    """I(A; X) for a deterministic channel and a uniform finite action prior."""

    if not signatures:
        return 0.0
    counts = Counter(signatures)
    total = len(signatures)
    return -sum(
        (count / total) * log2(count / total)
        for count in counts.values()
    )


def combined_signature(
    channels: Sequence[AuxiliaryChannel],
    action_index: int,
    environment_index: int = 0,
) -> tuple[Signature, ...]:
    return tuple(
        channel.environment_signatures[environment_index][action_index]
        for channel in channels
    )


def residual_automorphisms(
    group: Sequence[Permutation],
    channels: Sequence[AuxiliaryChannel],
    *,
    require_observed_invariance: bool = True,
) -> tuple[Permutation, ...]:
    """Return symmetries that survive a bundle of auxiliary channels.

    If `require_observed_invariance` is true, a channel contributes only when its
    action-conditioned signature is unchanged in every observed environment.  This is a
    finite certificate over the supplied environments, not a proof about every future
    environment.
    """

    if not group:
        raise ValueError("group must include the identity")
    action_count = len(group[0])
    if any(len(permutation) != action_count for permutation in group):
        raise ValueError("group permutations must have equal size")
    for channel in channels:
        channel.validate(action_count)

    accepted = tuple(
        channel
        for channel in channels
        if (not require_observed_invariance)
        or channel.invariant_on_observed_environments
    )
    if not accepted:
        return tuple(group)

    signatures = tuple(
        combined_signature(accepted, action_index)
        for action_index in range(action_count)
    )
    return tuple(
        permutation
        for permutation in group
        if all(
            signatures[action_index] == signatures[permutation[action_index]]
            for action_index in range(action_count)
        )
    )


def evaluate_auxiliary_bundle(
    group: Sequence[Permutation],
    channels: Sequence[AuxiliaryChannel],
    *,
    direct_anchor_bits: int,
) -> AuxiliaryBundleResult:
    if direct_anchor_bits < 0:
        raise ValueError("direct anchor cost must be non-negative")
    if not group:
        raise ValueError("group must include the identity")
    action_count = len(group[0])
    for channel in channels:
        channel.validate(action_count)

    certified = tuple(
        channel for channel in channels if channel.invariant_on_observed_environments
    )
    rejected = tuple(
        channel for channel in channels if not channel.invariant_on_observed_environments
    )
    residual = residual_automorphisms(group, channels)
    anchor_count = minimum_base_size(residual, action_count)
    symmetry_tax = anchor_count * direct_anchor_bits
    if certified:
        signatures = tuple(
            combined_signature(certified, action_index)
            for action_index in range(action_count)
        )
        information = deterministic_information_bits(signatures)
    else:
        information = 0.0

    executable_bits = sum(channel.executable_bits for channel in channels)
    return AuxiliaryBundleResult(
        tuple(channel.name for channel in channels),
        executable_bits,
        sum(channel.validation_operations for channel in channels),
        sum(channel.inference_operations for channel in channels),
        max((channel.peak_memory_bits for channel in channels), default=0),
        tuple(channel.name for channel in certified),
        tuple(channel.name for channel in rejected),
        residual,
        anchor_count,
        symmetry_tax,
        executable_bits + symmetry_tax,
        information,
    )


def naive_environmentwise_residual_size(
    group: Sequence[Permutation],
    channel: AuxiliaryChannel,
) -> int:
    """A deliberately invalid score that trusts each environment separately.

    A unique policy-specific tag can make every environment appear fully grounded even
    when the tag-to-action relation changes between environments.
    """

    action_count = len(group[0])
    channel.validate(action_count)
    sizes = []
    for row in channel.environment_signatures:
        sizes.append(
            sum(
                all(row[index] == row[permutation[index]] for index in range(action_count))
                for permutation in group
            )
        )
    return max(sizes)


def single_environment_two_world_counterexample() -> dict[str, object]:
    """Same first environment, incompatible future semantics.

    With one environment, a unique auxiliary tag is observationally compatible with both
    a stable channel and a policy-specific codebook.  Their next-environment predictions
    disagree, so training distinctiveness alone cannot certify grounding.
    """

    observed = tuple(range(8))
    stable_future = observed
    policy_specific_future = observed[1:] + observed[:1]
    return {
        "observed_training_signatures_equal": True,
        "training_signatures": observed,
        "stable_future": stable_future,
        "policy_specific_future": policy_specific_future,
        "future_predictions_differ": stable_future != policy_specific_future,
    }


def prospective_shift_counterexample() -> dict[str, object]:
    """Observed-environment invariance is not universal invariance."""

    training_rows = (tuple(range(8)), tuple(range(8)))
    shifted_future = tuple(reversed(range(8)))
    channel = AuxiliaryChannel(
        "apparently-stable-unique-tag",
        training_rows,
        executable_bits=3,
        validation_operations=16,
        inference_operations=1,
        peak_memory_bits=24,
    )
    return {
        "stable_on_observed_environments": channel.invariant_on_observed_environments,
        "prospective_environment_matches": shifted_future == training_rows[0],
        "prospective_environment_exposes_shift": shifted_future != training_rows[0],
    }


def pareto_frontier(
    results: Sequence[AuxiliaryBundleResult],
) -> tuple[AuxiliaryBundleResult, ...]:
    frontier: list[AuxiliaryBundleResult] = []
    for candidate in results:
        dominated = False
        for other in results:
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
    return tuple(sorted(frontier, key=lambda row: row.channel_names))


def run_experiment() -> dict[str, object]:
    adjacency = cycle_graph(8)
    group = graph_automorphisms(adjacency)

    stable_marker_a = AuxiliaryChannel(
        "stable-marker-a",
        (
            (1, 0, 0, 0, 0, 0, 0, 0),
            (1, 0, 0, 0, 0, 0, 0, 0),
            (1, 0, 0, 0, 0, 0, 0, 0),
        ),
        executable_bits=4,
        validation_operations=24,
        inference_operations=1,
        peak_memory_bits=8,
    )
    stable_marker_b = AuxiliaryChannel(
        "stable-marker-b",
        (
            (0, 1, 0, 0, 0, 0, 0, 0),
            (0, 1, 0, 0, 0, 0, 0, 0),
            (0, 1, 0, 0, 0, 0, 0, 0),
        ),
        executable_bits=4,
        validation_operations=24,
        inference_operations=1,
        peak_memory_bits=8,
    )
    spurious_unique_tag = AuxiliaryChannel(
        "policy-specific-unique-tag",
        (
            tuple(range(8)),
            tuple(range(1, 8)) + (0,),
            tuple(reversed(range(8))),
        ),
        executable_bits=3,
        validation_operations=24,
        inference_operations=1,
        peak_memory_bits=24,
    )

    no_aux = evaluate_auxiliary_bundle(group, (), direct_anchor_bits=7)
    stable_bundle = evaluate_auxiliary_bundle(
        group,
        (stable_marker_a, stable_marker_b),
        direct_anchor_bits=7,
    )
    spurious_bundle = evaluate_auxiliary_bundle(
        group,
        (spurious_unique_tag,),
        direct_anchor_bits=7,
    )
    naive_spurious_residual = naive_environmentwise_residual_size(
        group,
        spurious_unique_tag,
    )
    first_environment_information = deterministic_information_bits(
        spurious_unique_tag.environment_signatures[0]
    )
    two_world = single_environment_two_world_counterexample()
    prospective = prospective_shift_counterexample()
    frontier = pareto_frontier((no_aux, stable_bundle, spurious_bundle))

    checks = {
        "cycle_has_dihedral_symmetry": len(group) == 16,
        "stable_low_information_bundle_breaks_all_symmetry": (
            stable_bundle.residual_group_size == 1
        ),
        "stable_bundle_needs_no_direct_anchor": stable_bundle.direct_anchor_count == 0,
        "spurious_unique_tag_is_rejected": (
            spurious_bundle.rejected_channels == ("policy-specific-unique-tag",)
        ),
        "spurious_tag_leaves_full_certified_symmetry": (
            spurious_bundle.residual_group_size == 16
        ),
        "naive_environment_score_is_falsely_confident": naive_spurious_residual == 1,
        "spurious_tag_has_more_training_information": (
            first_environment_information > stable_bundle.deterministic_information_bits
        ),
        "certified_objective_prefers_stable_bundle": (
            stable_bundle.grounded_total_bits < spurious_bundle.grounded_total_bits
            and stable_bundle.grounded_total_bits < no_aux.grounded_total_bits
        ),
        "single_environment_is_non_identifying": two_world["future_predictions_differ"],
        "observed_invariance_needs_prospective_check": prospective[
            "prospective_environment_exposes_shift"
        ],
        "stable_bundle_is_on_pareto_frontier": stable_bundle in frontier,
    }

    return {
        "capability_id": "CAP-GEN-002-IAS-001",
        "claim": (
            "finite invariant-auxiliary symmetry certificate and resource objective: "
            "rank channels by certified residual automorphism plus grounding cost, not "
            "training distinctiveness alone"
        ),
        "claim_boundary": (
            "Invariant prediction, auxiliary-variable identifiability, automorphism "
            "stabilizers, and multi-environment causal representation learning are prior "
            "art. This gate supplies a project-specific counterexample and objective; it "
            "does not prove universal future invariance or a new general identifiability theorem."
        ),
        "base_symmetry": {
            "group_size": len(group),
            "minimum_direct_anchors": minimum_base_size(group, 8),
        },
        "stable_bundle": {
            "channels": stable_bundle.channel_names,
            "training_information_bits": stable_bundle.deterministic_information_bits,
            "residual_group_size": stable_bundle.residual_group_size,
            "direct_anchor_count": stable_bundle.direct_anchor_count,
            "executable_bits": stable_bundle.executable_bits,
            "symmetry_tax_bits": stable_bundle.symmetry_tax_bits,
            "grounded_total_bits": stable_bundle.grounded_total_bits,
        },
        "spurious_unique_tag": {
            "training_information_bits": first_environment_information,
            "naive_environmentwise_residual_size": naive_spurious_residual,
            "certified_residual_group_size": spurious_bundle.residual_group_size,
            "rejected_channels": spurious_bundle.rejected_channels,
            "executable_bits": spurious_bundle.executable_bits,
            "symmetry_tax_bits": spurious_bundle.symmetry_tax_bits,
            "grounded_total_bits": spurious_bundle.grounded_total_bits,
        },
        "no_auxiliary": {
            "residual_group_size": no_aux.residual_group_size,
            "symmetry_tax_bits": no_aux.symmetry_tax_bits,
            "grounded_total_bits": no_aux.grounded_total_bits,
        },
        "single_environment_counterexample": two_world,
        "prospective_shift_counterexample": prospective,
        "pareto_frontier": [result.channel_names for result in frontier],
        "checks": checks,
        "passed": all(checks.values()),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2, sort_keys=True))
