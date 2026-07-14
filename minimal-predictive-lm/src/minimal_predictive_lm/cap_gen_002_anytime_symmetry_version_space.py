from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import combinations
from math import log, sqrt
from typing import Iterable, Sequence

from .cap_gen_002_grounded_actuation_symmetry import (
    Permutation,
    cycle_graph,
    graph_automorphisms,
    minimum_base_size,
)


Subgroup = frozenset[Permutation]


@dataclass(frozen=True)
class BernoulliCount:
    successes: int
    trials: int

    def validate(self) -> None:
        if self.trials < 0:
            raise ValueError("trials must be non-negative")
        if not 0 <= self.successes <= self.trials:
            raise ValueError("successes must lie in [0, trials]")


@dataclass(frozen=True)
class SymmetryVersionCertificate:
    retained_elements: frozenset[Permutation]
    plausible_subgroups: tuple[Subgroup, ...]
    logically_supported_elements: frozenset[Permutation]
    robust_bases: tuple[tuple[int, ...], ...]
    generated_envelope: Subgroup
    envelope_base_size: int

    @property
    def robust_base_size(self) -> int:
        return len(self.robust_bases[0])


@dataclass(frozen=True)
class ExperimentChoice:
    name: str
    retained_elements: int
    rejected_elements: int
    plausible_subgroups: int
    robust_base_size: int


def identity_permutation(size: int) -> Permutation:
    return tuple(range(size))


def compose(left: Permutation, right: Permutation) -> Permutation:
    if len(left) != len(right):
        raise ValueError("permutation size mismatch")
    return tuple(left[right[index]] for index in range(len(left)))


def inverse(permutation: Permutation) -> Permutation:
    output = [0] * len(permutation)
    for source, target in enumerate(permutation):
        output[target] = source
    return tuple(output)


def generated_subgroup(
    generators: Iterable[Permutation],
    action_count: int,
) -> Subgroup:
    identity = identity_permutation(action_count)
    generator_set = {tuple(row) for row in generators}
    if any(len(row) != action_count for row in generator_set):
        raise ValueError("generator size mismatch")
    generator_set |= {inverse(row) for row in generator_set}

    subgroup: set[Permutation] = {identity}
    frontier = deque(generator_set)
    while frontier:
        candidate = frontier.popleft()
        if candidate in subgroup:
            continue
        subgroup.add(candidate)
        current = tuple(subgroup)
        for left in current:
            for product in (compose(left, candidate), compose(candidate, left)):
                if product not in subgroup:
                    frontier.append(product)
    return frozenset(subgroup)


def enumerate_subgroups(group: Sequence[Permutation]) -> tuple[Subgroup, ...]:
    if not group:
        raise ValueError("ambient group must be non-empty")
    action_count = len(group[0])
    ambient = frozenset(group)
    if any(len(row) != action_count for row in ambient):
        raise ValueError("ambient permutation size mismatch")

    identity = identity_permutation(action_count)
    if identity not in ambient:
        raise ValueError("ambient group must contain identity")

    seen: set[Subgroup] = {frozenset({identity})}
    frontier = deque(seen)
    while frontier:
        subgroup = frontier.popleft()
        for element in ambient:
            candidate = generated_subgroup((*subgroup, element), action_count)
            if not candidate <= ambient:
                raise ValueError("ambient set is not closed under composition")
            if candidate not in seen:
                seen.add(candidate)
                frontier.append(candidate)
    return tuple(sorted(seen, key=lambda row: (len(row), tuple(sorted(row)))))


def time_uniform_hoeffding_interval(
    count: BernoulliCount,
    *,
    delta: float,
    stream_count: int,
) -> tuple[float, float]:
    """A simple all-times confidence sequence for a bounded Bernoulli mean.

    At sample size n, the stream receives error budget
    delta / (stream_count * n * (n + 1)). Summing over n and all streams is at
    most delta. The construction is conservative but remains valid under optional
    stopping and non-anticipating adaptive stream selection when each stream's
    observations satisfy the stated conditional Bernoulli model.
    """

    count.validate()
    if not 0.0 < delta < 1.0:
        raise ValueError("delta must lie in (0, 1)")
    if stream_count < 1:
        raise ValueError("stream_count must be positive")
    if count.trials == 0:
        return 0.0, 1.0

    n = count.trials
    alpha = delta / (stream_count * n * (n + 1))
    radius = sqrt(log(2.0 / alpha) / (2.0 * n))
    estimate = count.successes / n
    return max(0.0, estimate - radius), min(1.0, estimate + radius)


def allocated_error_budget(
    *,
    delta: float,
    stream_count: int,
    maximum_trials: int,
) -> float:
    if maximum_trials < 1:
        return 0.0
    return sum(
        delta / (stream_count * n * (n + 1))
        for _stream in range(stream_count)
        for n in range(1, maximum_trials + 1)
    )


def intervals_disjoint(
    left: tuple[float, float],
    right: tuple[float, float],
) -> bool:
    return left[1] < right[0] or right[1] < left[0]


def retained_symmetries(
    ambient_group: Sequence[Permutation],
    channel_counts: Sequence[Sequence[BernoulliCount]],
    *,
    delta: float,
) -> frozenset[Permutation]:
    if not ambient_group:
        raise ValueError("ambient group must be non-empty")
    action_count = len(ambient_group[0])
    if not channel_counts:
        return frozenset(ambient_group)
    if any(len(channel) != action_count for channel in channel_counts):
        raise ValueError("every channel must cover every action")

    stream_count = len(channel_counts) * action_count
    intervals = tuple(
        tuple(
            time_uniform_hoeffding_interval(
                count,
                delta=delta,
                stream_count=stream_count,
            )
            for count in channel
        )
        for channel in channel_counts
    )

    retained: set[Permutation] = set()
    for permutation in ambient_group:
        rejected = any(
            intervals_disjoint(channel[action], channel[permutation[action]])
            for channel in intervals
            for action in range(action_count)
        )
        if not rejected:
            retained.add(permutation)
    return frozenset(retained)


def plausible_subgroup_version_space(
    ambient_group: Sequence[Permutation],
    retained_elements: Iterable[Permutation],
) -> tuple[Subgroup, ...]:
    retained = frozenset(retained_elements)
    return tuple(
        subgroup
        for subgroup in enumerate_subgroups(ambient_group)
        if subgroup <= retained
    )


def pointwise_stabilizer(
    subgroup: Subgroup,
    anchored_actions: Iterable[int],
) -> Subgroup:
    anchors = tuple(anchored_actions)
    return frozenset(
        permutation
        for permutation in subgroup
        if all(permutation[action] == action for action in anchors)
    )


def minimum_robust_bases(
    version_space: Sequence[Subgroup],
    action_count: int,
) -> tuple[tuple[int, ...], ...]:
    if not version_space:
        raise ValueError("version space must contain at least the trivial subgroup")
    for size in range(action_count + 1):
        bases = tuple(
            subset
            for subset in combinations(range(action_count), size)
            if all(
                len(pointwise_stabilizer(subgroup, subset)) == 1
                for subgroup in version_space
            )
        )
        if bases:
            return bases
    raise AssertionError("the full action set must ground every subgroup")


def build_version_certificate(
    ambient_group: Sequence[Permutation],
    retained_elements: Iterable[Permutation],
) -> SymmetryVersionCertificate:
    if not ambient_group:
        raise ValueError("ambient group must be non-empty")
    action_count = len(ambient_group[0])
    retained = frozenset(retained_elements)
    version_space = plausible_subgroup_version_space(ambient_group, retained)
    supported = frozenset(
        element
        for subgroup in version_space
        for element in subgroup
    )
    robust_bases = minimum_robust_bases(version_space, action_count)
    envelope = generated_subgroup(supported, action_count)
    envelope_base = minimum_base_size(tuple(envelope), action_count)
    return SymmetryVersionCertificate(
        retained,
        version_space,
        supported,
        robust_bases,
        envelope,
        envelope_base,
    )


def marker_counts(
    *,
    action_count: int,
    marked_actions: Sequence[int],
    trials: int,
) -> tuple[tuple[BernoulliCount, ...], ...]:
    return tuple(
        tuple(
            BernoulliCount(trials if action == marker else 0, trials)
            for action in range(action_count)
        )
        for marker in marked_actions
    )


def balanced_counts(
    *,
    action_count: int,
    channel_count: int,
    trials: int,
) -> tuple[tuple[BernoulliCount, ...], ...]:
    if trials % 2:
        raise ValueError("balanced fixture requires an even trial count")
    return tuple(
        tuple(BernoulliCount(trials // 2, trials) for _ in range(action_count))
        for _ in range(channel_count)
    )


def experiment_choice(
    name: str,
    ambient_group: Sequence[Permutation],
    retained_elements: Iterable[Permutation],
) -> ExperimentChoice:
    certificate = build_version_certificate(ambient_group, retained_elements)
    return ExperimentChoice(
        name,
        len(certificate.retained_elements),
        len(ambient_group) - len(certificate.retained_elements),
        len(certificate.plausible_subgroups),
        certificate.robust_base_size,
    )


def run_experiment() -> dict[str, object]:
    delta = 0.05

    cycle_eight_group = graph_automorphisms(cycle_graph(8))
    early_retained = retained_symmetries(
        cycle_eight_group,
        marker_counts(action_count=8, marked_actions=(0, 1), trials=16),
        delta=delta,
    )
    late_retained = retained_symmetries(
        cycle_eight_group,
        marker_counts(action_count=8, marked_actions=(0, 1), trials=32),
        delta=delta,
    )
    null_retained = retained_symmetries(
        cycle_eight_group,
        balanced_counts(action_count=8, channel_count=2, trials=64),
        delta=delta,
    )
    early_certificate = build_version_certificate(cycle_eight_group, early_retained)
    late_certificate = build_version_certificate(cycle_eight_group, late_retained)
    null_certificate = build_version_certificate(cycle_eight_group, null_retained)

    square_group = graph_automorphisms(cycle_graph(4))
    identity = identity_permutation(4)
    rotation = tuple((index + 1) % 4 for index in range(4))
    reverse_rotation = inverse(rotation)
    reflection = tuple((-index) % 4 for index in range(4))
    rotations = generated_subgroup((rotation,), 4)

    logically_inconsistent = build_version_certificate(
        square_group,
        (identity, rotation),
    )
    incompatible_worlds = build_version_certificate(
        square_group,
        (*rotations, reflection),
    )

    count_greedy = experiment_choice(
        "reject-more-but-leave-reflection",
        square_group,
        (identity, reflection),
    )
    version_space_choice = experiment_choice(
        "reject-fewer-but-break-every-subgroup",
        square_group,
        (identity, rotation, reverse_rotation),
    )

    checks = {
        "anytime_budget_below_delta": allocated_error_budget(
            delta=delta,
            stream_count=16,
            maximum_trials=100_000,
        ) < delta,
        "no_signal_preserves_full_group": len(null_retained) == 16,
        "early_evidence_does_not_overground": len(early_retained) == 16,
        "late_evidence_reaches_identity": len(late_retained) == 1,
        "early_symmetry_tax_is_two_anchors": early_certificate.robust_base_size == 2,
        "late_symmetry_tax_is_zero": late_certificate.robust_base_size == 0,
        "logical_pruning_removes_impossible_rotation": (
            len(logically_inconsistent.retained_elements) == 2
            and len(logically_inconsistent.logically_supported_elements) == 1
        ),
        "version_space_beats_single_group_envelope": (
            incompatible_worlds.robust_base_size == 1
            and incompatible_worlds.envelope_base_size == 2
        ),
        "element_count_greedy_is_misdirected": (
            count_greedy.rejected_elements > version_space_choice.rejected_elements
            and count_greedy.robust_base_size > version_space_choice.robust_base_size
        ),
    }

    return {
        "capability_id": "CAP-GEN-002-ASVS-001",
        "claim": (
            "an anytime-safe subgroup version space prevents finite-sample elementwise "
            "symmetry decisions from understating residual grounding ambiguity"
        ),
        "claim_boundary": (
            "time-uniform confidence sequences, sequential familywise error control, "
            "active hypothesis testing, subgroup enumeration, automorphism groups, and "
            "group bases are prior art. The unverified novelty candidate is their joint "
            "resource-accounted acquisition from one raw mixed interaction stream."
        ),
        "time_uniform_certificate": {
            "delta": delta,
            "allocated_budget_through_100000": allocated_error_budget(
                delta=delta,
                stream_count=16,
                maximum_trials=100_000,
            ),
            "ambient_group_size": len(cycle_eight_group),
            "ambient_subgroups": len(enumerate_subgroups(cycle_eight_group)),
        },
        "finite_sample_progression": {
            "trials_16": {
                "retained_elements": len(early_retained),
                "plausible_subgroups": len(early_certificate.plausible_subgroups),
                "robust_base_size": early_certificate.robust_base_size,
            },
            "trials_32": {
                "retained_elements": len(late_retained),
                "plausible_subgroups": len(late_certificate.plausible_subgroups),
                "robust_base_size": late_certificate.robust_base_size,
            },
            "equal_means_control": {
                "retained_elements": len(null_retained),
                "plausible_subgroups": len(null_certificate.plausible_subgroups),
                "robust_base_size": null_certificate.robust_base_size,
            },
        },
        "logical_pruning": {
            "raw_retained_elements": len(logically_inconsistent.retained_elements),
            "logically_supported_elements": len(
                logically_inconsistent.logically_supported_elements
            ),
            "plausible_subgroups": len(logically_inconsistent.plausible_subgroups),
        },
        "version_space_vs_envelope": {
            "raw_retained_elements": len(incompatible_worlds.retained_elements),
            "plausible_subgroups": len(incompatible_worlds.plausible_subgroups),
            "robust_base_size": incompatible_worlds.robust_base_size,
            "generated_envelope_size": len(incompatible_worlds.generated_envelope),
            "generated_envelope_base_size": incompatible_worlds.envelope_base_size,
        },
        "active_choice_counterexample": {
            "element_count_choice": count_greedy.__dict__,
            "version_space_choice": version_space_choice.__dict__,
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2, sort_keys=True))
