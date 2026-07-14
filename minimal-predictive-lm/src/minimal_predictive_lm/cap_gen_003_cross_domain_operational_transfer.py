from __future__ import annotations

from dataclasses import dataclass
import json
from math import ceil, log2
from typing import Iterable, Mapping, Sequence


State = str
Edge = tuple[State, State]
Transition = tuple[State, State]


@dataclass(frozen=True)
class InteractionDomain:
    name: str
    states: tuple[State, ...]
    passive_edges: tuple[Edge, ...]
    active_transitions: tuple[Transition, ...]
    action_surface: str = "step"


@dataclass(frozen=True)
class SharedOperatorCertificate:
    operator_name: str
    training_domains: tuple[str, ...]
    structural_family: str
    minimum_domain_size: int
    maximum_domain_size: int


@dataclass(frozen=True)
class TransferResult:
    status: str
    predictions: tuple[Transition, ...]
    orientation_index: int | None
    candidate_count: int
    grounded_interactions: int
    reason: str


@dataclass(frozen=True)
class ResourceComparison:
    separate_control_entries: int
    shared_control_entries: int
    separate_active_interactions: int
    shared_active_interactions: int
    heldout_interaction_savings: int
    control_entry_reduction: float


def normalize_edge(left: State, right: State) -> Edge:
    return (left, right) if left < right else (right, left)


def _validate_domain(domain: InteractionDomain) -> None:
    if len(domain.states) < 3:
        raise ValueError("at least three states are required")
    if len(set(domain.states)) != len(domain.states):
        raise ValueError("states must be unique")
    state_set = set(domain.states)
    for left, right in domain.passive_edges:
        if left == right:
            raise ValueError("self edges are not supported")
        if left not in state_set or right not in state_set:
            raise ValueError("passive edge references an unknown state")
    for source, target in domain.active_transitions:
        if source not in state_set or target not in state_set:
            raise ValueError("active transition references an unknown state")


def adjacency(domain: InteractionDomain) -> dict[State, tuple[State, ...]]:
    _validate_domain(domain)
    rows: dict[State, set[State]] = {state: set() for state in domain.states}
    for left, right in domain.passive_edges:
        rows[left].add(right)
        rows[right].add(left)
    return {state: tuple(sorted(neighbours)) for state, neighbours in rows.items()}


def _walk_cycle(
    neighbours: Mapping[State, Sequence[State]],
    start: State,
    first: State,
) -> tuple[State, ...] | None:
    order = [start]
    previous = start
    current = first
    while current != start:
        if current in order:
            return None
        order.append(current)
        candidates = [node for node in neighbours[current] if node != previous]
        if len(candidates) != 1:
            return None
        previous, current = current, candidates[0]
    return tuple(order)


def cycle_orders(domain: InteractionDomain) -> tuple[tuple[State, ...], ...]:
    """Return the two orientations of a connected simple cycle, or an empty tuple."""

    rows = adjacency(domain)
    if any(len(nodes) != 2 for nodes in rows.values()):
        return ()
    start = min(domain.states)
    output: list[tuple[State, ...]] = []
    for first in rows[start]:
        order = _walk_cycle(rows, start, first)
        if order is not None and len(order) == len(domain.states):
            output.append(order)
    unique = tuple(dict.fromkeys(output))
    return unique if len(unique) == 2 else ()


def successor_map(order: Sequence[State]) -> dict[State, State]:
    if len(order) < 3:
        raise ValueError("a cycle order needs at least three states")
    return {
        state: order[(index + 1) % len(order)]
        for index, state in enumerate(order)
    }


def transition_table(order: Sequence[State]) -> tuple[Transition, ...]:
    mapping = successor_map(order)
    return tuple(sorted(mapping.items()))


def consistent_orientations(domain: InteractionDomain) -> tuple[int, ...]:
    orders = cycle_orders(domain)
    if not orders:
        return ()
    observed = dict(domain.active_transitions)
    if len(observed) != len(domain.active_transitions):
        raise ValueError("a source may have only one observed active successor")
    output: list[int] = []
    for index, order in enumerate(orders):
        mapping = successor_map(order)
        if all(mapping[source] == target for source, target in observed.items()):
            output.append(index)
    return tuple(output)


def learn_shared_cycle_operator(
    training_domains: Sequence[InteractionDomain],
) -> SharedOperatorCertificate:
    if len(training_domains) < 2:
        raise ValueError("cross-domain certification requires at least two domains")
    sizes: list[int] = []
    names: list[str] = []
    for domain in training_domains:
        if len(domain.active_transitions) != len(domain.states):
            raise ValueError("training domains require complete active support")
        orientations = consistent_orientations(domain)
        if len(orientations) != 1:
            raise ValueError("training domain does not certify one oriented-cycle operator")
        sizes.append(len(domain.states))
        names.append(domain.name)
    return SharedOperatorCertificate(
        operator_name="oriented-cycle-successor",
        training_domains=tuple(names),
        structural_family="connected-degree-two-cycle",
        minimum_domain_size=min(sizes),
        maximum_domain_size=max(sizes),
    )


def transfer_operator(
    certificate: SharedOperatorCertificate,
    domain: InteractionDomain,
) -> TransferResult:
    if certificate.structural_family != "connected-degree-two-cycle":
        raise ValueError("unsupported certificate family")
    orders = cycle_orders(domain)
    if not orders:
        return TransferResult(
            status="unsupported",
            predictions=(),
            orientation_index=None,
            candidate_count=0,
            grounded_interactions=len(domain.active_transitions),
            reason="held-out passive topology is not a connected simple cycle",
        )
    candidates = consistent_orientations(domain)
    if len(candidates) == 0:
        return TransferResult(
            status="contradiction",
            predictions=(),
            orientation_index=None,
            candidate_count=0,
            grounded_interactions=len(domain.active_transitions),
            reason="grounded transitions contradict every certified orientation",
        )
    if len(candidates) > 1:
        return TransferResult(
            status="abstain",
            predictions=(),
            orientation_index=None,
            candidate_count=len(candidates),
            grounded_interactions=len(domain.active_transitions),
            reason="orientation symmetry remains unresolved",
        )
    orientation = candidates[0]
    return TransferResult(
        status="transferred",
        predictions=transition_table(orders[orientation]),
        orientation_index=orientation,
        candidate_count=1,
        grounded_interactions=len(domain.active_transitions),
        reason="one grounded edge selects the domain adapter orientation",
    )


def separate_table_predictions(domain: InteractionDomain) -> tuple[Transition, ...]:
    return tuple(sorted(domain.active_transitions))


def surface_token_transfer(
    training_domain: InteractionDomain,
    heldout_domain: InteractionDomain,
) -> tuple[Transition, ...]:
    """A deliberately surface-only baseline that reuses the training orientation index."""

    if training_domain.action_surface != heldout_domain.action_surface:
        return ()
    training_candidates = consistent_orientations(training_domain)
    heldout_orders = cycle_orders(heldout_domain)
    if len(training_candidates) != 1 or not heldout_orders:
        return ()
    return transition_table(heldout_orders[training_candidates[0]])


def exact_accuracy(
    predictions: Iterable[Transition],
    truth: Iterable[Transition],
) -> float:
    predicted = dict(predictions)
    expected = dict(truth)
    if not expected:
        return 0.0
    correct = sum(predicted.get(source) == target for source, target in expected.items())
    return correct / len(expected)


def _empty_cycle(name: str, states: Sequence[State]) -> InteractionDomain:
    edges = tuple(
        normalize_edge(states[index], states[(index + 1) % len(states)])
        for index in range(len(states))
    )
    return InteractionDomain(
        name=name,
        states=tuple(states),
        passive_edges=tuple(sorted(set(edges))),
        active_transitions=(),
    )


def cycle_fixture(
    name: str,
    states: Sequence[State],
    orientation_index: int,
    active_sources: Sequence[State] | None = None,
) -> tuple[InteractionDomain, tuple[Transition, ...]]:
    empty = _empty_cycle(name, states)
    orders = cycle_orders(empty)
    if orientation_index not in (0, 1):
        raise ValueError("orientation index must be zero or one")
    truth = transition_table(orders[orientation_index])
    truth_map = dict(truth)
    sources = tuple(states) if active_sources is None else tuple(active_sources)
    active = tuple((source, truth_map[source]) for source in sources)
    return (
        InteractionDomain(
            name=name,
            states=tuple(states),
            passive_edges=empty.passive_edges,
            active_transitions=active,
        ),
        truth,
    )


def path_fixture(name: str, states: Sequence[State]) -> InteractionDomain:
    edges = tuple(
        normalize_edge(states[index], states[index + 1])
        for index in range(len(states) - 1)
    )
    return InteractionDomain(
        name=name,
        states=tuple(states),
        passive_edges=edges,
        active_transitions=(),
    )


def resource_comparison(
    training_domains: Sequence[InteractionDomain],
    heldout_size: int,
    heldout_grounded_interactions: int,
) -> ResourceComparison:
    domain_count = len(training_domains) + 1
    separate_entries = sum(len(domain.states) for domain in training_domains) + heldout_size
    shared_entries = 1 + domain_count  # one operator plus one orientation adapter per domain
    separate_interactions = separate_entries
    shared_interactions = (
        sum(len(domain.active_transitions) for domain in training_domains)
        + heldout_grounded_interactions
    )
    return ResourceComparison(
        separate_control_entries=separate_entries,
        shared_control_entries=shared_entries,
        separate_active_interactions=separate_interactions,
        shared_active_interactions=shared_interactions,
        heldout_interaction_savings=heldout_size - heldout_grounded_interactions,
        control_entry_reduction=separate_entries / shared_entries,
    )


def run_experiment() -> dict[str, object]:
    alpha, alpha_truth = cycle_fixture(
        "alpha-symbols",
        ("amber", "birch", "cedar", "dune", "ember"),
        orientation_index=0,
    )
    beta, beta_truth = cycle_fixture(
        "beta-codes",
        ("q7", "m2", "z9", "a4", "t1", "k8", "c3"),
        orientation_index=1,
    )
    gamma_full, gamma_truth = cycle_fixture(
        "gamma-commands",
        ("north", "violet", "copper", "echo", "jade", "lima", "orbit", "piano", "quartz"),
        orientation_index=1,
    )
    gamma_truth_map = dict(gamma_truth)
    anchor_source = gamma_full.states[0]
    gamma_one_anchor = InteractionDomain(
        name=gamma_full.name,
        states=gamma_full.states,
        passive_edges=gamma_full.passive_edges,
        active_transitions=((anchor_source, gamma_truth_map[anchor_source]),),
    )
    gamma_zero_anchor = InteractionDomain(
        name=gamma_full.name,
        states=gamma_full.states,
        passive_edges=gamma_full.passive_edges,
        active_transitions=(),
    )

    certificate = learn_shared_cycle_operator((alpha, beta))
    transferred = transfer_operator(certificate, gamma_one_anchor)
    zero_anchor = transfer_operator(certificate, gamma_zero_anchor)
    surface_predictions = surface_token_transfer(alpha, gamma_zero_anchor)
    separate_predictions = separate_table_predictions(gamma_one_anchor)
    unsupported = transfer_operator(
        certificate,
        path_fixture("branching-control", ("p0", "p1", "p2", "p3", "p4")),
    )
    resources = resource_comparison(
        (alpha, beta),
        heldout_size=len(gamma_full.states),
        heldout_grounded_interactions=1,
    )

    transferred_accuracy = exact_accuracy(transferred.predictions, gamma_truth)
    surface_accuracy = exact_accuracy(surface_predictions, gamma_truth)
    separate_accuracy = exact_accuracy(separate_predictions, gamma_truth)

    result = {
        "capability_id": "CAP-GEN-003-COT-001",
        "strategic_pivot": "stop refining CAP-GEN-002 finite-symmetry details and test reusable operational knowledge across heterogeneous surfaces",
        "training_domains": [
            {"name": alpha.name, "state_count": len(alpha.states), "accuracy": exact_accuracy(alpha.active_transitions, alpha_truth)},
            {"name": beta.name, "state_count": len(beta.states), "accuracy": exact_accuracy(beta.active_transitions, beta_truth)},
        ],
        "heldout_domain": {
            "name": gamma_full.name,
            "state_count": len(gamma_full.states),
            "grounded_interactions": 1,
            "transferred_status": transferred.status,
            "transferred_exact_accuracy": transferred_accuracy,
            "transferred_predictions": len(transferred.predictions),
            "zero_anchor_status": zero_anchor.status,
            "zero_anchor_candidates": zero_anchor.candidate_count,
            "surface_token_baseline_accuracy": surface_accuracy,
            "separate_table_baseline_accuracy": separate_accuracy,
            "separate_table_baseline_coverage": len(separate_predictions) / len(gamma_truth),
        },
        "structural_rejection": {
            "status": unsupported.status,
            "reason": unsupported.reason,
        },
        "resources": {
            "separate_control_entries": resources.separate_control_entries,
            "shared_control_entries": resources.shared_control_entries,
            "control_entry_reduction": resources.control_entry_reduction,
            "separate_active_interactions": resources.separate_active_interactions,
            "shared_active_interactions": resources.shared_active_interactions,
            "heldout_interaction_savings": resources.heldout_interaction_savings,
        },
        "passed": (
            transferred.status == "transferred"
            and transferred_accuracy == 1.0
            and zero_anchor.status == "abstain"
            and zero_anchor.candidate_count == 2
            and surface_accuracy == 0.0
            and len(separate_predictions) == 1
            and unsupported.status == "unsupported"
            and resources.heldout_interaction_savings == 8
        ),
        "claim_boundary": (
            "MDP homomorphisms, action equivariance, graph automorphisms, program-library learning, "
            "generalist agents, and cross-embodiment latent actions are prior art. COT-001 is a finite "
            "bridge gate showing that surface sharing is insufficient and that certified operational "
            "structure can reduce held-out grounding. It is not raw natural-language learning, public "
            "benchmark progress, or human-level intelligence."
        ),
    }
    return result


def main() -> None:
    print(json.dumps(run_experiment(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
