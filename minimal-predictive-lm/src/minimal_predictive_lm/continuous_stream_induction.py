from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Iterable

from .primitive_invention import AffineCharacterPrimitive


def _description_bits(payload: object) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ) * 8


_BOUNDARY_PATTERN = re.compile(r"(?:\r?\n+|[。.!?！？;；]+)")
_ASCII_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
_SUCCESS_CUES = (
    "pass",
    "passed",
    "success",
    "succeeded",
    "ok",
    "成功",
    "合格",
    "正常",
)
_FAILURE_CUES = (
    "fail",
    "failed",
    "failure",
    "error",
    "失敗",
    "不合格",
    "異常",
)
_CONDITION_CUES = ("if", "when", "unless", "もし", "なら", "場合", "とき")
_PROVENANCE_PATTERN = re.compile(
    r"(?:source|origin|evidence|根拠|出典|由来)\s*[:=]?\s*([A-Za-z0-9_-]+)",
    re.IGNORECASE,
)
_ROLE_STOPWORDS = frozenset(
    {
        "and",
        "then",
        "test",
        "check",
        "status",
        "validation",
        "source",
        "origin",
        "evidence",
        "pass",
        "passed",
        "success",
        "succeeded",
        "ok",
        "fail",
        "failed",
        "failure",
        "error",
        "became",
        "changed",
        "into",
        "from",
        "to",
        "input",
        "output",
        "retry",
        "rollback",
    }
)


@dataclass(frozen=True)
class StreamSegment:
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class InferredStreamEvent:
    start: int
    end: int
    source: str
    target: str
    result: str
    has_condition: bool
    provenance: str | None
    offset: int
    changed_characters: int
    local_score: int

    def render(self) -> object:
        return {
            "start": self.start,
            "end": self.end,
            "source": self.source,
            "target": self.target,
            "result": self.result,
            "has_condition": self.has_condition,
            "provenance": self.provenance,
            "offset": self.offset,
            "changed_characters": self.changed_characters,
        }


@dataclass(frozen=True)
class StreamPrimitiveCluster:
    identifier: str
    primitive: AffineCharacterPrimitive
    event_indices: tuple[int, ...]
    support_events: int
    normalized_gain_bits: int

    @property
    def description_bits(self) -> int:
        return self.primitive.description_bits


@dataclass(frozen=True)
class StreamInference:
    events: tuple[InferredStreamEvent, ...]
    clusters: tuple[StreamPrimitiveCluster, ...]
    candidate_pair_evaluations: int
    stream_bits: int
    representation_bits: int


def split_continuous_stream(text: str) -> tuple[StreamSegment, ...]:
    rows: list[StreamSegment] = []
    cursor = 0
    for match in _BOUNDARY_PATTERN.finditer(text):
        if match.start() > cursor:
            left = cursor
            right = match.start()
            while left < right and text[left].isspace():
                left += 1
            while right > left and text[right - 1].isspace():
                right -= 1
            if left < right:
                rows.append(StreamSegment(text[left:right], left, right))
        cursor = match.end()
    if cursor < len(text):
        left = cursor
        right = len(text)
        while left < right and text[left].isspace():
            left += 1
        while right > left and text[right - 1].isspace():
            right -= 1
        if left < right:
            rows.append(StreamSegment(text[left:right], left, right))
    return tuple(rows)


def _constant_offset(source: str, target: str) -> tuple[int, int] | None:
    if len(source) != len(target) or source == target:
        return None
    changed = [
        ord(right) - ord(left)
        for left, right in zip(source, target)
        if left != right
    ]
    if len(changed) < 2 or len(set(changed)) != 1:
        return None
    return changed[0], len(changed)


def _infer_result(segment: str) -> str:
    folded = segment.casefold()
    if any(cue in folded for cue in _FAILURE_CUES):
        return "failure"
    if any(cue in folded for cue in _SUCCESS_CUES):
        return "success"
    return "unknown"


def _has_condition(segment: str) -> bool:
    folded = segment.casefold()
    return any(cue in folded for cue in _CONDITION_CUES)


def _infer_provenance(segment: str) -> str | None:
    match = _PROVENANCE_PATTERN.search(segment)
    return match.group(1) if match is not None else None


def infer_segment_event(
    segment: StreamSegment,
    *,
    maximum_token_gap: int = 7,
) -> tuple[InferredStreamEvent | None, int]:
    tokens = tuple(
        (match.group(), segment.start + match.start(), segment.start + match.end())
        for match in _ASCII_WORD.finditer(segment.text)
    )
    best: tuple[int, str, str, int, int] | None = None
    candidate_evaluations = 0
    for left_index, (source, _, _) in enumerate(tokens):
        if source.casefold() in _ROLE_STOPWORDS:
            continue
        for right_index in range(
            left_index + 1,
            min(len(tokens), left_index + maximum_token_gap + 1),
        ):
            target = tokens[right_index][0]
            if target.casefold() in _ROLE_STOPWORDS:
                continue
            candidate_evaluations += 1
            relation = _constant_offset(source, target)
            if relation is None:
                continue
            offset, changed = relation
            score = changed * 12 - (right_index - left_index)
            candidate = (score, source, target, offset, changed)
            if best is None or candidate > best:
                best = candidate
    if best is None:
        return None, candidate_evaluations
    score, source, target, offset, changed = best
    return (
        InferredStreamEvent(
            start=segment.start,
            end=segment.end,
            source=source,
            target=target,
            result=_infer_result(segment.text),
            has_condition=_has_condition(segment.text),
            provenance=_infer_provenance(segment.text),
            offset=offset,
            changed_characters=changed,
            local_score=score,
        ),
        candidate_evaluations,
    )


def induce_stream_clusters(
    events: Iterable[InferredStreamEvent],
    *,
    minimum_support_events: int = 2,
    evidence_value_bits: int = 384,
) -> tuple[StreamPrimitiveCluster, ...]:
    items = tuple(events)
    grouped: dict[int, list[tuple[int, InferredStreamEvent]]] = {}
    for index, event in enumerate(items):
        grouped.setdefault(event.offset, []).append((index, event))
    candidates: list[tuple[int, int, AffineCharacterPrimitive, tuple[int, ...]]] = []
    for offset, rows in grouped.items():
        if len(rows) < minimum_support_events:
            continue
        changed_sources = [
            ord(left)
            for _, event in rows
            for left, right in zip(event.source, event.target)
            if left != right
        ]
        primitive = AffineCharacterPrimitive(
            min(changed_sources),
            max(changed_sources),
            offset,
        )
        covered = tuple(
            index
            for index, event in rows
            if primitive.apply(event.source) == event.target
        )
        if len(covered) < minimum_support_events:
            continue
        gain = len(covered) * evidence_value_bits - primitive.description_bits
        candidates.append((gain, offset, primitive, covered))
    candidates.sort(key=lambda row: (-row[0], row[2].description_bits, row[1]))
    return tuple(
        StreamPrimitiveCluster(
            identifier=f"S{index}",
            primitive=primitive,
            event_indices=covered,
            support_events=len(covered),
            normalized_gain_bits=gain,
        )
        for index, (gain, _, primitive, covered) in enumerate(candidates)
        if gain > 0
    )


def infer_continuous_stream(text: str) -> StreamInference:
    events: list[InferredStreamEvent] = []
    candidate_evaluations = 0
    for segment in split_continuous_stream(text):
        event, evaluations = infer_segment_event(segment)
        candidate_evaluations += evaluations
        if event is not None:
            events.append(event)
    clusters = induce_stream_clusters(events)
    representation = {
        "events": [event.render() for event in events],
        "clusters": [
            {
                "id": cluster.identifier,
                "primitive": cluster.primitive.render(),
                "event_indices": list(cluster.event_indices),
            }
            for cluster in clusters
        ],
    }
    return StreamInference(
        events=tuple(events),
        clusters=clusters,
        candidate_pair_evaluations=candidate_evaluations,
        stream_bits=len(text.encode("utf-8")) * 8,
        representation_bits=_description_bits(representation),
    )


def event_signature(event: InferredStreamEvent) -> tuple[object, ...]:
    return (
        event.source,
        event.target,
        event.result,
        event.has_condition,
        event.provenance,
    )


def event_precision_recall(
    inferred: Iterable[InferredStreamEvent],
    expected: Iterable[tuple[object, ...]],
) -> tuple[float, float]:
    predicted = {event_signature(event) for event in inferred}
    gold = set(expected)
    overlap = len(predicted & gold)
    precision = overlap / len(predicted) if predicted else 0.0
    recall = overlap / len(gold) if gold else 0.0
    return precision, recall


def cluster_coverage(
    clusters: Iterable[StreamPrimitiveCluster],
    events: Iterable[InferredStreamEvent],
) -> float:
    items = tuple(events)
    if not items:
        return 0.0
    covered = {index for cluster in clusters for index in cluster.event_indices}
    return len(covered) / len(items)
