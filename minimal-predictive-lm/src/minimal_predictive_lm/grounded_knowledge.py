from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Iterable, Mapping


@dataclass(frozen=True)
class SourceObservation:
    source: str
    correct: bool


@dataclass(frozen=True)
class Claim:
    subject: str
    relation: str
    value: str
    source: str
    provenance: str


@dataclass(frozen=True)
class SourceTrust:
    source: str
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
class KnowledgeAnswer:
    value: str | None
    confidence: float
    abstained: bool
    conflict: bool
    claims_read: int
    available_claims: int
    provenance: tuple[str, ...]
    scores: Mapping[str, float]


@dataclass(frozen=True)
class KnowledgeIndex:
    claims_by_key: Mapping[tuple[str, str], tuple[Claim, ...]]
    trust: Mapping[str, SourceTrust]

    @property
    def description_bits(self) -> int:
        payload = {
            "trust": [
                {
                    "source": item.source,
                    "successes": item.successes,
                    "failures": item.failures,
                }
                for item in sorted(
                    self.trust.values(),
                    key=lambda item: item.source,
                )
            ],
            "claims": [
                {
                    "subject": claim.subject,
                    "relation": claim.relation,
                    "value": claim.value,
                    "source": claim.source,
                    "provenance": claim.provenance,
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

    def answer(
        self,
        subject: str,
        relation: str,
        *,
        confidence_threshold: float = 0.8,
        adaptive: bool = True,
    ) -> KnowledgeAnswer:
        claims = list(self.claims_by_key.get((relation, subject), ()))
        if not claims:
            return KnowledgeAnswer(
                None,
                0.0,
                True,
                False,
                0,
                0,
                (),
                {},
            )

        claims.sort(
            key=lambda claim: (
                -self.trust[claim.source].weight,
                claim.source,
                claim.provenance,
            )
        )
        weights = [
            self.trust[claim.source].weight for claim in claims
        ]
        remaining_weight = sum(weights)
        scores: dict[str, float] = {}
        provenance: list[str] = []
        values_seen: set[str] = set()
        reads = 0

        for claim, weight in zip(claims, weights):
            remaining_weight -= weight
            scores[claim.value] = scores.get(claim.value, 0.0) + weight
            provenance.append(claim.provenance)
            values_seen.add(claim.value)
            reads += 1

            if adaptive:
                leader_value, leader_score = max(
                    scores.items(),
                    key=lambda item: (item[1], item[0]),
                )
                competitors = [
                    score
                    for value, score in scores.items()
                    if value != leader_value
                ]
                strongest_known = max([0.0, *competitors])
                worst_opponent = strongest_known + remaining_weight
                lower_confidence = _binary_confidence(
                    leader_score,
                    worst_opponent,
                )
                if lower_confidence >= confidence_threshold:
                    return KnowledgeAnswer(
                        leader_value,
                        lower_confidence,
                        False,
                        len(values_seen) > 1,
                        reads,
                        len(claims),
                        tuple(provenance),
                        dict(scores),
                    )

        leader_value, leader_score = max(
            scores.items(),
            key=lambda item: (item[1], item[0]),
        )
        denominator = math.exp(-leader_score)
        for value, score in scores.items():
            if value == leader_value:
                continue
            denominator += math.exp(score - leader_score)
        confidence = 1.0 / (1.0 + denominator)
        abstained = confidence < confidence_threshold
        return KnowledgeAnswer(
            None if abstained else leader_value,
            confidence,
            abstained,
            len(values_seen) > 1,
            reads,
            len(claims),
            tuple(provenance),
            dict(scores),
        )


def _binary_confidence(leader: float, opponent: float) -> float:
    difference = opponent - leader
    if difference > 700:
        return 0.0
    if difference < -700:
        return 1.0
    return 1.0 / (1.0 + math.exp(difference))


def learn_source_trust(
    observations: Iterable[SourceObservation],
) -> dict[str, SourceTrust]:
    counts: dict[str, list[int]] = {}
    for observation in observations:
        counts.setdefault(observation.source, [0, 0])
        counts[observation.source][
            0 if observation.correct else 1
        ] += 1
    return {
        source: SourceTrust(source, successes, failures)
        for source, (successes, failures) in sorted(counts.items())
    }


def build_knowledge_index(
    claims: Iterable[Claim],
    trust: Mapping[str, SourceTrust],
) -> KnowledgeIndex:
    grouped: dict[tuple[str, str], list[Claim]] = {}
    for claim in claims:
        if claim.source not in trust:
            raise ValueError(
                f"missing trust estimate for source {claim.source!r}"
            )
        grouped.setdefault(
            (claim.relation, claim.subject),
            [],
        ).append(claim)
    return KnowledgeIndex(
        {
            key: tuple(
                sorted(
                    items,
                    key=lambda item: (
                        item.source,
                        item.provenance,
                    ),
                )
            )
            for key, items in grouped.items()
        },
        dict(trust),
    )
