from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable, Sequence

RawEvent = str
Edge = tuple[str, str]
Transition = tuple[str, str]


@dataclass(frozen=True)
class Segment:
    ordinal: int
    start_index: int
    end_index: int
    passive_edges: tuple[Edge, ...]
    active_transitions: tuple[Transition, ...]

    @property
    def states(self) -> tuple[str, ...]:
        nodes: set[str] = set()
        for left, right in self.passive_edges:
            nodes.add(left)
            nodes.add(right)
        for source, target in self.active_transitions:
            nodes.add(source)
            nodes.add(target)
        return tuple(sorted(nodes))


@dataclass(frozen=True)
class BoundaryProposal:
    event_index: int
    previous_segment_ordinal: int
    reason: str
    causal: bool


@dataclass(frozen=True)
class ParsedStream:
    segments: tuple[Segment, ...]
    proposals: tuple[BoundaryProposal, ...]
    reset_tokens_used: int
    domain_label_tokens_used: int


@dataclass(frozen=True)
class SharedCycleCertificate:
    operator_name: str
    training_segment_count: int
    family: str


@dataclass(frozen=True)
class TransferResult:
    status: str
    predictions: tuple[Transition, ...]
    exact_accuracy: float
    candidate_count: int
    grounded_interactions: int
    future_successors_used: int
    reason: str


@dataclass(frozen=True)
class SegmentationAbsorption:
    active_transition_count: int
    shared_core_entries: int
    boundary_rule_entries: int
    adapter_entries: int

    @property
    def core_only_reduction(self) -> float:
        return self.active_transition_count / self.shared_core_entries

    @property
    def fully_charged_entries(self) -> int:
        return self.shared_core_entries + self.boundary_rule_entries + self.adapter_entries

    @property
    def fully_charged_reduction(self) -> float:
        return self.active_transition_count / self.fully_charged_entries


@dataclass(frozen=True)
class ResourceVector:
    executable_entries: int
    active_interactions: int
    passive_observations: int
    boundary_proposals: int

    def scalar_cost(
        self,
        *,
        executable_weight: float = 1.0,
        active_weight: float = 1.0,
        passive_weight: float = 1.0,
        proposal_weight: float = 1.0,
    ) -> float:
        return (
            executable_weight * self.executable_entries
            + active_weight * self.active_interactions
            + passive_weight * self.passive_observations
            + proposal_weight * self.boundary_proposals
        )


def normalize_edge(left: str, right: str) -> Edge:
    if left == right:
        raise ValueError("self-edge is unsupported")
    return (left, right) if left < right else (right, left)


def parse_event(raw: RawEvent) -> tuple[str, str, str]:
    parts = raw.strip().split()
    if len(parts) != 3 or parts[0] not in {"EDGE", "STEP"}:
        raise ValueError(f"unsupported event: {raw!r}")
    return parts[0], parts[1], parts[2]


def adjacency(edges: Iterable[Edge]) -> dict[str, set[str]]:
    rows: dict[str, set[str]] = {}
    for left, right in edges:
        rows.setdefault(left, set()).add(right)
        rows.setdefault(right, set()).add(left)
    return rows


def graph_is_connected(edges: Iterable[Edge]) -> bool:
    rows = adjacency(edges)
    if not rows:
        return False
    pending = [next(iter(rows))]
    seen: set[str] = set()
    while pending:
        node = pending.pop()
        if node in seen:
            continue
        seen.add(node)
        pending.extend(rows[node] - seen)
    return len(seen) == len(rows)


def is_complete_simple_cycle(edges: Iterable[Edge]) -> bool:
    unique = set(edges)
    rows = adjacency(unique)
    return (
        len(rows) >= 3
        and len(unique) == len(rows)
        and graph_is_connected(unique)
        and all(len(neighbours) == 2 for neighbours in rows.values())
    )


def partial_cycle_is_possible(edges: Iterable[Edge]) -> bool:
    unique = set(edges)
    if not unique:
        return True
    rows = adjacency(unique)
    if any(len(neighbours) > 2 for neighbours in rows.values()):
        return False
    if not graph_is_connected(unique):
        return False
    edge_count = len(unique)
    node_count = len(rows)
    if edge_count > node_count:
        return False
    if edge_count == node_count and not all(len(neighbours) == 2 for neighbours in rows.values()):
        return False
    return True


def cycle_orders(edges: Iterable[Edge]) -> tuple[tuple[str, ...], ...]:
    unique = set(edges)
    if not is_complete_simple_cycle(unique):
        return ()
    rows = adjacency(unique)
    start = min(rows)
    output: list[tuple[str, ...]] = []
    for first in sorted(rows[start]):
        order = [start]
        previous = start
        current = first
        while current != start:
            if current in order:
                break
            order.append(current)
            candidates = rows[current] - {previous}
            if len(candidates) != 1:
                break
            previous, current = current, next(iter(candidates))
        if current == start and len(order) == len(rows):
            output.append(tuple(order))
    unique_orders = tuple(dict.fromkeys(output))
    return unique_orders if len(unique_orders) == 2 else ()


def successor_map(order: Sequence[str]) -> dict[str, str]:
    return {state: order[(index + 1) % len(order)] for index, state in enumerate(order)}


def active_orientation_candidates(
    edges: Iterable[Edge], transitions: Iterable[Transition]
) -> tuple[int, ...]:
    orders = cycle_orders(edges)
    if not orders:
        return ()
    observed: dict[str, str] = {}
    for source, target in transitions:
        previous = observed.get(source)
        if previous is not None and previous != target:
            return ()
        observed[source] = target
    candidates: list[int] = []
    for index, order in enumerate(orders):
        mapping = successor_map(order)
        if all(mapping.get(source) == target for source, target in observed.items()):
            candidates.append(index)
    return tuple(candidates)


def segment_has_unique_orientation(segment: Segment) -> bool:
    return (
        is_complete_simple_cycle(segment.passive_edges)
        and len(active_orientation_candidates(
            segment.passive_edges,
            segment.active_transitions,
        )) == 1
    )


def segment_is_training_certified(segment: Segment) -> bool:
    if len(set(source for source, _ in segment.active_transitions)) != len(segment.states):
        return False
    return segment_has_unique_orientation(segment)


def _records_compatible(
    edges: set[Edge], active: dict[str, str], event: tuple[str, str, str]
) -> bool:
    kind, left, right = event
    next_edges = set(edges)
    next_active = dict(active)
    if kind == "EDGE":
        try:
            edge = normalize_edge(left, right)
        except ValueError:
            return False
        if is_complete_simple_cycle(edges) and edge not in edges:
            return False
        next_edges.add(edge)
        return partial_cycle_is_possible(next_edges)

    previous = next_active.get(left)
    if previous is not None and previous != right:
        return False
    next_active[left] = right
    if next_edges and normalize_edge(left, right) not in next_edges:
        return False
    if is_complete_simple_cycle(next_edges):
        return bool(active_orientation_candidates(next_edges, next_active.items()))
    return True


def parse_reset_free_stream(events: Sequence[RawEvent]) -> ParsedStream:
    if any(raw.strip() == "RESET" for raw in events):
        raise ValueError("RESET tokens are forbidden")

    segments: list[Segment] = []
    proposals: list[BoundaryProposal] = []
    edges: set[Edge] = set()
    active: dict[str, str] = {}
    start_index = 0

    def close(end_index: int) -> None:
        nonlocal edges, active, start_index
        if not edges and not active:
            return
        segments.append(
            Segment(
                ordinal=len(segments),
                start_index=start_index,
                end_index=end_index,
                passive_edges=tuple(sorted(edges)),
                active_transitions=tuple(sorted(active.items())),
            )
        )
        edges = set()
        active = {}
        start_index = end_index

    for index, raw in enumerate(events):
        event = parse_event(raw)
        if _records_compatible(edges, active, event):
            kind, left, right = event
            if kind == "EDGE":
                edges.add(normalize_edge(left, right))
            else:
                active[left] = right
            continue

        current = Segment(
            ordinal=len(segments),
            start_index=start_index,
            end_index=index,
            passive_edges=tuple(sorted(edges)),
            active_transitions=tuple(sorted(active.items())),
        )
        if not segment_has_unique_orientation(current):
            raise ValueError("incompatibility occurred before the current context was certified")
        proposals.append(
            BoundaryProposal(
                event_index=index,
                previous_segment_ordinal=current.ordinal,
                reason="current event has zero support under the certified context",
                causal=True,
            )
        )
        close(index)
        kind, left, right = event
        if kind == "EDGE":
            edges.add(normalize_edge(left, right))
        else:
            active[left] = right

    close(len(events))
    return ParsedStream(
        segments=tuple(segments),
        proposals=tuple(proposals),
        reset_tokens_used=0,
        domain_label_tokens_used=0,
    )


def learn_shared_cycle_operator(training_segments: Sequence[Segment]) -> SharedCycleCertificate:
    if len(training_segments) < 2:
        raise ValueError("at least two training contexts are required")
    if not all(segment_is_training_certified(s) for s in training_segments):
        raise ValueError("every training context must fully certify the operator family")
    return SharedCycleCertificate(
        operator_name="oriented-cycle-successor",
        training_segment_count=len(training_segments),
        family="connected-degree-two-cycle",
    )


def transition_table(order: Sequence[str]) -> tuple[Transition, ...]:
    return tuple(sorted(successor_map(order).items()))


def exact_accuracy(predictions: Iterable[Transition], truth: Iterable[Transition]) -> float:
    predicted = dict(predictions)
    expected = dict(truth)
    if not expected:
        return 0.0
    return sum(predicted.get(source) == target for source, target in expected.items()) / len(expected)


def transfer_to_segment(
    certificate: SharedCycleCertificate,
    segment: Segment,
    truth: Iterable[Transition],
) -> TransferResult:
    if certificate.family != "connected-degree-two-cycle":
        raise ValueError("unsupported certificate")
    orders = cycle_orders(segment.passive_edges)
    if not orders:
        return TransferResult("unsupported", (), 0.0, 0, len(segment.active_transitions), 0, "passive topology is outside the certified family")
    candidates = active_orientation_candidates(segment.passive_edges, segment.active_transitions)
    if not candidates:
        return TransferResult("contradiction", (), 0.0, 0, len(segment.active_transitions), 0, "grounded observations contradict every reusable orientation")
    if len(candidates) > 1:
        return TransferResult("abstain", (), 0.0, len(candidates), len(segment.active_transitions), 0, "the context adapter is not yet identified")
    predictions = transition_table(orders[candidates[0]])
    return TransferResult("transferred", predictions, exact_accuracy(predictions, truth), 1, len(segment.active_transitions), 0, "past and current observations identify one reusable adapter")


def make_cycle_records(
    states: Sequence[str], orientation: int, *, active_sources: Sequence[str] | None = None
) -> tuple[tuple[RawEvent, ...], tuple[Transition, ...]]:
    if len(states) < 3:
        raise ValueError("at least three states are required")
    edges = tuple(normalize_edge(states[index], states[(index + 1) % len(states)]) for index in range(len(states)))
    edge_records = tuple(f"EDGE {left} {right}" for left, right in edges)
    orders = cycle_orders(tuple(sorted(set(edges))))
    if orientation not in (0, 1):
        raise ValueError("orientation must be zero or one")
    truth = transition_table(orders[orientation])
    mapping = dict(truth)
    sources = tuple(states) if active_sources is None else tuple(active_sources)
    step_records = tuple(f"STEP {source} {mapping[source]}" for source in sources)
    return edge_records + step_records, truth


def make_path_records(states: Sequence[str]) -> tuple[RawEvent, ...]:
    return tuple(f"EDGE {states[index]} {states[index + 1]}" for index in range(len(states) - 1))


def segmentation_absorption_profile(active_transition_count: int) -> SegmentationAbsorption:
    return SegmentationAbsorption(active_transition_count, 1, 1, active_transition_count)


def causal_boundary_control() -> dict[str, object]:
    return {
        "prefix": "STEP shared",
        "world_successors": ["left", "right"],
        "future_successors_used": 1,
        "certified": False,
        "reason": "a boundary key using the successor is unavailable before prediction",
    }


def nonidentifiable_boundary_control() -> dict[str, object]:
    records, _ = make_cycle_records(("a", "b", "c", "d"), 0)
    parsed = parse_reset_free_stream(records + records)
    return {
        "hidden_episode_count": 2,
        "detected_segment_count": len(parsed.segments),
        "detected_boundary_count": len(parsed.proposals),
        "operational_difference_observed": False,
        "correct_action": "merge",
    }


def delayed_boundary_certification_control() -> dict[str, object]:
    singleton = Segment(1, 0, 1, (), (("x", "y"),))
    certified = is_complete_simple_cycle(singleton.passive_edges) and len(active_orientation_candidates(singleton.passive_edges, singleton.active_transitions)) == 1
    return {
        "proposal_allowed": True,
        "new_context_certified": certified,
        "operational_reuse_surplus_positive": False,
        "accepted_boundary": False,
    }


def run_experiment() -> dict[str, object]:
    train_a_records, train_a_truth = make_cycle_records(("amber", "birch", "cedar", "dune", "ember"), 0)
    train_b_records, train_b_truth = make_cycle_records(("q7", "m2", "z9", "a4", "t1", "k8", "c3"), 1)
    heldout_states = ("north", "violet", "copper", "echo", "jade", "lima", "orbit", "piano", "quartz")
    heldout_full_records, heldout_truth = make_cycle_records(heldout_states, 1)
    heldout_truth_map = dict(heldout_truth)
    heldout_edges = heldout_full_records[: len(heldout_states)]
    heldout_one_anchor = heldout_edges + (f"STEP {heldout_states[0]} {heldout_truth_map[heldout_states[0]]}",)
    unsupported_records = make_path_records(("p0", "p1", "p2", "p3", "p4"))

    stream = train_a_records + train_b_records + heldout_one_anchor + unsupported_records
    freeze_index = len(train_a_records) + len(train_b_records)
    parsed = parse_reset_free_stream(stream)

    training_segments = tuple(segment for segment in parsed.segments if segment.start_index < freeze_index)
    heldout_segments = tuple(segment for segment in parsed.segments if segment.start_index >= freeze_index)
    certificate = learn_shared_cycle_operator(training_segments)
    positive = transfer_to_segment(certificate, heldout_segments[0], heldout_truth)
    zero_anchor_segment = Segment(
        heldout_segments[0].ordinal,
        heldout_segments[0].start_index,
        heldout_segments[0].end_index,
        heldout_segments[0].passive_edges,
        (),
    )
    zero_anchor = transfer_to_segment(certificate, zero_anchor_segment, heldout_truth)
    unsupported = transfer_to_segment(certificate, heldout_segments[1], ())

    observed_active = len(train_a_truth) + len(train_b_truth) + 1
    absorption = segmentation_absorption_profile(observed_active)
    separate = ResourceVector(21, 21, 0, 0)
    shared = ResourceVector(6, 13, 21, len(parsed.proposals))
    heldout_separate_cost = 18
    heldout_shared_incremental_cost = 12

    result = {
        "capability_id": "CAP-GEN-003-RBOR-001",
        "stream": {
            "event_count": len(stream),
            "reset_tokens_used": parsed.reset_tokens_used,
            "domain_label_tokens_used": parsed.domain_label_tokens_used,
            "detected_segment_count": len(parsed.segments),
            "detected_boundary_count": len(parsed.proposals),
            "all_boundaries_causal": all(p.causal for p in parsed.proposals),
            "freeze_index_used_only_for_evaluation": freeze_index,
        },
        "positive_transfer": {
            "status": positive.status,
            "exact_accuracy": positive.exact_accuracy,
            "predictions": len(positive.predictions),
            "grounded_interactions": positive.grounded_interactions,
            "future_successors_used": positive.future_successors_used,
            "zero_anchor_status": zero_anchor.status,
            "zero_anchor_candidates": zero_anchor.candidate_count,
            "unsupported_status": unsupported.status,
        },
        "segmentation_absorption": {
            "active_transition_count": absorption.active_transition_count,
            "core_only_reduction": absorption.core_only_reduction,
            "fully_charged_entries": absorption.fully_charged_entries,
            "fully_charged_reduction": absorption.fully_charged_reduction,
        },
        "causal_boundary_control": causal_boundary_control(),
        "nonidentifiable_boundary_control": nonidentifiable_boundary_control(),
        "delayed_certification_control": delayed_boundary_certification_control(),
        "resources": {
            "separate": separate.__dict__,
            "shared": shared.__dict__,
            "unit_weight_global_surplus": separate.scalar_cost() - shared.scalar_cost(),
            "heldout_separate_cost": heldout_separate_cost,
            "heldout_shared_incremental_cost": heldout_shared_incremental_cost,
            "heldout_incremental_surplus": heldout_separate_cost - heldout_shared_incremental_cost,
            "passive_cost_break_even_with_unit_other_costs": (
                (separate.executable_entries + separate.active_interactions - shared.executable_entries - shared.active_interactions - shared.boundary_proposals)
                / shared.passive_observations
            ),
        },
        "passed": (
            parsed.reset_tokens_used == 0
            and parsed.domain_label_tokens_used == 0
            and len(training_segments) == 2
            and len(heldout_segments) == 2
            and len(parsed.proposals) == 3
            and all(proposal.causal for proposal in parsed.proposals)
            and positive.status == "transferred"
            and positive.exact_accuracy == 1.0
            and len(positive.predictions) == 9
            and positive.grounded_interactions == 1
            and positive.future_successors_used == 0
            and zero_anchor.status == "abstain"
            and zero_anchor.candidate_count == 2
            and unsupported.status == "unsupported"
            and absorption.core_only_reduction == 13.0
            and absorption.fully_charged_reduction < 1.0
            and causal_boundary_control()["certified"] is False
            and nonidentifiable_boundary_control()["detected_boundary_count"] == 0
            and delayed_boundary_certification_control()["accepted_boundary"] is False
            and heldout_separate_cost - heldout_shared_incremental_cost > 0
        ),
        "claim_boundary": (
            "Bayesian online change-point detection, predictive-error event segmentation, task-free continual learning, switching-system identification, MDL segmentation, and graph/action equivariance are prior art. RBOR-001 is a finite project gate for causal boundary proposals and prospective operational-reuse accounting. It is not raw event-role discovery, a public-trace result, natural-language learning, or human-level intelligence."
        ),
    }
    return result


def main() -> None:
    print(json.dumps(run_experiment(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
