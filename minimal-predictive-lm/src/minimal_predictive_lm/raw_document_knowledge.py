from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json
import math
import re
from typing import Iterable, Mapping


@dataclass(frozen=True)
class RawDocument:
    document_id: str
    source: str
    topic: str
    year: int
    text: str
    copied_from: str | None = None


@dataclass(frozen=True)
class ContextObservation:
    source: str
    topic: str
    era: str
    correct: bool


@dataclass(frozen=True)
class ContextTrust:
    source: str
    topic: str
    era: str
    successes: int
    failures: int

    @property
    def reliability(self) -> float:
        return (self.successes + 1.0) / (
            self.successes + self.failures + 2.0
        )

    @property
    def weight(self) -> float:
        probability = min(
            1.0 - 1e-9,
            max(0.5 + 1e-9, self.reliability),
        )
        return math.log(probability / (1.0 - probability))


@dataclass(frozen=True)
class ExtractedClaim:
    subject: str
    relation: str
    value: str
    source: str
    provenance: str
    topic: str
    year: int
    origin: str
    span_start: int
    span_end: int


@dataclass(frozen=True)
class EvidenceUnit:
    origin: str
    value: str
    weight: float
    reliability: float
    provenance: tuple[str, ...]


@dataclass(frozen=True)
class RawKnowledgeAnswer:
    value: str | None
    confidence: float
    abstained: bool
    conflict: bool
    claim_reads: int
    available_claims: int
    independent_origins: int
    provenance: tuple[str, ...]


_PATTERNS = (
    re.compile(
        r"(?P<subject>[A-Za-z0-9_]+)の"
        r"(?P<relation>[A-Za-z0-9_]+)は"
        r"(?P<value>[A-Za-z0-9_]+)(?:です|である)?[。.]"
    ),
    re.compile(
        r"(?P<subject>[A-Za-z0-9_]+)'s\s+"
        r"(?P<relation>[A-Za-z0-9_]+)\s+is\s+"
        r"(?P<value>[A-Za-z0-9_]+)[.]?",
        re.IGNORECASE,
    ),
)


def era_for_year(year: int) -> str:
    return "recent" if year >= 2025 else "legacy"


def _resolve_origins(
    documents: Iterable[RawDocument],
) -> dict[str, str]:
    items = tuple(documents)
    by_id = {document.document_id: document for document in items}

    def root(document: RawDocument) -> str:
        current = document
        visited: set[str] = set()
        while current.copied_from is not None:
            if current.document_id in visited:
                raise ValueError("copy cycle")
            visited.add(current.document_id)
            parent = by_id.get(current.copied_from)
            if parent is None:
                raise ValueError(
                    f"missing copied_from document {current.copied_from!r}"
                )
            current = parent
        return current.document_id

    return {document.document_id: root(document) for document in items}


def extract_claims(
    documents: Iterable[RawDocument],
) -> tuple[ExtractedClaim, ...]:
    items = tuple(documents)
    origins = _resolve_origins(items)
    claims: list[ExtractedClaim] = []
    for document in items:
        matches = [
            match
            for pattern in _PATTERNS
            for match in pattern.finditer(document.text)
        ]
        matches.sort(key=lambda match: (match.start(), match.end()))
        for match in matches:
            claims.append(
                ExtractedClaim(
                    match.group("subject"),
                    match.group("relation"),
                    match.group("value").lower(),
                    document.source,
                    (
                        f"doc://{document.document_id}"
                        f"#{match.start()}-{match.end()}"
                    ),
                    document.topic,
                    document.year,
                    origins[document.document_id],
                    match.start(),
                    match.end(),
                )
            )
    return tuple(claims)


def learn_context_trust(
    observations: Iterable[ContextObservation],
) -> tuple[
    dict[tuple[str, str, str], ContextTrust],
    dict[str, ContextTrust],
]:
    contextual_counts: dict[tuple[str, str, str], list[int]] = {}
    global_counts: dict[str, list[int]] = {}
    for observation in observations:
        contextual_counts.setdefault(
            (observation.source, observation.topic, observation.era),
            [0, 0],
        )[0 if observation.correct else 1] += 1
        global_counts.setdefault(observation.source, [0, 0])[
            0 if observation.correct else 1
        ] += 1

    contextual = {
        key: ContextTrust(*key, successes, failures)
        for key, (successes, failures) in sorted(
            contextual_counts.items()
        )
    }
    global_trust = {
        source: ContextTrust(source, "*", "*", successes, failures)
        for source, (successes, failures) in sorted(
            global_counts.items()
        )
    }
    return contextual, global_trust


@dataclass(frozen=True)
class RawKnowledgeIndex:
    claims_by_key: Mapping[
        tuple[str, str],
        tuple[ExtractedClaim, ...],
    ]
    contextual_trust: Mapping[
        tuple[str, str, str],
        ContextTrust,
    ]
    global_trust: Mapping[str, ContextTrust]

    @property
    def description_bits(self) -> int:
        payload = {
            "contextual_trust": [
                {
                    "source": item.source,
                    "topic": item.topic,
                    "era": item.era,
                    "successes": item.successes,
                    "failures": item.failures,
                }
                for item in sorted(
                    self.contextual_trust.values(),
                    key=lambda item: (
                        item.source,
                        item.topic,
                        item.era,
                    ),
                )
            ],
            "claims": [
                {
                    "subject": claim.subject,
                    "relation": claim.relation,
                    "value": claim.value,
                    "source": claim.source,
                    "provenance": claim.provenance,
                    "topic": claim.topic,
                    "year": claim.year,
                    "origin": claim.origin,
                }
                for key in sorted(self.claims_by_key)
                for claim in self.claims_by_key[key]
            ],
        }
        return len(
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ) * 8

    def _trust(
        self,
        claim: ExtractedClaim,
        contextual: bool,
    ) -> ContextTrust:
        if contextual:
            key = (
                claim.source,
                claim.topic,
                era_for_year(claim.year),
            )
            if key in self.contextual_trust:
                return self.contextual_trust[key]
        return self.global_trust[claim.source]

    def _evidence_units(
        self,
        claims: Iterable[ExtractedClaim],
        *,
        contextual: bool,
        correlation_aware: bool,
    ) -> tuple[EvidenceUnit, ...]:
        claim_items = tuple(claims)
        grouped: dict[str, list[ExtractedClaim]] = defaultdict(list)
        if correlation_aware:
            for claim in claim_items:
                grouped[claim.origin].append(claim)
        else:
            for index, claim in enumerate(claim_items):
                grouped[
                    f"{claim.origin}:{index}:{claim.provenance}"
                ].append(claim)

        units: list[EvidenceUnit] = []
        for origin, items in grouped.items():
            best = max(
                items,
                key=lambda claim: (
                    self._trust(claim, contextual).weight,
                    claim.provenance,
                ),
            )
            trust = self._trust(best, contextual)
            units.append(
                EvidenceUnit(
                    origin,
                    best.value,
                    trust.weight,
                    trust.reliability,
                    tuple(
                        sorted(claim.provenance for claim in items)
                    ),
                )
            )
        return tuple(
            sorted(
                units,
                key=lambda item: (-item.weight, item.origin),
            )
        )

    def answer(
        self,
        subject: str,
        relation: str,
        *,
        confidence_threshold: float = 0.8,
        contextual: bool = True,
        correlation_aware: bool = True,
        adaptive_voi: bool = True,
        information_value: float = 16.0,
        read_cost: float = 1.0,
    ) -> RawKnowledgeAnswer:
        claims = self.claims_by_key.get((relation, subject), ())
        units = list(
            self._evidence_units(
                claims,
                contextual=contextual,
                correlation_aware=correlation_aware,
            )
        )
        if not units:
            return RawKnowledgeAnswer(
                None,
                0.0,
                True,
                False,
                0,
                0,
                0,
                (),
            )

        all_values = sorted({unit.value for unit in units})
        if len(all_values) == 1:
            unit = units[0]
            abstained = unit.reliability < confidence_threshold
            return RawKnowledgeAnswer(
                None if abstained else unit.value,
                unit.reliability,
                abstained,
                False,
                1,
                len(claims),
                len({item.origin for item in units}),
                unit.provenance,
            )
        if len(all_values) != 2:
            raise ValueError(
                "Phase 10e bounded VOI currently supports binary values"
            )

        scores: dict[str, float] = defaultdict(float)
        provenance: list[str] = []
        reads = 0
        values_seen: set[str] = set()

        while units:
            leader, confidence = _leader_confidence(
                scores,
                all_values,
            )
            if reads and adaptive_voi:
                opponent = (
                    all_values[0]
                    if leader == all_values[1]
                    else all_values[1]
                )
                margin = scores.get(leader, 0.0) - scores.get(
                    opponent,
                    0.0,
                )
                lower_confidence = _sigmoid(
                    margin - sum(unit.weight for unit in units)
                )
                if lower_confidence >= confidence_threshold:
                    return RawKnowledgeAnswer(
                        leader,
                        lower_confidence,
                        False,
                        len(values_seen) > 1,
                        reads,
                        len(claims),
                        len({item.origin for item in units})
                        + reads,
                        tuple(provenance),
                    )

            if adaptive_voi:
                candidates = [
                    (
                        _entropy_voi(
                            confidence,
                            unit.reliability,
                            information_value,
                            read_cost,
                        ),
                        unit.weight,
                        -index,
                        index,
                    )
                    for index, unit in enumerate(units)
                ]
                best_voi, _, _, selected = max(candidates)
                if best_voi <= 0.0 and reads:
                    return RawKnowledgeAnswer(
                        None,
                        confidence,
                        True,
                        len(values_seen) > 1,
                        reads,
                        len(claims),
                        len({item.origin for item in units})
                        + reads,
                        tuple(provenance),
                    )
            else:
                selected = 0

            unit = units.pop(selected)
            scores[unit.value] = (
                scores.get(unit.value, 0.0) + unit.weight
            )
            provenance.extend(unit.provenance)
            values_seen.add(unit.value)
            reads += 1

        leader, confidence = _leader_confidence(
            scores,
            all_values,
        )
        abstained = confidence < confidence_threshold
        return RawKnowledgeAnswer(
            None if abstained else leader,
            confidence,
            abstained,
            len(values_seen) > 1,
            reads,
            len(claims),
            reads,
            tuple(provenance),
        )


def _sigmoid(value: float) -> float:
    return 1.0 / (
        1.0 + math.exp(-max(-700.0, min(700.0, value)))
    )


def _leader_confidence(
    scores: Mapping[str, float],
    values: list[str],
) -> tuple[str, float]:
    difference = scores.get(values[0], 0.0) - scores.get(
        values[1],
        0.0,
    )
    probability = _sigmoid(difference)
    if probability >= 0.5:
        return values[0], probability
    return values[1], 1.0 - probability


def _binary_entropy(probability: float) -> float:
    if probability <= 0.0 or probability >= 1.0:
        return 0.0
    return -(
        probability * math.log2(probability)
        + (1.0 - probability)
        * math.log2(1.0 - probability)
    )


def _entropy_voi(
    current_probability: float,
    reliability: float,
    information_value: float,
    read_cost: float,
) -> float:
    positive_probability = (
        current_probability * reliability
        + (1.0 - current_probability)
        * (1.0 - reliability)
    )
    positive_posterior = (
        current_probability * reliability / positive_probability
        if positive_probability
        else current_probability
    )
    negative_probability = 1.0 - positive_probability
    negative_posterior = (
        current_probability
        * (1.0 - reliability)
        / negative_probability
        if negative_probability
        else current_probability
    )
    expected_entropy = (
        positive_probability
        * _binary_entropy(positive_posterior)
        + negative_probability
        * _binary_entropy(negative_posterior)
    )
    information_gain = (
        _binary_entropy(current_probability)
        - expected_entropy
    )
    return information_value * information_gain - read_cost


def build_raw_knowledge_index(
    claims: Iterable[ExtractedClaim],
    contextual_trust: Mapping[
        tuple[str, str, str],
        ContextTrust,
    ],
    global_trust: Mapping[str, ContextTrust],
) -> RawKnowledgeIndex:
    grouped: dict[
        tuple[str, str],
        list[ExtractedClaim],
    ] = defaultdict(list)
    for claim in claims:
        if claim.source not in global_trust:
            raise ValueError(
                f"missing trust estimate for source {claim.source!r}"
            )
        grouped[(claim.relation, claim.subject)].append(claim)
    return RawKnowledgeIndex(
        {
            key: tuple(
                sorted(
                    items,
                    key=lambda item: (
                        item.origin,
                        item.source,
                        item.provenance,
                    ),
                )
            )
            for key, items in grouped.items()
        },
        dict(contextual_trust),
        dict(global_trust),
    )
