from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
import unicodedata
from typing import Iterable, Mapping


@dataclass(frozen=True)
class WorldState:
    facts: tuple[tuple[str, str, str], ...] = ()

    def as_dict(self) -> dict[tuple[str, str], str]:
        return {(relation, subject): value for relation, subject, value in self.facts}

    @classmethod
    def from_dict(cls, facts: Mapping[tuple[str, str], str]) -> "WorldState":
        return cls(
            tuple(
                sorted(
                    (relation, subject, value)
                    for (relation, subject), value in facts.items()
                )
            )
        )


@dataclass(frozen=True)
class Interaction:
    action_token: str
    arguments: tuple[str, str]
    before: WorldState
    after: WorldState
    reward: float = 1.0


@dataclass(frozen=True)
class ConceptSchema:
    identifier: str
    relation: str
    subject_argument: int
    value_argument: int


@dataclass(frozen=True)
class ConceptMachine:
    schemas: tuple[ConceptSchema, ...]
    action_to_concept: Mapping[str, str]

    def schema(self, concept_id: str) -> ConceptSchema:
        return next(
            schema for schema in self.schemas if schema.identifier == concept_id
        )

    def execute(
        self,
        concept_id: str,
        arguments: tuple[str, str],
        state: WorldState,
    ) -> WorldState:
        schema = self.schema(concept_id)
        facts = state.as_dict()
        subject = arguments[schema.subject_argument]
        value = arguments[schema.value_argument]
        facts[(schema.relation, subject)] = value
        return WorldState.from_dict(facts)

    def plan(
        self,
        current: WorldState,
        target: WorldState,
    ) -> tuple[tuple[str, tuple[str, str]], ...]:
        current_facts = current.as_dict()
        target_facts = target.as_dict()
        steps: list[tuple[str, tuple[str, str]]] = []
        by_relation = {schema.relation: schema for schema in self.schemas}
        for (relation, subject), target_value in sorted(target_facts.items()):
            if current_facts.get((relation, subject)) == target_value:
                continue
            schema = by_relation[relation]
            arguments = ["", ""]
            arguments[schema.subject_argument] = subject
            arguments[schema.value_argument] = target_value
            steps.append((schema.identifier, (arguments[0], arguments[1])))
        return tuple(steps)

    @property
    def description_bits(self) -> int:
        schema_payload = [
            {
                "id": schema.identifier,
                "relation": schema.relation,
                "subject_argument": schema.subject_argument,
                "value_argument": schema.value_argument,
            }
            for schema in self.schemas
        ]
        binding_payload = sorted(self.action_to_concept.items())
        return len(
            json.dumps(
                {"schemas": schema_payload, "bindings": binding_payload},
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ) * 8


@dataclass(frozen=True)
class LanguageExample:
    language: str
    surface: str
    concept_id: str


@dataclass(frozen=True)
class LanguageRule:
    language: str
    feature: str
    concept_id: str
    support: int


@dataclass(frozen=True)
class LanguageCodec:
    rules: tuple[LanguageRule, ...]
    output_templates: Mapping[tuple[str, str], str]

    def ground(self, language: str, surface: str) -> str | None:
        features = text_features(surface)
        scores: dict[str, int] = {}
        for rule in self.rules:
            if rule.language != language or rule.feature not in features:
                continue
            payload = rule.feature.split(":", 1)[1]
            scores[rule.concept_id] = scores.get(rule.concept_id, 0) + len(payload)
        if not scores:
            return None
        best = max(scores.values())
        winners = sorted(
            concept for concept, score in scores.items() if score == best
        )
        return winners[0] if len(winners) == 1 else None

    def render(
        self,
        language: str,
        concept_id: str,
        arguments: tuple[str, str],
    ) -> str:
        return self.output_templates[(language, concept_id)].format(*arguments)

    @property
    def description_bits(self) -> int:
        payload = {
            "rules": [
                {
                    "language": rule.language,
                    "feature": rule.feature,
                    "concept_id": rule.concept_id,
                    "support": rule.support,
                }
                for rule in self.rules
            ],
            "templates": [
                {
                    "language": language,
                    "concept_id": concept_id,
                    "template": template,
                }
                for (language, concept_id), template in sorted(
                    self.output_templates.items()
                )
            ],
        }
        return len(
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ) * 8


def canonical_text(raw: str) -> str:
    normalized = unicodedata.normalize("NFKC", raw).lower()
    normalized = re.sub(
        r"[^0-9a-zA-Zぁ-んァ-ヶ一-龠_]+",
        " ",
        normalized,
    )
    return " ".join(normalized.split())


def text_features(raw: str) -> frozenset[str]:
    normalized = canonical_text(raw)
    features: set[str] = set()
    for token in normalized.split():
        features.add(f"w:{token}")
        for japanese in re.findall(r"[ぁ-んァ-ヶ一-龠]+", token):
            for width in range(2, min(6, len(japanese)) + 1):
                for start in range(len(japanese) - width + 1):
                    features.add(
                        f"j{width}:{japanese[start:start + width]}"
                    )
        for latin in re.findall(r"[a-z0-9_]+", token):
            features.add(f"a:{latin}")
            for width in range(3, min(7, len(latin)) + 1):
                for start in range(len(latin) - width + 1):
                    features.add(f"a{width}:{latin[start:start + width]}")
    return frozenset(features)


def infer_effect_signature(interaction: Interaction) -> tuple[str, int, int]:
    before = interaction.before.as_dict()
    after = interaction.after.as_dict()
    changes = [
        (key, value)
        for key, value in after.items()
        if before.get(key) != value
    ]
    if len(changes) != 1:
        raise ValueError(
            f"expected exactly one changed fact, got {changes!r}"
        )
    (relation, subject), value = changes[0]
    try:
        subject_argument = interaction.arguments.index(subject)
        value_argument = interaction.arguments.index(value)
    except ValueError as exc:
        raise ValueError(
            "changed subject/value must be present in action arguments"
        ) from exc
    if subject_argument == value_argument:
        raise ValueError("subject and value roles must be distinct")
    return relation, subject_argument, value_argument


def induce_concepts(interactions: Iterable[Interaction]) -> ConceptMachine:
    items = list(interactions)
    signatures_by_action: dict[str, set[tuple[str, int, int]]] = {}
    for interaction in items:
        signatures_by_action.setdefault(
            interaction.action_token,
            set(),
        ).add(infer_effect_signature(interaction))

    unstable = {
        action: signatures
        for action, signatures in signatures_by_action.items()
        if len(signatures) != 1
    }
    if unstable:
        raise ValueError(f"unstable action effects: {unstable!r}")

    unique_signatures = sorted(
        {
            next(iter(signatures))
            for signatures in signatures_by_action.values()
        }
    )
    concept_by_signature = {
        signature: f"C{index}"
        for index, signature in enumerate(unique_signatures)
    }
    schemas = tuple(
        ConceptSchema(
            concept_by_signature[signature],
            signature[0],
            signature[1],
            signature[2],
        )
        for signature in unique_signatures
    )
    action_to_concept = {
        action: concept_by_signature[next(iter(signatures))]
        for action, signatures in sorted(signatures_by_action.items())
    }
    return ConceptMachine(schemas, action_to_concept)


def _feature_cost(feature: str) -> float:
    payload = feature.split(":", 1)[1]
    return (
        len(feature.encode("utf-8")) * 8
        + 32.0 / max(1, len(payload) ** 2)
    )


def induce_language_codec(
    examples: Iterable[LanguageExample],
    output_templates: Mapping[tuple[str, str], str],
    *,
    minimum_support: int = 1,
) -> LanguageCodec:
    items = list(examples)
    selected: list[LanguageRule] = []
    languages = sorted({item.language for item in items})
    concepts = sorted({item.concept_id for item in items})

    for language in languages:
        language_items = [
            item for item in items if item.language == language
        ]
        feature_sets = {
            item.surface: text_features(item.surface)
            for item in language_items
        }
        for concept_id in concepts:
            positives = [
                item
                for item in language_items
                if item.concept_id == concept_id
            ]
            negatives = [
                item
                for item in language_items
                if item.concept_id != concept_id
            ]
            if not positives:
                continue
            candidate_features = set().union(
                *(feature_sets[item.surface] for item in positives)
            )
            candidates: list[tuple[str, frozenset[str], float]] = []
            for feature in candidate_features:
                covered = frozenset(
                    item.surface
                    for item in positives
                    if feature in feature_sets[item.surface]
                )
                contamination = sum(
                    feature in feature_sets[item.surface]
                    for item in negatives
                )
                if len(covered) < minimum_support or contamination:
                    continue
                candidates.append(
                    (feature, covered, _feature_cost(feature))
                )

            uncovered = {item.surface for item in positives}
            while uncovered:
                available = [
                    candidate
                    for candidate in candidates
                    if candidate[1] & uncovered
                ]
                if not available:
                    raise ValueError(
                        f"no stable feature cover for {(language, concept_id)}"
                    )
                best = max(
                    available,
                    key=lambda candidate: (
                        len(candidate[1] & uncovered) / candidate[2],
                        len(candidate[1] & uncovered),
                        len(candidate[0]),
                        candidate[0],
                    ),
                )
                selected.append(
                    LanguageRule(
                        language,
                        best[0],
                        concept_id,
                        len(best[1]),
                    )
                )
                uncovered.difference_update(best[1])

    return LanguageCodec(
        tuple(
            sorted(
                selected,
                key=lambda rule: (
                    rule.language,
                    rule.concept_id,
                    rule.feature,
                ),
            )
        ),
        dict(output_templates),
    )


def codec_accuracy(
    codec: LanguageCodec,
    examples: Iterable[LanguageExample],
) -> float:
    items = list(examples)
    return sum(
        codec.ground(item.language, item.surface) == item.concept_id
        for item in items
    ) / len(items)


def language_first_description_bits(
    examples: Iterable[LanguageExample],
    schemas: Mapping[str, ConceptSchema],
    output_templates: Mapping[tuple[str, str], str],
) -> int:
    payload = []
    for item in examples:
        schema = schemas[item.concept_id]
        payload.append(
            {
                "language": item.language,
                "surface": item.surface,
                "relation": schema.relation,
                "subject_argument": schema.subject_argument,
                "value_argument": schema.value_argument,
                "output_template": output_templates[
                    (item.language, item.concept_id)
                ],
            }
        )
    return len(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ) * 8


def permutation_equivalent_groundings(number_of_concepts: int) -> int:
    return math.factorial(number_of_concepts)


def grounding_lower_bound_bits(number_of_concepts: int) -> float:
    return math.log2(
        permutation_equivalent_groundings(number_of_concepts)
    )
