from __future__ import annotations

from dataclasses import dataclass
import json
import re
import unicodedata
from typing import Iterable, Mapping


def _normalize_phrase(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold().strip()
    text = re.sub(r"\s+", " ", text)
    return text.rstrip(".?! ")


def _bits(payload: object) -> int:
    return len(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ) * 8


@dataclass(frozen=True)
class TruthPhraseObservation:
    surface: str
    polarity: bool


@dataclass(frozen=True)
class AttributionObservation:
    surface: str


@dataclass(frozen=True)
class SignedClaim:
    speaker: str
    target: str
    asserted_truth: bool

    def render(self) -> object:
        return [self.speaker, self.target, self.asserted_truth]


@dataclass(frozen=True)
class SignedClaimProgram:
    base_assignments: tuple[tuple[str, bool], ...]
    claims: tuple[SignedClaim, ...]
    query_entity: str
    query_polarity: bool = True

    def render(self) -> object:
        return {
            "base_assignments": [list(row) for row in self.base_assignments],
            "claims": [claim.render() for claim in self.claims],
            "query_entity": self.query_entity,
            "query_polarity": self.query_polarity,
        }


@dataclass(frozen=True)
class ClaimPrediction:
    output: str | None
    operations: int
    reads: int
    writes: int
    known_entities: int
    conflicted_entities: tuple[str, ...]
    unresolved_entities: tuple[str, ...]


@dataclass(frozen=True)
class SignedClaimRuntime:
    """Resolve signed attributed claims by monotone fixed-point propagation.

    A truthful speaker's statement matches the target's truth value. A lying
    speaker's statement does not. Multiple incompatible derivations create an
    explicit conflict and therefore force abstention for that entity.
    """

    def execute(self, program: SignedClaimProgram) -> ClaimPrediction:
        values: dict[str, set[bool]] = {}
        operations = reads = writes = 0

        for entity, truth in program.base_assignments:
            values.setdefault(entity, set()).add(bool(truth))
            operations += 1
            writes += 1

        changed = True
        while changed:
            changed = False
            for claim in program.claims:
                operations += 1
                target_values = values.get(claim.target, set())
                reads += 1
                if len(target_values) != 1:
                    continue
                target_truth = next(iter(target_values))
                speaker_truth = target_truth == claim.asserted_truth
                bucket = values.setdefault(claim.speaker, set())
                if speaker_truth not in bucket:
                    bucket.add(speaker_truth)
                    writes += 1
                    changed = True

        query_values = values.get(program.query_entity, set())
        reads += 1
        conflicts = tuple(sorted(entity for entity, rows in values.items() if len(rows) > 1))
        entities = {
            entity for entity, _truth in program.base_assignments
        } | {
            claim.speaker for claim in program.claims
        } | {
            claim.target for claim in program.claims
        } | {program.query_entity}
        unresolved = tuple(sorted(entity for entity in entities if not values.get(entity)))
        if len(query_values) != 1:
            return ClaimPrediction(
                None,
                operations,
                reads,
                writes,
                sum(len(rows) == 1 for rows in values.values()),
                conflicts,
                unresolved,
            )
        actual = next(iter(query_values))
        return ClaimPrediction(
            "Yes" if actual == program.query_polarity else "No",
            operations,
            reads,
            writes,
            sum(len(rows) == 1 for rows in values.values()),
            conflicts,
            unresolved,
        )


@dataclass(frozen=True)
class SignedClaimMachine:
    truth_phrases: tuple[tuple[str, bool], ...]
    attribution_phrases: tuple[str, ...]
    runtime: SignedClaimRuntime = SignedClaimRuntime()
    benchmark_task_name_branches: int = 0
    domain_specific_handlers: int = 0

    def truth_map(self) -> dict[str, bool]:
        return dict(self.truth_phrases)

    def compile(self, prompt: str) -> SignedClaimProgram | None:
        return compile_signed_claim_program(
            prompt,
            truth_phrases=self.truth_map(),
            attribution_phrases=self.attribution_phrases,
        )

    def predict(self, prompt: str) -> ClaimPrediction:
        program = self.compile(prompt)
        if program is None:
            return ClaimPrediction(None, 1, 0, 0, 0, (), ())
        return self.runtime.execute(program)

    def render(self) -> object:
        return {
            "truth_phrases": [list(row) for row in self.truth_phrases],
            "attribution_phrases": list(self.attribution_phrases),
            "runtime": {
                "state": "entity -> {true,false}",
                "transition": "speaker_truth = (target_truth == asserted_truth)",
                "conflict_policy": "abstain",
                "unanchored_cycle_policy": "abstain",
            },
            "benchmark_task_name_branches": self.benchmark_task_name_branches,
            "domain_specific_handlers": self.domain_specific_handlers,
        }

    @property
    def description_bits(self) -> int:
        return _bits(self.render())


_ENTITY = r"[A-Z][A-Za-z'-]*"


def induce_truth_phrases(
    observations: Iterable[TruthPhraseObservation],
) -> tuple[tuple[str, bool], ...]:
    mapping: dict[str, bool] = {}
    for observation in observations:
        phrase = _normalize_phrase(observation.surface)
        if not phrase:
            raise ValueError("truth phrase cannot be empty")
        incumbent = mapping.get(phrase)
        if incumbent is not None and incumbent != observation.polarity:
            raise ValueError(f"conflicting truth phrase grounding: {phrase!r}")
        mapping[phrase] = bool(observation.polarity)
    if not mapping:
        raise ValueError("at least one truth phrase observation is required")
    return tuple(sorted(mapping.items()))


def induce_attribution_phrases(
    observations: Iterable[AttributionObservation],
) -> tuple[str, ...]:
    phrases = tuple(
        sorted(
            {_normalize_phrase(observation.surface) for observation in observations},
            key=lambda row: (-len(row), row),
        )
    )
    if not phrases or any(not phrase for phrase in phrases):
        raise ValueError("at least one non-empty attribution phrase is required")
    return phrases


def induce_signed_claim_machine(
    truth_observations: Iterable[TruthPhraseObservation],
    attribution_observations: Iterable[AttributionObservation],
) -> SignedClaimMachine:
    return SignedClaimMachine(
        induce_truth_phrases(truth_observations),
        induce_attribution_phrases(attribution_observations),
    )


def _split_sentences(prompt: str) -> tuple[str, ...]:
    text = unicodedata.normalize("NFKC", prompt).strip()
    text = re.sub(r"^Question:\s*", "", text, flags=re.IGNORECASE)
    rows = tuple(
        segment.strip()
        for segment in re.split(r"(?<=[.?!])\s+", text)
        if segment.strip()
    )
    return rows


def _match_truth_phrase(surface: str, phrases: Mapping[str, bool]) -> bool | None:
    normalized = _normalize_phrase(surface)
    return phrases.get(normalized)


def _parse_query(sentence: str, phrases: Mapping[str, bool]) -> tuple[str, bool] | None:
    normalized = sentence.strip().rstrip("?")
    match = re.fullmatch(rf"Does\s+({_ENTITY})\s+(.+)", normalized, re.IGNORECASE)
    if match:
        polarity = _match_truth_phrase(match.group(2), phrases)
        return None if polarity is None else (match.group(1), polarity)
    match = re.fullmatch(rf"Is\s+({_ENTITY})\s+(.+)", normalized, re.IGNORECASE)
    if match:
        polarity = _match_truth_phrase(f"is {match.group(2)}", phrases)
        return None if polarity is None else (match.group(1), polarity)
    return None


def compile_signed_claim_program(
    prompt: str,
    *,
    truth_phrases: Mapping[str, bool],
    attribution_phrases: Iterable[str],
) -> SignedClaimProgram | None:
    sentences = _split_sentences(prompt)
    if len(sentences) < 2:
        return None
    query = _parse_query(sentences[-1], truth_phrases)
    if query is None:
        return None

    bases: dict[str, bool] = {}
    claims: list[SignedClaim] = []
    attribution = tuple(attribution_phrases)
    for raw_sentence in sentences[:-1]:
        sentence = raw_sentence.rstrip(".?! ").strip()
        attributed = False
        for cue in attribution:
            match = re.fullmatch(
                rf"({_ENTITY})\s+{re.escape(cue)}\s+({_ENTITY})\s+(.+)",
                sentence,
                re.IGNORECASE,
            )
            if not match:
                continue
            polarity = _match_truth_phrase(match.group(3), truth_phrases)
            if polarity is None:
                return None
            claims.append(SignedClaim(match.group(1), match.group(2), polarity))
            attributed = True
            break
        if attributed:
            continue

        match = re.fullmatch(rf"({_ENTITY})\s+(.+)", sentence)
        if not match:
            return None
        polarity = _match_truth_phrase(match.group(2), truth_phrases)
        if polarity is None:
            return None
        entity = match.group(1)
        incumbent = bases.get(entity)
        if incumbent is not None and incumbent != polarity:
            return None
        bases[entity] = polarity

    if not bases or not claims:
        return None
    return SignedClaimProgram(
        tuple(sorted(bases.items())),
        tuple(claims),
        query[0],
        query[1],
    )
