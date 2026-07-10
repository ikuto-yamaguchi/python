from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import re
from typing import Iterable, Sequence


@dataclass(frozen=True)
class SemanticExample:
    text: str
    intent: str
    entity: str | None = None
    location: str | None = None


@dataclass(frozen=True)
class SemanticProgram:
    intent: str
    entity: str | None
    location: str | None


Atom = tuple[str, str]
Rule = tuple[Atom, ...]


def normalize_surface(text: str) -> str:
    return re.sub(
        r"\s+",
        "",
        text.strip().replace("？", "?").replace("。", "").replace("！", "!"),
    )


def mask_typed_symbols(
    text: str,
    entities: Sequence[str],
    locations: Sequence[str],
) -> tuple[str, str | None, str | None]:
    """Replace known runtime symbols with typed slots without memorizing utterances."""

    masked = normalize_surface(text)
    entity: str | None = None
    location: str | None = None

    for candidate in sorted(entities, key=len, reverse=True):
        if candidate in masked:
            entity = candidate
            masked = masked.replace(candidate, "<E>", 1)
            break

    for candidate in sorted(locations, key=len, reverse=True):
        if candidate in masked:
            location = candidate
            masked = masked.replace(candidate, "<L>", 1)
            break

    return masked, entity, location


def _atom_matches(atom: Atom, skeleton: str) -> bool:
    kind, value = atom
    if kind == "contains":
        return value in skeleton
    if kind == "has_entity":
        return "<E>" in skeleton
    if kind == "has_location":
        return "<L>" in skeleton
    if kind == "no_entity":
        return "<E>" not in skeleton
    if kind == "no_location":
        return "<L>" not in skeleton
    if kind == "entity_before_location":
        return (
            "<E>" in skeleton
            and "<L>" in skeleton
            and skeleton.index("<E>") < skeleton.index("<L>")
        )
    if kind == "location_before_entity":
        return (
            "<E>" in skeleton
            and "<L>" in skeleton
            and skeleton.index("<L>") < skeleton.index("<E>")
        )
    raise ValueError(f"unknown atom: {kind}")


def atom_description_bits(atom: Atom) -> int:
    kind, value = atom
    if kind == "contains":
        return 4 + 8 * len(value.encode("utf-8"))
    return 4


def rule_description_bits(rule: Rule) -> int:
    return 3 + sum(atom_description_bits(atom) for atom in rule)


class ExactSurfaceParser:
    """Memorization baseline: exact normalized utterance -> exact semantic program."""

    def __init__(self, examples: Iterable[SemanticExample]) -> None:
        self._programs = {
            normalize_surface(example.text): SemanticProgram(
                example.intent, example.entity, example.location
            )
            for example in examples
            if example.intent != "other"
        }

    def parse(self, text: str) -> SemanticProgram | None:
        return self._programs.get(normalize_surface(text))

    @property
    def description_bits(self) -> int:
        return sum(
            8 * len(surface.encode("utf-8")) + 2
            for surface in self._programs
        )


class SlotTemplateParser:
    """Typed-slot baseline: memorizes surface skeletons but not entity/location pairs."""

    def __init__(
        self,
        examples: Iterable[SemanticExample],
        entities: Sequence[str],
        locations: Sequence[str],
    ) -> None:
        self.entities = tuple(entities)
        self.locations = tuple(locations)
        self._intents: dict[str, str] = {}
        for example in examples:
            if example.intent == "other":
                continue
            skeleton, _, _ = mask_typed_symbols(
                example.text, self.entities, self.locations
            )
            self._intents[skeleton] = example.intent

    def parse(self, text: str) -> SemanticProgram | None:
        skeleton, entity, location = mask_typed_symbols(
            text, self.entities, self.locations
        )
        intent = self._intents.get(skeleton)
        if intent is None:
            return None
        return SemanticProgram(intent, entity, location)

    @property
    def description_bits(self) -> int:
        return sum(
            8 * len(skeleton.encode("utf-8")) + 2
            for skeleton in self._intents
        )


class InducedFeatureParser:
    """Small symbolic hypothesis search over typed slots and character features.

    The candidate language is intentionally restricted. It searches conjunctions
    of one or two atoms and greedily covers each intent with rules that make no
    training false positives. A validation objective chooses the minimum n-gram
    length instead of fixing it by hand.
    """

    STRUCTURAL_ATOMS: tuple[Atom, ...] = (
        ("has_entity", ""),
        ("has_location", ""),
        ("no_entity", ""),
        ("no_location", ""),
        ("entity_before_location", ""),
        ("location_before_entity", ""),
    )

    def __init__(
        self,
        rules: dict[str, tuple[Rule, ...]],
        entities: Sequence[str],
        locations: Sequence[str],
        *,
        min_ngram: int,
        validation_objective: int,
    ) -> None:
        self.rules = rules
        self.entities = tuple(entities)
        self.locations = tuple(locations)
        self.min_ngram = min_ngram
        self.validation_objective = validation_objective

    @classmethod
    def _fit_with_min_ngram(
        cls,
        examples: Sequence[SemanticExample],
        entities: Sequence[str],
        locations: Sequence[str],
        *,
        min_ngram: int,
        max_ngram: int = 6,
    ) -> "InducedFeatureParser":
        skeletons = [
            mask_typed_symbols(example.text, entities, locations)[0]
            for example in examples
        ]
        atoms: set[Atom] = set(cls.STRUCTURAL_ATOMS)

        for skeleton in skeletons:
            literal = skeleton.replace("<E>", "").replace("<L>", "")
            for width in range(min_ngram, max_ngram + 1):
                for start in range(max(0, len(literal) - width + 1)):
                    substring = literal[start : start + width]
                    if substring and not all(char in "、,?!" for char in substring):
                        atoms.add(("contains", substring))

        rules: dict[str, tuple[Rule, ...]] = {}
        target_intents = sorted(
            {example.intent for example in examples if example.intent != "other"}
        )
        atom_list = sorted(atoms)

        for intent in target_intents:
            positives = {
                index
                for index, example in enumerate(examples)
                if example.intent == intent
            }
            negatives = set(range(len(examples))) - positives
            candidates: list[tuple[Rule, set[int], int]] = []

            for size in (1, 2):
                for rule in combinations(atom_list, size):
                    if not any(atom[0] == "contains" for atom in rule):
                        continue
                    coverage = {
                        index
                        for index, skeleton in enumerate(skeletons)
                        if all(_atom_matches(atom, skeleton) for atom in rule)
                    }
                    positive_coverage = coverage & positives
                    if positive_coverage and not (coverage & negatives):
                        candidates.append(
                            (rule, positive_coverage, rule_description_bits(rule))
                        )

            uncovered = set(positives)
            chosen: list[Rule] = []
            while uncovered:
                eligible = [
                    candidate
                    for candidate in candidates
                    if candidate[1] & uncovered
                ]
                if not eligible:
                    break
                best = max(
                    eligible,
                    key=lambda candidate: (
                        len(candidate[1] & uncovered),
                        -candidate[2],
                    ),
                )
                chosen.append(best[0])
                uncovered -= best[1]

            rules[intent] = tuple(chosen)

        return cls(
            rules,
            entities,
            locations,
            min_ngram=min_ngram,
            validation_objective=0,
        )

    @classmethod
    def fit(
        cls,
        training: Sequence[SemanticExample],
        validation: Sequence[SemanticExample],
        entities: Sequence[str],
        locations: Sequence[str],
        *,
        candidate_min_ngrams: Sequence[int] = (1, 2, 3, 4),
        error_bits: int = 512,
    ) -> "InducedFeatureParser":
        candidates: list[InducedFeatureParser] = []
        for min_ngram in candidate_min_ngrams:
            parser = cls._fit_with_min_ngram(
                training,
                entities,
                locations,
                min_ngram=min_ngram,
            )
            errors = 0
            for example in validation:
                program = parser.parse(example.text)
                predicted = program.intent if program is not None else "other"
                errors += int(predicted != example.intent)
            parser.validation_objective = (
                errors * error_bits + parser.description_bits
            )
            candidates.append(parser)

        return min(
            candidates,
            key=lambda parser: (
                parser.validation_objective,
                parser.description_bits,
                parser.min_ngram,
            ),
        )

    def parse(self, text: str) -> SemanticProgram | None:
        skeleton, entity, location = mask_typed_symbols(
            text, self.entities, self.locations
        )
        matches: list[tuple[str, int, int]] = []

        for intent, intent_rules in self.rules.items():
            satisfied = [
                rule
                for rule in intent_rules
                if all(_atom_matches(atom, skeleton) for atom in rule)
            ]
            if satisfied:
                matches.append(
                    (
                        intent,
                        max(len(rule) for rule in satisfied),
                        min(rule_description_bits(rule) for rule in satisfied),
                    )
                )

        if not matches:
            return None

        matches.sort(key=lambda item: (item[1], -item[2]), reverse=True)
        if len(matches) > 1 and matches[0][1:] == matches[1][1:]:
            return None

        return SemanticProgram(matches[0][0], entity, location)

    @property
    def description_bits(self) -> int:
        return sum(
            rule_description_bits(rule)
            for intent_rules in self.rules.values()
            for rule in intent_rules
        )

    @property
    def rule_count(self) -> int:
        return sum(len(intent_rules) for intent_rules in self.rules.values())

    def checks_per_utterance_upper_bound(self) -> int:
        return self.rule_count * 2
