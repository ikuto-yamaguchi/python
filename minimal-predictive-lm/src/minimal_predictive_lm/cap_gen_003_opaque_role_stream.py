from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .cap_gen_003_opaque_role_core import (
    OpaqueRecord,
    Pair,
    RoleInterpretation,
    cycle_orders,
    evaluate_assignment,
    exact_accuracy,
    infer_role_interpretations,
    transition_table,
)


@dataclass(frozen=True)
class OpaqueSegment:
    ordinal: int
    start_index: int
    end_index: int
    records: tuple[OpaqueRecord, ...]
    interpretations: tuple[RoleInterpretation, ...]


@dataclass(frozen=True)
class BoundaryProposal:
    event_index: int
    previous_segment_ordinal: int
    causal: bool
    reason: str


@dataclass(frozen=True)
class ParsedOpaqueStream:
    segments: tuple[OpaqueSegment, ...]
    proposals: tuple[BoundaryProposal, ...]
    reset_tokens_used: int
    semantic_role_tokens_used: int
    domain_label_tokens_used: int


@dataclass(frozen=True)
class SharedOperatorCertificate:
    operator_name: str
    structural_family: str
    training_segment_count: int
    role_adapter_count: int
    orientation_adapter_count: int


@dataclass(frozen=True)
class TransferResult:
    status: str
    predictions: tuple[Pair, ...]
    exact_accuracy: float
    interpretation_count: int
    orientation_candidate_count: int
    grounded_interactions: int
    future_successors_used: int
    reason: str


def interpretation_is_training_certified(
    interpretation: RoleInterpretation,
) -> bool:
    if not interpretation.complete_topology or not interpretation.unique_orientation:
        return False
    nodes = set()
    for left, right in interpretation.topology_pairs:
        nodes.add(left)
        nodes.add(right)
    action_sources = {source for source, _ in interpretation.action_pairs}
    return action_sources == nodes


def segment_has_unique_training_interpretation(segment: OpaqueSegment) -> bool:
    return (
        len(segment.interpretations) == 1
        and interpretation_is_training_certified(segment.interpretations[0])
    )


def segment_ready_for_boundary(segment: OpaqueSegment) -> bool:
    return any(
        interpretation.complete_topology
        and interpretation.unique_orientation
        and len(interpretation.action_pairs) >= 1
        for interpretation in segment.interpretations
    )


def make_segment(
    ordinal: int,
    start_index: int,
    end_index: int,
    records: Sequence[OpaqueRecord],
) -> OpaqueSegment:
    frozen = tuple(records)
    return OpaqueSegment(
        ordinal=ordinal,
        start_index=start_index,
        end_index=end_index,
        records=frozen,
        interpretations=infer_role_interpretations(frozen),
    )


def parse_opaque_stream(records: Sequence[OpaqueRecord]) -> ParsedOpaqueStream:
    segments: list[OpaqueSegment] = []
    proposals: list[BoundaryProposal] = []
    current: list[OpaqueRecord] = []
    start_index = 0

    for index, record in enumerate(records):
        trial = current + [record]
        interpretations = infer_role_interpretations(trial)
        if interpretations:
            current = trial
            continue

        previous = make_segment(len(segments), start_index, index, current)
        if not current or not segment_ready_for_boundary(previous):
            raise ValueError(
                "all role interpretations failed before the context was certifiable"
            )
        proposals.append(
            BoundaryProposal(
                event_index=index,
                previous_segment_ordinal=previous.ordinal,
                causal=True,
                reason=(
                    "the current opaque record has zero support under every "
                    "retained role interpretation"
                ),
            )
        )
        segments.append(previous)
        current = [record]
        start_index = index
        if not infer_role_interpretations(current):
            raise ValueError("a new context cannot start from this record")

    if current:
        segments.append(
            make_segment(
                len(segments),
                start_index,
                len(records),
                current,
            )
        )

    return ParsedOpaqueStream(
        segments=tuple(segments),
        proposals=tuple(proposals),
        reset_tokens_used=0,
        semantic_role_tokens_used=0,
        domain_label_tokens_used=0,
    )


def learn_shared_operator(
    training_segments: Sequence[OpaqueSegment],
) -> SharedOperatorCertificate:
    if len(training_segments) < 2:
        raise ValueError("at least two training contexts are required")
    if not all(
        segment_has_unique_training_interpretation(segment)
        for segment in training_segments
    ):
        raise ValueError(
            "every training context must identify local roles and orientation"
        )
    return SharedOperatorCertificate(
        operator_name="oriented-cycle-successor",
        structural_family="connected-degree-two-cycle",
        training_segment_count=len(training_segments),
        role_adapter_count=len(training_segments),
        orientation_adapter_count=len(training_segments),
    )


def transfer_to_segment(
    certificate: SharedOperatorCertificate,
    segment: OpaqueSegment,
    truth: Iterable[Pair],
) -> TransferResult:
    if certificate.structural_family != "connected-degree-two-cycle":
        raise ValueError("unsupported certificate family")
    usable = [
        interpretation
        for interpretation in segment.interpretations
        if interpretation.complete_topology
    ]
    if not usable:
        return TransferResult(
            "unsupported", (), 0.0, len(segment.interpretations), 0, 0, 0,
            "no retained role interpretation supplies the certified topology",
        )
    prospective: list[tuple[RoleInterpretation, int]] = []
    for interpretation in usable:
        for orientation in interpretation.orientation_candidates or (0, 1):
            if not interpretation.action_pairs:
                prospective.append((interpretation, orientation))
            elif orientation in interpretation.orientation_candidates:
                prospective.append((interpretation, orientation))
    if not prospective:
        return TransferResult(
            "contradiction", (), 0.0, len(usable), 0,
            sum(len(item.action_pairs) for item in usable), 0,
            "every retained role interpretation contradicts the operator",
        )
    prediction_tables = {
        transition_table(cycle_orders(item.topology_pairs)[orientation])
        for item, orientation in prospective
    }
    if len(prediction_tables) != 1:
        return TransferResult(
            "abstain", (), 0.0, len(usable), len(prospective),
            max((len(item.action_pairs) for item in usable), default=0), 0,
            "role or orientation ambiguity changes prospective predictions",
        )
    predictions = next(iter(prediction_tables))
    grounded = max((len(item.action_pairs) for item in usable), default=0)
    return TransferResult(
        "transferred", predictions, exact_accuracy(predictions, truth),
        len(usable), 1, grounded, 0,
        "one local role interpretation and orientation determine all predictions",
    )


def surface_copy_baseline(
    source_segment: OpaqueSegment,
    target_segment: OpaqueSegment,
) -> str:
    if len(source_segment.interpretations) != 1:
        return "unavailable"
    source = source_segment.interpretations[0]
    copied = evaluate_assignment(
        target_segment.records,
        source.topology_tag,
        source.action_tag,
    )
    if not copied.valid:
        return "contradiction"
    if not copied.complete_topology:
        return "unsupported"
    return "accepted"
