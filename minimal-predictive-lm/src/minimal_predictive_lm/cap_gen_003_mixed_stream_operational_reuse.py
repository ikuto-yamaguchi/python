from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Sequence

from .cap_gen_003_cross_domain_operational_transfer import (
    InteractionDomain,
    SharedOperatorCertificate,
    consistent_orientations,
    cycle_fixture,
    exact_accuracy,
    learn_shared_cycle_operator,
    normalize_edge,
    path_fixture,
    transfer_operator,
)


RawEvent = str
Edge = tuple[str, str]
Transition = tuple[str, str]


@dataclass(frozen=True)
class StreamEpisode:
    ordinal: int
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

    def to_domain(self, phase: str) -> InteractionDomain:
        return InteractionDomain(
            name=f"{phase}-episode-{self.ordinal:03d}",
            states=self.states,
            passive_edges=tuple(sorted(set(self.passive_edges))),
            active_transitions=self.active_transitions,
        )


@dataclass(frozen=True)
class ParsedMixedStream:
    training_episodes: tuple[StreamEpisode, ...]
    heldout_episodes: tuple[StreamEpisode, ...]
    reset_count: int
    freeze_count: int


@dataclass(frozen=True)
class MixedStreamCertificate:
    parser_name: str
    operator: SharedOperatorCertificate
    training_episode_count: int
    domain_label_tokens_used: int
    causal_boundary_events: int


@dataclass(frozen=True)
class HeldoutEpisodeResult:
    ordinal: int
    status: str
    exact_accuracy: float
    predictions: int
    candidate_count: int
    grounded_interactions: int


@dataclass(frozen=True)
class SegmentationAbsorptionProfile:
    active_transition_count: int
    shared_core_entries: int
    segmenter_entries: int
    adapter_entries: int
    training_accuracy: float

    @property
    def core_only_reduction(self) -> float:
        return self.active_transition_count / self.shared_core_entries

    @property
    def fully_charged_entries(self) -> int:
        return self.shared_core_entries + self.segmenter_entries + self.adapter_entries

    @property
    def fully_charged_reduction(self) -> float:
        return self.active_transition_count / self.fully_charged_entries


@dataclass(frozen=True)
class ControlResourceProfile:
    separate_control_entries: int
    shared_control_entries: int
    separate_active_interactions: int
    shared_active_interactions: int
    heldout_interaction_savings: int

    @property
    def control_entry_reduction(self) -> float:
        return self.separate_control_entries / self.shared_control_entries


def _parse_episode_records(
    records: Sequence[RawEvent],
    start_ordinal: int = 0,
) -> tuple[StreamEpisode, ...]:
    episodes: list[StreamEpisode] = []
    edges: list[Edge] | None = None
    active: list[Transition] | None = None

    def close_current() -> None:
        nonlocal edges, active
        if edges is None or active is None:
            return
        if not edges and not active:
            raise ValueError("RESET may not create an empty episode")
        episodes.append(
            StreamEpisode(
                ordinal=start_ordinal + len(episodes),
                passive_edges=tuple(sorted(set(edges))),
                active_transitions=tuple(active),
            )
        )
        edges = None
        active = None

    for raw in records:
        line = raw.strip()
        if not line:
            continue
        if line == "RESET":
            close_current()
            edges = []
            active = []
            continue
        if edges is None or active is None:
            raise ValueError("every episode must begin with RESET")
        parts = line.split()
        if len(parts) != 3:
            raise ValueError(f"malformed event: {line}")
        opcode, left, right = parts
        if opcode == "EDGE":
            edges.append(normalize_edge(left, right))
        elif opcode == "STEP":
            active.append((left, right))
        else:
            raise ValueError(f"unsupported event opcode: {opcode}")
    close_current()
    return tuple(episodes)


def parse_mixed_stream(events: Sequence[RawEvent]) -> ParsedMixedStream:
    """Parse one stream with generic RESET and FREEZE events, never domain IDs."""

    freeze_positions = [
        index for index, raw in enumerate(events) if raw.strip() == "FREEZE"
    ]
    if len(freeze_positions) != 1:
        raise ValueError("exactly one FREEZE event is required")
    freeze = freeze_positions[0]
    training_records = events[:freeze]
    heldout_records = events[freeze + 1 :]
    if any(raw.strip() == "FREEZE" for raw in training_records + heldout_records):
        raise ValueError("FREEZE may occur only once")

    training = _parse_episode_records(training_records, start_ordinal=0)
    heldout = _parse_episode_records(
        heldout_records,
        start_ordinal=len(training),
    )
    if len(training) < 2:
        raise ValueError("at least two training episodes are required")
    if not heldout:
        raise ValueError("at least one held-out episode is required")
    return ParsedMixedStream(
        training_episodes=training,
        heldout_episodes=heldout,
        reset_count=sum(raw.strip() == "RESET" for raw in events),
        freeze_count=1,
    )


def certify_mixed_stream(parsed: ParsedMixedStream) -> MixedStreamCertificate:
    training_domains = tuple(
        episode.to_domain("training")
        for episode in parsed.training_episodes
    )
    operator = learn_shared_cycle_operator(training_domains)
    return MixedStreamCertificate(
        parser_name="causal-reset-event-parser",
        operator=operator,
        training_episode_count=len(training_domains),
        domain_label_tokens_used=0,
        causal_boundary_events=parsed.reset_count,
    )


def evaluate_heldout(
    parsed: ParsedMixedStream,
    certificate: MixedStreamCertificate,
    truths: Sequence[Sequence[Transition]],
) -> tuple[HeldoutEpisodeResult, ...]:
    if len(truths) != len(parsed.heldout_episodes):
        raise ValueError("one truth table is required per held-out episode")
    output: list[HeldoutEpisodeResult] = []
    for episode, truth in zip(parsed.heldout_episodes, truths, strict=True):
        result = transfer_operator(
            certificate.operator,
            episode.to_domain("heldout"),
        )
        accuracy = exact_accuracy(result.predictions, truth) if truth else 0.0
        output.append(
            HeldoutEpisodeResult(
                ordinal=episode.ordinal,
                status=result.status,
                exact_accuracy=accuracy,
                predictions=len(result.predictions),
                candidate_count=result.candidate_count,
                grounded_interactions=result.grounded_interactions,
            )
        )
    return tuple(output)


def serialize_episode(domain: InteractionDomain) -> tuple[RawEvent, ...]:
    """Serialize without including domain.name or any task/domain identifier."""

    records: list[str] = ["RESET"]
    records.extend(
        f"EDGE {left} {right}"
        for left, right in sorted(set(domain.passive_edges))
    )
    records.extend(
        f"STEP {source} {target}"
        for source, target in domain.active_transitions
    )
    return tuple(records)


def singleton_segmentation_absorption(
    events: Sequence[RawEvent],
) -> SegmentationAbsorptionProfile:
    """A fake model: each STEP becomes its own segment and one-entry adapter."""

    active_count = sum(raw.strip().startswith("STEP ") for raw in events)
    if active_count == 0:
        raise ValueError("the stream needs active transitions")
    return SegmentationAbsorptionProfile(
        active_transition_count=active_count,
        shared_core_entries=1,
        segmenter_entries=1,
        adapter_entries=active_count,
        training_accuracy=1.0,
    )


def future_looking_boundary_control(
    left_world_event: str,
    right_world_event: str,
) -> dict[str, object]:
    """A target-dependent boundary key is unavailable before the successor."""

    left = left_world_event.split()
    right = right_world_event.split()
    if (
        len(left) != 3
        or len(right) != 3
        or left[0] != "STEP"
        or right[0] != "STEP"
    ):
        raise ValueError("controls require STEP source target events")
    causal_left = tuple(left[:2])
    causal_right = tuple(right[:2])
    future_left = tuple(left)
    future_right = tuple(right)
    return {
        "causal_prefix_equal": causal_left == causal_right,
        "future_boundary_keys_differ": future_left != future_right,
        "future_successors_used": int(left[2] != right[2]),
        "certified": False,
    }


def merge_episodes_ignoring_resets(
    events: Sequence[RawEvent],
) -> InteractionDomain:
    edges: list[Edge] = []
    active: list[Transition] = []
    for raw in events:
        line = raw.strip()
        if not line or line in {"RESET", "FREEZE"}:
            continue
        opcode, left, right = line.split()
        if opcode == "EDGE":
            edges.append(normalize_edge(left, right))
        elif opcode == "STEP":
            active.append((left, right))
        else:
            raise ValueError(f"unsupported event opcode: {opcode}")
    states = sorted(
        {node for edge in edges for node in edge}
        | {node for transition in active for node in transition}
    )
    return InteractionDomain(
        name="merged-without-causal-boundaries",
        states=tuple(states),
        passive_edges=tuple(sorted(set(edges))),
        active_transitions=tuple(active),
    )


def no_reset_control(events: Sequence[RawEvent]) -> dict[str, object]:
    merged = merge_episodes_ignoring_resets(events)
    try:
        candidates = consistent_orientations(merged)
    except ValueError:
        return {
            "status": "contradiction",
            "candidate_count": 0,
            "causal_reset_required": True,
        }
    return {
        "status": "ambiguous" if len(candidates) != 1 else "accidentally-identified",
        "candidate_count": len(candidates),
        "causal_reset_required": len(candidates) != 1,
    }


def control_resource_profile(
    training_sizes: Sequence[int],
    heldout_size: int,
    heldout_grounded_interactions: int,
    episode_count: int,
) -> ControlResourceProfile:
    separate = sum(training_sizes) + heldout_size
    shared = 1 + episode_count + 1
    return ControlResourceProfile(
        separate_control_entries=separate,
        shared_control_entries=shared,
        separate_active_interactions=separate,
        shared_active_interactions=(
            sum(training_sizes) + heldout_grounded_interactions
        ),
        heldout_interaction_savings=(
            heldout_size - heldout_grounded_interactions
        ),
    )


def run_experiment() -> dict[str, object]:
    alpha, _ = cycle_fixture(
        "not-serialized",
        ("amber", "birch", "cedar", "dune", "ember"),
        orientation_index=0,
    )
    beta, _ = cycle_fixture(
        "also-hidden",
        ("q7", "m2", "z9", "a4", "t1", "k8", "c3"),
        orientation_index=1,
    )
    gamma_full, gamma_truth = cycle_fixture(
        "heldout-name-never-emitted",
        (
            "north",
            "violet",
            "copper",
            "echo",
            "jade",
            "lima",
            "orbit",
            "piano",
            "quartz",
        ),
        orientation_index=1,
    )
    gamma_truth_map = dict(gamma_truth)
    anchor_source = gamma_full.states[0]
    gamma_one = InteractionDomain(
        name=gamma_full.name,
        states=gamma_full.states,
        passive_edges=gamma_full.passive_edges,
        active_transitions=((anchor_source, gamma_truth_map[anchor_source]),),
    )
    gamma_zero = InteractionDomain(
        name=gamma_full.name,
        states=gamma_full.states,
        passive_edges=gamma_full.passive_edges,
        active_transitions=(),
    )
    unsupported = path_fixture(
        "not-emitted",
        ("p0", "p1", "p2", "p3", "p4"),
    )

    stream = (
        serialize_episode(alpha)
        + serialize_episode(beta)
        + ("FREEZE",)
        + serialize_episode(gamma_one)
        + serialize_episode(unsupported)
    )
    parsed = parse_mixed_stream(stream)
    certificate = certify_mixed_stream(parsed)
    heldout = evaluate_heldout(
        parsed,
        certificate,
        (gamma_truth, ()),
    )

    zero_stream = (
        serialize_episode(alpha)
        + serialize_episode(beta)
        + ("FREEZE",)
        + serialize_episode(gamma_zero)
    )
    zero_parsed = parse_mixed_stream(zero_stream)
    zero_certificate = certify_mixed_stream(zero_parsed)
    zero_result = evaluate_heldout(
        zero_parsed,
        zero_certificate,
        (gamma_truth,),
    )[0]

    same_states = ("s0", "s1", "s2", "s3", "s4")
    opposite_a, _ = cycle_fixture(
        "hidden-a",
        same_states,
        orientation_index=0,
    )
    opposite_b, _ = cycle_fixture(
        "hidden-b",
        same_states,
        orientation_index=1,
    )
    no_reset = no_reset_control(
        serialize_episode(opposite_a) + serialize_episode(opposite_b)
    )

    absorption = singleton_segmentation_absorption(stream)
    future_control = future_looking_boundary_control(
        "STEP shared left",
        "STEP shared right",
    )
    resources = control_resource_profile(
        training_sizes=(len(alpha.states), len(beta.states)),
        heldout_size=len(gamma_full.states),
        heldout_grounded_interactions=1,
        episode_count=3,
    )

    transferred = heldout[0]
    rejected = heldout[1]
    result = {
        "capability_id": "CAP-GEN-003-MSO-001",
        "purpose": (
            "remove supplied domain labels from one mixed stream while "
            "requiring prospective operational reuse rather than post-hoc "
            "segmentation"
        ),
        "stream": {
            "event_count": len(stream),
            "training_episode_count": len(parsed.training_episodes),
            "heldout_episode_count": len(parsed.heldout_episodes),
            "reset_count": parsed.reset_count,
            "freeze_count": parsed.freeze_count,
            "domain_label_tokens_used": certificate.domain_label_tokens_used,
            "parser": certificate.parser_name,
        },
        "positive_transfer": {
            "status": transferred.status,
            "exact_accuracy": transferred.exact_accuracy,
            "predictions": transferred.predictions,
            "grounded_interactions": transferred.grounded_interactions,
            "zero_anchor_status": zero_result.status,
            "zero_anchor_candidates": zero_result.candidate_count,
            "unsupported_status": rejected.status,
        },
        "segmentation_absorption": {
            "active_transition_count": absorption.active_transition_count,
            "training_accuracy": absorption.training_accuracy,
            "core_only_reduction": absorption.core_only_reduction,
            "fully_charged_entries": absorption.fully_charged_entries,
            "fully_charged_reduction": absorption.fully_charged_reduction,
        },
        "causal_boundary_control": future_control,
        "no_reset_control": no_reset,
        "resources": {
            "separate_control_entries": resources.separate_control_entries,
            "shared_control_entries": resources.shared_control_entries,
            "control_entry_reduction": resources.control_entry_reduction,
            "separate_active_interactions": resources.separate_active_interactions,
            "shared_active_interactions": resources.shared_active_interactions,
            "heldout_interaction_savings": resources.heldout_interaction_savings,
        },
        "passed": (
            certificate.domain_label_tokens_used == 0
            and transferred.status == "transferred"
            and transferred.exact_accuracy == 1.0
            and transferred.predictions == 9
            and transferred.grounded_interactions == 1
            and zero_result.status == "abstain"
            and zero_result.candidate_count == 2
            and rejected.status == "unsupported"
            and absorption.core_only_reduction > 10.0
            and absorption.fully_charged_reduction < 1.0
            and future_control["causal_prefix_equal"] is True
            and future_control["future_boundary_keys_differ"] is True
            and no_reset["status"] == "contradiction"
            and resources.heldout_interaction_savings == 8
            and resources.control_entry_reduction == 4.2
        ),
        "claim_boundary": (
            "Task inference, task-free continual learning, switching "
            "dynamical systems, change-point detection, graph homomorphisms, "
            "and MDL segmentation are prior art. MSO-001 is a project bridge "
            "gate with typed RESET/EDGE/STEP events and a supplied cycle "
            "hypothesis language. It is not raw natural-language learning, "
            "a public-data result, multi-family induction, or human-level "
            "intelligence."
        ),
    }
    return result


def main() -> None:
    print(json.dumps(run_experiment(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
