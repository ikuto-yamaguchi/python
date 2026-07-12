from __future__ import annotations

from dataclasses import dataclass
import json
import re
import unicodedata
from typing import Iterable, Mapping

from .signed_claim_graph import SignedClaim, SignedClaimProgram


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold().strip()
    return re.sub(r"\s+", " ", text)


def _description_bits(payload: object) -> int:
    return len(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ) * 8


@dataclass(frozen=True)
class ClauseEvent:
    kind: str
    entity: str | None = None
    speaker: str | None = None
    target: str | None = None
    polarity: bool = True

    def render(self) -> object:
        return {
            "kind": self.kind,
            "entity": self.entity,
            "speaker": self.speaker,
            "target": self.target,
            "polarity": self.polarity,
        }


@dataclass(frozen=True)
class ClauseObservation:
    surface: str
    event: ClauseEvent


@dataclass(frozen=True)
class ClauseTemplate:
    kind: str
    tokens: tuple[str, ...]

    def render(self) -> object:
        return {"kind": self.kind, "tokens": list(self.tokens)}


@dataclass(frozen=True)
class InducedClauseCompiler:
    templates: tuple[ClauseTemplate, ...]
    truth_phrases: tuple[tuple[str, bool], ...]
    attribution_phrases: tuple[str, ...]
    training_observations: int
    benchmark_task_name_branches: int = 0

    def truth_map(self) -> dict[str, bool]:
        return dict(self.truth_phrases)

    def compile_clause(self, surface: str) -> ClauseEvent | None:
        runtime_tokens = _runtime_tokens(
            surface,
            truth_phrases=self.truth_map(),
            attribution_phrases=self.attribution_phrases,
        )
        if runtime_tokens is None:
            return None
        events = {
            json.dumps(event.render(), sort_keys=True): event
            for template in self.templates
            if (event := _match_template(template, runtime_tokens)) is not None
        }
        if len(events) != 1:
            return None
        return next(iter(events.values()))

    def compile_prompt(self, prompt: str) -> SignedClaimProgram | None:
        sentences = _split_sentences(prompt)
        if len(sentences) < 2:
            return None
        events = tuple(self.compile_clause(sentence) for sentence in sentences)
        if any(event is None for event in events):
            return None
        resolved = tuple(event for event in events if event is not None)
        queries = tuple(event for event in resolved if event.kind == "query")
        if len(queries) != 1 or resolved[-1].kind != "query":
            return None

        bases: dict[str, bool] = {}
        claims: list[SignedClaim] = []
        for event in resolved[:-1]:
            if event.kind == "base" and event.entity is not None:
                incumbent = bases.get(event.entity)
                if incumbent is not None and incumbent != event.polarity:
                    return None
                bases[event.entity] = event.polarity
            elif (
                event.kind == "claim"
                and event.speaker is not None
                and event.target is not None
            ):
                claims.append(SignedClaim(event.speaker, event.target, event.polarity))
            else:
                return None
        query = queries[0]
        if not bases or not claims or query.entity is None:
            return None
        return SignedClaimProgram(
            tuple(sorted(bases.items())),
            tuple(claims),
            query.entity,
            query.polarity,
        )

    def render(self) -> object:
        return {
            "templates": [template.render() for template in self.templates],
            "truth_phrases": [list(row) for row in self.truth_phrases],
            "attribution_phrases": list(self.attribution_phrases),
            "training_observations": self.training_observations,
            "matching": "exact token-class template with variable entity slots",
            "ambiguity_policy": "abstain",
            "benchmark_task_name_branches": self.benchmark_task_name_branches,
        }

    @property
    def description_bits(self) -> int:
        return _description_bits(self.render())


def _replace_literal(text: str, literal: str, replacement: str) -> str:
    return re.sub(
        rf"(?<![\w'-]){re.escape(_normalize(literal))}(?![\w'-])",
        replacement,
        text,
        flags=re.IGNORECASE,
    )


def _replace_grounded_phrases(
    text: str,
    truth_phrases: Mapping[str, bool],
    attribution_phrases: Iterable[str],
) -> str:
    output = text
    for phrase in sorted(truth_phrases, key=lambda row: (-len(row), row)):
        marker = "§truth:1" if truth_phrases[phrase] else "§truth:0"
        output = _replace_literal(output, phrase, marker)
    for phrase in sorted(attribution_phrases, key=lambda row: (-len(row), row)):
        output = _replace_literal(output, phrase, "§attribution")
    return output


def _tokenize(text: str) -> tuple[str, ...]:
    cleaned = text.strip().rstrip(".?! ")
    return tuple(token for token in cleaned.split() if token)


def _observation_tokens(
    observation: ClauseObservation,
    truth_phrases: Mapping[str, bool],
    attribution_phrases: Iterable[str],
) -> tuple[str, ...]:
    text = _normalize(observation.surface)
    event = observation.event
    if event.kind == "base":
        slots = (("§entity", event.entity),)
    elif event.kind == "claim":
        slots = (("§speaker", event.speaker), ("§target", event.target))
    elif event.kind == "query":
        slots = (("§entity", event.entity),)
    else:
        raise ValueError(f"unsupported clause kind: {event.kind!r}")

    for marker, value in sorted(slots, key=lambda row: -(len(row[1] or ""))):
        if not value:
            raise ValueError(f"missing slot value for {event.kind!r}")
        text = _replace_literal(text, value, marker)
    text = _replace_grounded_phrases(text, truth_phrases, attribution_phrases)
    tokens = tuple(
        "§truth" if token.startswith("§truth:") else token
        for token in _tokenize(text)
    )
    if "§truth" not in tokens:
        raise ValueError("observation has no grounded truth phrase")
    if event.kind == "claim" and "§attribution" not in tokens:
        raise ValueError("claim observation has no grounded attribution phrase")
    return tokens


def _runtime_tokens(
    surface: str,
    *,
    truth_phrases: Mapping[str, bool],
    attribution_phrases: Iterable[str],
) -> tuple[str, ...] | None:
    text = _normalize(surface)
    text = re.sub(r"^question:\s*", "", text)
    text = _replace_grounded_phrases(text, truth_phrases, attribution_phrases)
    tokens = _tokenize(text)
    if not tokens or not any(token.startswith("§truth:") for token in tokens):
        return None
    return tokens


def _is_entity_token(token: str) -> bool:
    return bool(re.fullmatch(r"[a-z][a-z0-9'-]*", token))


def _match_template(
    template: ClauseTemplate,
    runtime_tokens: tuple[str, ...],
) -> ClauseEvent | None:
    if len(template.tokens) != len(runtime_tokens):
        return None
    captured: dict[str, str] = {}
    polarity: bool | None = None
    for expected, observed in zip(template.tokens, runtime_tokens, strict=True):
        if expected in {"§entity", "§speaker", "§target"}:
            if not _is_entity_token(observed):
                return None
            captured[expected] = observed
        elif expected == "§truth":
            if observed == "§truth:1":
                polarity = True
            elif observed == "§truth:0":
                polarity = False
            else:
                return None
        elif expected == "§attribution":
            if observed != "§attribution":
                return None
        elif expected != observed:
            return None
    if polarity is None:
        return None
    if template.kind == "base":
        return ClauseEvent("base", entity=captured.get("§entity"), polarity=polarity)
    if template.kind == "claim":
        return ClauseEvent(
            "claim",
            speaker=captured.get("§speaker"),
            target=captured.get("§target"),
            polarity=polarity,
        )
    if template.kind == "query":
        return ClauseEvent("query", entity=captured.get("§entity"), polarity=polarity)
    return None


def _split_sentences(prompt: str) -> tuple[str, ...]:
    text = unicodedata.normalize("NFKC", prompt).strip()
    return tuple(
        segment.strip()
        for segment in re.split(r"(?<=[.?!])\s+", text)
        if segment.strip()
    )


def induce_clause_compiler(
    observations: Iterable[ClauseObservation],
    *,
    truth_phrases: Mapping[str, bool],
    attribution_phrases: Iterable[str],
) -> InducedClauseCompiler:
    rows = tuple(observations)
    if not rows:
        raise ValueError("at least one clause observation is required")
    normalized_truth = {
        _normalize(phrase): bool(polarity)
        for phrase, polarity in truth_phrases.items()
    }
    attribution = tuple(sorted({_normalize(row) for row in attribution_phrases}))
    templates = {
        ClauseTemplate(
            observation.event.kind,
            _observation_tokens(
                observation,
                normalized_truth,
                attribution,
            ),
        )
        for observation in rows
    }
    if {template.kind for template in templates} != {"base", "claim", "query"}:
        raise ValueError("observations must identify base, claim, and query templates")
    return InducedClauseCompiler(
        tuple(sorted(templates, key=lambda row: (row.kind, row.tokens))),
        tuple(sorted(normalized_truth.items())),
        attribution,
        len(rows),
    )
