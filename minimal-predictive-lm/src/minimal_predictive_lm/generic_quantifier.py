from __future__ import annotations

from dataclasses import dataclass
import json
import re
import unicodedata
from typing import Iterable, Mapping, Sequence


_INVENTORY_RE = re.compile(
    r"\bi\s+have\s+(.*?)\.\s*how\s+many\s+(.+?)\s+do\s+i\s+have\s*\?\s*$",
    re.IGNORECASE,
)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).casefold()).strip()


def _bits(payload: object) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ) * 8


@dataclass(frozen=True)
class QuantityObservation:
    surface: str
    value: int


@dataclass(frozen=True)
class QuantifiedExample:
    prompt: str
    answer: int


@dataclass(frozen=True)
class MembershipObservation:
    item: str
    concept: str


@dataclass(frozen=True)
class QuantifiedItem:
    surface: str
    quantity: int


@dataclass(frozen=True)
class ParsedQuantifiedQuery:
    items: tuple[QuantifiedItem, ...]
    query_concept: str


@dataclass(frozen=True)
class IdentifiabilityInterval:
    minimum: int
    maximum: int

    @property
    def identifiable(self) -> bool:
        return self.minimum == self.maximum


@dataclass(frozen=True)
class GenericQuantifierProgram:
    quantity_lexicon: tuple[tuple[str, int], ...]
    universal_concepts: tuple[str, ...]
    memberships: tuple[tuple[str, str], ...]
    domain_specific_handlers: int = 0

    def quantity_map(self) -> dict[str, int]:
        return dict(self.quantity_lexicon)

    def membership_map(self) -> dict[str, set[str]]:
        output: dict[str, set[str]] = {}
        for item, concept in self.memberships:
            output.setdefault(item, set()).add(concept)
        return output

    def parse(self, prompt: str) -> ParsedQuantifiedQuery | None:
        return parse_quantified_query(prompt, self.quantity_map())

    def identifiability_interval(self, prompt: str) -> IdentifiabilityInterval | None:
        parsed = self.parse(prompt)
        if parsed is None:
            return None
        if parsed.query_concept in self.universal_concepts:
            total = sum(item.quantity for item in parsed.items)
            return IdentifiabilityInterval(total, total)
        memberships = self.membership_map()
        minimum = 0
        maximum = 0
        for item in parsed.items:
            concepts = memberships.get(_normalize(item.surface))
            if concepts is None:
                maximum += item.quantity
            elif parsed.query_concept in concepts:
                minimum += item.quantity
                maximum += item.quantity
        return IdentifiabilityInterval(minimum, maximum)

    def answer(self, prompt: str) -> int | None:
        interval = self.identifiability_interval(prompt)
        if interval is None or not interval.identifiable:
            return None
        return interval.minimum

    def render(self) -> object:
        return {
            "quantity_lexicon": [list(row) for row in self.quantity_lexicon],
            "universal_concepts": list(self.universal_concepts),
            "memberships": [list(row) for row in self.memberships],
            "domain_specific_handlers": self.domain_specific_handlers,
        }

    @property
    def description_bits(self) -> int:
        return _bits(self.render())


def induce_quantity_lexicon(
    observations: Iterable[QuantityObservation],
) -> tuple[tuple[str, int], ...]:
    mapping: dict[str, int] = {}
    for observation in observations:
        key = _normalize(observation.surface)
        if observation.value <= 0:
            raise ValueError("quantity values must be positive")
        incumbent = mapping.get(key)
        if incumbent is not None and incumbent != observation.value:
            raise ValueError("inconsistent quantity grounding")
        mapping[key] = observation.value
    if not mapping:
        raise ValueError("at least one quantity observation is required")
    return tuple(sorted(mapping.items()))


def _split_inventory(text: str) -> tuple[str, ...]:
    normalized = re.sub(r"\s*,?\s+and\s+", ", ", text, flags=re.IGNORECASE)
    return tuple(part.strip() for part in normalized.split(",") if part.strip())


def _parse_item(phrase: str, quantities: Mapping[str, int]) -> QuantifiedItem | None:
    words = phrase.strip().split()
    if not words:
        return None
    first = _normalize(words[0])
    if first in quantities:
        quantity = quantities[first]
        surface = " ".join(words[1:]).strip()
    else:
        return None
    if not surface:
        return None
    return QuantifiedItem(_normalize(surface), quantity)


def parse_quantified_query(
    prompt: str,
    quantities: Mapping[str, int],
) -> ParsedQuantifiedQuery | None:
    match = _INVENTORY_RE.search(unicodedata.normalize("NFKC", prompt))
    if match is None:
        return None
    item_rows: list[QuantifiedItem] = []
    for phrase in _split_inventory(match.group(1)):
        item = _parse_item(phrase, quantities)
        if item is None:
            return None
        item_rows.append(item)
    if not item_rows:
        return None
    return ParsedQuantifiedQuery(tuple(item_rows), _normalize(match.group(2)))


def induce_universal_concepts(
    examples: Iterable[QuantifiedExample],
    quantities: Mapping[str, int],
) -> tuple[str, ...]:
    candidates: set[str] = set()
    for example in examples:
        parsed = parse_quantified_query(example.prompt, quantities)
        if parsed is None:
            raise ValueError("universal-concept example could not be parsed")
        total = sum(item.quantity for item in parsed.items)
        if total != example.answer:
            raise ValueError("example does not support an all-items concept")
        candidates.add(parsed.query_concept)
    if not candidates:
        raise ValueError("at least one universal concept example is required")
    return tuple(sorted(candidates))


def induce_generic_quantifier(
    quantity_observations: Iterable[QuantityObservation],
    universal_examples: Iterable[QuantifiedExample],
    memberships: Iterable[MembershipObservation] = (),
) -> GenericQuantifierProgram:
    quantity_rows = induce_quantity_lexicon(quantity_observations)
    quantity_map = dict(quantity_rows)
    universal = induce_universal_concepts(universal_examples, quantity_map)
    membership_rows = tuple(
        sorted(
            {
                (_normalize(observation.item), _normalize(observation.concept))
                for observation in memberships
            }
        )
    )
    return GenericQuantifierProgram(quantity_rows, universal, membership_rows)


def interval_widths(
    program: GenericQuantifierProgram,
    prompts: Sequence[str],
) -> tuple[int, ...]:
    output: list[int] = []
    for prompt in prompts:
        interval = program.identifiability_interval(prompt)
        output.append(-1 if interval is None else interval.maximum - interval.minimum)
    return tuple(output)
