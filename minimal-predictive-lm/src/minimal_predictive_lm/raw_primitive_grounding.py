from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import json
import re
from typing import Iterable, Protocol

from .primitive_invention import (
    AffineCharacterPrimitive,
    StringPrimitive,
)


def _description_bits(payload: object) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ) * 8


@dataclass(frozen=True)
class RawResidualObservation:
    identifier: str
    channel: str
    text: str


@dataclass(frozen=True)
class ExtractedSpan:
    value: str
    start: int
    end: int
    delimiter: str


@dataclass(frozen=True)
class RawPairEvidence:
    observation_id: str
    channel: str
    source: str
    target: str
    source_index: int
    target_index: int
    changed_characters: int
    offset: int


@dataclass(frozen=True)
class PrimitiveCluster:
    identifier: str
    primitive: AffineCharacterPrimitive
    evidence: tuple[RawPairEvidence, ...]
    support_observations: tuple[str, ...]
    support_channels: tuple[str, ...]
    false_matching_pairs: int
    normalized_gain_bits: int

    @property
    def description_bits(self) -> int:
        return self.primitive.description_bits


class ContextAwareStringPrimitive(Protocol):
    kind: str

    def apply(self, value: str) -> str:
        ...

    def render(self) -> object:
        ...

    @property
    def description_bits(self) -> int:
        ...


_QUOTED_PATTERNS = (
    ("double_quote", re.compile(r'"((?:\\.|[^"\\])*)"')),
    ("single_quote", re.compile(r"'((?:\\.|[^'\\])*)'")),
    ("backtick", re.compile(r"`([^`]*)`")),
    ("japanese_quote", re.compile(r"「([^」]*)」")),
)


def extract_raw_spans(text: str) -> tuple[ExtractedSpan, ...]:
    rows: list[ExtractedSpan] = []
    for delimiter, pattern in _QUOTED_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(1)
            if not value:
                continue
            rows.append(
                ExtractedSpan(
                    value=value,
                    start=match.start(1),
                    end=match.end(1),
                    delimiter=delimiter,
                )
            )
    rows.sort(key=lambda row: (row.start, row.end, row.delimiter))
    unique: list[ExtractedSpan] = []
    seen: set[tuple[int, int, str]] = set()
    for row in rows:
        key = (row.start, row.end, row.value)
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return tuple(unique)


def ordered_span_pairs(
    observation: RawResidualObservation,
    *,
    maximum_length: int = 256,
) -> tuple[tuple[int, int, str, str], ...]:
    spans = extract_raw_spans(observation.text)
    rows: list[tuple[int, int, str, str]] = []
    for left_index, left in enumerate(spans):
        for right_index in range(left_index + 1, len(spans)):
            right = spans[right_index]
            if max(len(left.value), len(right.value)) > maximum_length:
                continue
            rows.append((left_index, right_index, left.value, right.value))
    return tuple(rows)


def _offset_evidence(
    observation: RawResidualObservation,
    left_index: int,
    right_index: int,
    source: str,
    target: str,
    *,
    minimum_changed_characters: int,
) -> RawPairEvidence | None:
    if len(source) != len(target) or source == target:
        return None
    changed = [
        (ord(left), ord(right))
        for left, right in zip(source, target)
        if left != right
    ]
    if len(changed) < minimum_changed_characters:
        return None
    offsets = {right - left for left, right in changed}
    if len(offsets) != 1:
        return None
    return RawPairEvidence(
        observation_id=observation.identifier,
        channel=observation.channel,
        source=source,
        target=target,
        source_index=left_index,
        target_index=right_index,
        changed_characters=len(changed),
        offset=next(iter(offsets)),
    )


def infer_offset_evidence(
    observations: Iterable[RawResidualObservation],
    *,
    minimum_changed_characters: int = 2,
) -> tuple[RawPairEvidence, ...]:
    rows: list[RawPairEvidence] = []
    for observation in observations:
        for left_index, right_index, source, target in ordered_span_pairs(observation):
            evidence = _offset_evidence(
                observation,
                left_index,
                right_index,
                source,
                target,
                minimum_changed_characters=minimum_changed_characters,
            )
            if evidence is not None:
                rows.append(evidence)
    return tuple(rows)


def _primitive_matches_pair(
    primitive: ContextAwareStringPrimitive,
    source: str,
    target: str,
    *,
    context: str = "",
) -> bool:
    return apply_contextual_primitive(primitive, source, context=context) == target


def induce_raw_primitive_clusters(
    observations: Iterable[RawResidualObservation],
    *,
    minimum_support_observations: int = 3,
    minimum_support_channels: int = 2,
    evidence_value_bits: int = 256,
    false_match_cost_bits: int = 128,
) -> tuple[PrimitiveCluster, ...]:
    items = tuple(observations)
    evidence = infer_offset_evidence(items)
    grouped: dict[int, list[RawPairEvidence]] = {}
    for row in evidence:
        grouped.setdefault(row.offset, []).append(row)

    candidates: list[PrimitiveCluster] = []
    all_pairs = tuple(
        (observation.identifier, source, target)
        for observation in items
        for _, _, source, target in ordered_span_pairs(observation)
    )
    for offset, rows in grouped.items():
        best_by_observation: dict[str, RawPairEvidence] = {}
        for row in rows:
            incumbent = best_by_observation.get(row.observation_id)
            if incumbent is None or row.changed_characters > incumbent.changed_characters:
                best_by_observation[row.observation_id] = row
        selected_rows = tuple(best_by_observation.values())
        channels = tuple(sorted({row.channel for row in selected_rows}))
        if (
            len(selected_rows) < minimum_support_observations
            or len(channels) < minimum_support_channels
        ):
            continue

        changed_sources = [
            ord(left)
            for row in selected_rows
            for left, right in zip(row.source, row.target)
            if left != right
        ]
        primitive = AffineCharacterPrimitive(
            min(changed_sources),
            max(changed_sources),
            offset,
        )
        covered = tuple(
            row
            for row in selected_rows
            if primitive.apply(row.source) == row.target
        )
        if len(covered) < minimum_support_observations:
            continue
        covered_ids = {row.observation_id for row in covered}
        false_matches = sum(
            1
            for observation_id, source, target in all_pairs
            if observation_id not in covered_ids
            and primitive.apply(source) == target
        )
        gain = (
            len(covered) * evidence_value_bits
            - primitive.description_bits
            - false_matches * false_match_cost_bits
        )
        candidates.append(
            PrimitiveCluster(
                identifier="",
                primitive=primitive,
                evidence=covered,
                support_observations=tuple(
                    sorted(row.observation_id for row in covered)
                ),
                support_channels=channels,
                false_matching_pairs=false_matches,
                normalized_gain_bits=gain,
            )
        )

    candidates.sort(
        key=lambda row: (
            -row.normalized_gain_bits,
            -len(row.support_observations),
            row.primitive.description_bits,
            row.primitive.offset,
        )
    )
    assigned: set[str] = set()
    selected: list[PrimitiveCluster] = []
    for row in candidates:
        remaining = tuple(
            evidence_row
            for evidence_row in row.evidence
            if evidence_row.observation_id not in assigned
        )
        channels = tuple(sorted({evidence_row.channel for evidence_row in remaining}))
        if (
            len(remaining) < minimum_support_observations
            or len(channels) < minimum_support_channels
        ):
            continue
        identifier = f"P{len(selected)}"
        selected.append(
            PrimitiveCluster(
                identifier=identifier,
                primitive=row.primitive,
                evidence=remaining,
                support_observations=tuple(
                    sorted(evidence_row.observation_id for evidence_row in remaining)
                ),
                support_channels=channels,
                false_matching_pairs=row.false_matching_pairs,
                normalized_gain_bits=row.normalized_gain_bits,
            )
        )
        assigned.update(evidence_row.observation_id for evidence_row in remaining)
    return tuple(selected)


def extract_best_pair(
    observation: RawResidualObservation,
    primitive: ContextAwareStringPrimitive | None = None,
) -> tuple[str, str] | None:
    pairs = ordered_span_pairs(observation)
    if not pairs:
        return None
    if primitive is not None:
        exact = [
            (source, target)
            for _, _, source, target in pairs
            if _primitive_matches_pair(
                primitive,
                source,
                target,
                context=observation.text,
            )
        ]
        if exact:
            return max(
                exact,
                key=lambda pair: (
                    sum(left != right for left, right in zip(pair[0], pair[1])),
                    len(pair[0]),
                ),
            )
    return max(
        ((source, target) for _, _, source, target in pairs),
        key=lambda pair: (
            SequenceMatcher(None, pair[0], pair[1]).ratio(),
            min(len(pair[0]), len(pair[1])),
        ),
    )


@dataclass(frozen=True)
class ReplacementCompositePrimitive:
    base: ContextAwareStringPrimitive
    replacements: tuple[tuple[str, str], ...]
    kind: str = "base_with_residual_replacements"

    def apply(self, value: str) -> str:
        output = self.base.apply(value)
        for source, target in sorted(
            self.replacements,
            key=lambda row: (-len(row[0]), row[0], row[1]),
        ):
            output = output.replace(source, target)
        return output

    def render(self) -> object:
        return {
            "kind": self.kind,
            "base": self.base.render(),
            "replacements": [list(row) for row in self.replacements],
        }

    @property
    def description_bits(self) -> int:
        return _description_bits(self.render())


@dataclass(frozen=True)
class IdentityPrimitive:
    kind: str = "identity"

    def apply(self, value: str) -> str:
        return value

    def render(self) -> object:
        return {"kind": self.kind}

    @property
    def description_bits(self) -> int:
        return _description_bits(self.render())


@dataclass(frozen=True)
class ContextualBypassPrimitive:
    base: ContextAwareStringPrimitive
    bypass_token: str
    kind: str = "contextual_bypass"

    def apply(self, value: str) -> str:
        return self.base.apply(value)

    def apply_with_context(self, value: str, context: str) -> str:
        if self.bypass_token.casefold() in context.casefold():
            return value
        return self.base.apply(value)

    def render(self) -> object:
        return {
            "kind": self.kind,
            "bypass_token": self.bypass_token,
            "base": self.base.render(),
        }

    @property
    def description_bits(self) -> int:
        return _description_bits(self.render())


def apply_contextual_primitive(
    primitive: ContextAwareStringPrimitive,
    value: str,
    *,
    context: str = "",
) -> str:
    contextual = getattr(primitive, "apply_with_context", None)
    if contextual is not None:
        return contextual(value, context)
    return primitive.apply(value)


def raw_primitive_accuracy(
    primitive: ContextAwareStringPrimitive,
    observations: Iterable[RawResidualObservation],
) -> float:
    items = tuple(observations)
    if not items:
        raise ValueError("at least one observation is required")
    correct = 0
    measured = 0
    for observation in items:
        pair = extract_best_pair(observation)
        if pair is None:
            continue
        measured += 1
        source, target = pair
        correct += int(
            apply_contextual_primitive(
                primitive,
                source,
                context=observation.text,
            )
            == target
        )
    if measured == 0:
        raise ValueError("no candidate source/target pairs were extracted")
    return correct / measured


def propose_residual_extension(
    base: ContextAwareStringPrimitive,
    observations: Iterable[RawResidualObservation],
) -> ReplacementCompositePrimitive:
    replacements: dict[str, str] = {}
    for observation in observations:
        pair = extract_best_pair(observation)
        if pair is None:
            continue
        source, target = pair
        baseline = apply_contextual_primitive(base, source, context=observation.text)
        matcher = SequenceMatcher(None, baseline, target)
        for tag, left_start, left_end, right_start, right_end in matcher.get_opcodes():
            if tag == "equal":
                continue
            old = baseline[left_start:left_end]
            new = target[right_start:right_end]
            if not old or old == new:
                continue
            previous = replacements.get(old)
            if previous is not None and previous != new:
                raise ValueError("residual replacement is inconsistent")
            replacements[old] = new
    if not replacements:
        raise ValueError("no reusable residual replacement was found")
    return ReplacementCompositePrimitive(base, tuple(sorted(replacements.items())))


_TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_-]{2,}")
_CONTEXT_STOPWORDS = frozenset(
    {
        "input",
        "output",
        "source",
        "target",
        "result",
        "status",
        "pass",
        "expected",
        "actual",
        "tool",
        "test",
        "case",
        "label",
    }
)


def _context_tokens(observation: RawResidualObservation) -> set[str]:
    text = observation.text
    for span in reversed(extract_raw_spans(text)):
        text = text[: span.start] + " " * (span.end - span.start) + text[span.end :]
    return {
        token.casefold()
        for token in _TOKEN_PATTERN.findall(text)
        if token.casefold() not in _CONTEXT_STOPWORDS
    }


def learn_bypass_token(
    successful_observations: Iterable[RawResidualObservation],
    conflicting_observations: Iterable[RawResidualObservation],
) -> str:
    successes = tuple(successful_observations)
    conflicts = tuple(conflicting_observations)
    if not conflicts:
        raise ValueError("at least one conflicting observation is required")
    common = set.intersection(*(_context_tokens(row) for row in conflicts))
    seen_in_success = (
        set().union(*(_context_tokens(row) for row in successes)) if successes else set()
    )
    candidates = sorted(common - seen_in_success, key=lambda token: (len(token), token))
    if not candidates:
        raise ValueError("no context token separates conflicts from successes")
    return candidates[0]


@dataclass(frozen=True)
class PrimitiveVersion:
    version: int
    primitive: ContextAwareStringPrimitive
    parent_version: int | None
    reason: str
    evidence_ids: tuple[str, ...]

    @property
    def description_bits(self) -> int:
        return self.primitive.description_bits


@dataclass(frozen=True)
class PrimitiveVersionDecision:
    accepted: bool
    rolled_back: bool
    old_accuracy: float
    new_accuracy: float
    candidate_bits: int
    migration_bits: int
    expected_future_calls: int
    normalized_lifetime_gain_bits: int
    active_version: int


class VersionedPrimitiveLibrary:
    def __init__(self, primitive: ContextAwareStringPrimitive, *, reason: str) -> None:
        self._versions: list[PrimitiveVersion] = [
            PrimitiveVersion(1, primitive, None, reason, ())
        ]
        self._active_version = 1
        self._rejected: list[PrimitiveVersionDecision] = []

    @property
    def versions(self) -> tuple[PrimitiveVersion, ...]:
        return tuple(self._versions)

    @property
    def active(self) -> PrimitiveVersion:
        return next(row for row in self._versions if row.version == self._active_version)

    @property
    def rejected_decisions(self) -> tuple[PrimitiveVersionDecision, ...]:
        return tuple(self._rejected)

    def stage(
        self,
        candidate: ContextAwareStringPrimitive,
        evidence: Iterable[RawResidualObservation],
        *,
        reason: str,
        expected_future_calls: int,
        error_cost_bits: int = 64,
        migration_bits: int = 128,
        minimum_accuracy: float = 1.0,
    ) -> PrimitiveVersionDecision:
        items = tuple(evidence)
        old_accuracy = raw_primitive_accuracy(self.active.primitive, items)
        new_accuracy = raw_primitive_accuracy(candidate, items)
        additional_bits = max(0, candidate.description_bits - self.active.description_bits)
        benefit = round(
            expected_future_calls
            * max(0.0, new_accuracy - old_accuracy)
            * error_cost_bits
        )
        gain = benefit - additional_bits - migration_bits
        accepted = (
            new_accuracy >= minimum_accuracy
            and new_accuracy >= old_accuracy
            and gain > 0
        )
        rolled_back = not accepted
        if accepted:
            version = self._versions[-1].version + 1
            self._versions.append(
                PrimitiveVersion(
                    version,
                    candidate,
                    self.active.version,
                    reason,
                    tuple(row.identifier for row in items),
                )
            )
            self._active_version = version
        decision = PrimitiveVersionDecision(
            accepted=accepted,
            rolled_back=rolled_back,
            old_accuracy=old_accuracy,
            new_accuracy=new_accuracy,
            candidate_bits=candidate.description_bits,
            migration_bits=migration_bits,
            expected_future_calls=expected_future_calls,
            normalized_lifetime_gain_bits=gain,
            active_version=self._active_version,
        )
        if rolled_back:
            self._rejected.append(decision)
        return decision
