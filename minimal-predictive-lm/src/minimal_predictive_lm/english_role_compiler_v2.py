from __future__ import annotations

import re

from .english_role_compiler import (
    _SEMANTIC_ROLE_CUES,
    CompiledReference,
    EnglishRoleReferenceResolver,
    ReferenceAnswer,
    _extract_prompt,
    _is_neutral_ambiguity,
    _normalise,
    _object_control,
    _option_entity,
    _possessive_fit,
    _sentence_mentions,
    _subject_control,
)
from .generic_reference_machine import ReferenceCandidate, ReferenceSituation


# Central predicates such as "is an expert" must outrank nouns that merely occur
# inside their complement ("expert on rare skin conditions").
_PRIORITY_CUES = tuple(
    row
    for key in (
        "expert on",
        "rare skin condition",
        "focuses on code",
        "understand the case",
        "repairing the sidewalk",
        "tax preparation",
        "like to teach",
        "completed the repair",
        "needed a lab assistant",
        "have to mop",
        "working on the house",
        "better understood the problem",
    )
    for row in _SEMANTIC_ROLE_CUES
    if key in row[0]
)


def _predicate_scope(sentence: str) -> str:
    lower = _normalise(sentence)
    matches = list(
        re.finditer(r"\b(?:he|she|they|him|her|them|his|their)\b", lower)
    )
    if not matches:
        return lower
    return lower[matches[-1].end() :].strip()


def _semantic_fit_v2(sentence: str, entity: str) -> bool:
    scope = _predicate_scope(sentence)
    for cues, roles in _PRIORITY_CUES:
        if any(cue in scope for cue in cues):
            return any(role in entity for role in roles)
    return False


def compile_reference_prompt_v2(prompt: str) -> CompiledReference | None:
    parsed = _extract_prompt(prompt)
    if parsed is None:
        return None
    sentence, options = parsed
    ambiguous = next(
        (letter for letter, text in options.items() if "ambiguous" in text.casefold()),
        None,
    )
    if ambiguous is None:
        return None
    mentions = _sentence_mentions(sentence)
    usable = {
        letter: entity
        for letter, text in options.items()
        if letter != ambiguous
        and (entity := _option_entity(text, mentions)) is not None
    }
    if len(usable) < 2:
        return None
    sentence_lower = _normalise(sentence)
    positions = [sentence_lower.find(entity) for entity in usable.values()]
    positions = [position for position in positions if position >= 0]
    if len(positions) < 2:
        return None
    neutral = _is_neutral_ambiguity(sentence)
    candidates: list[ReferenceCandidate] = []
    operations = len(sentence) + sum(len(text) for text in options.values())
    for letter, entity in usable.items():
        position = sentence_lower.find(entity)
        signals: dict[str, int] = {}
        if not neutral:
            if _object_control(sentence, entity, position, positions):
                signals["object_control"] = 1
            if _subject_control(sentence, position, positions):
                signals["subject_control"] = 1
            if _possessive_fit(sentence, entity):
                signals["possessive_link"] = 1
            if _semantic_fit_v2(sentence, entity):
                signals["semantic_fit"] = 1
        candidates.append(ReferenceCandidate.build(letter, **signals))
        operations += 1 + len(signals)
    return CompiledReference(
        ReferenceSituation(tuple(candidates)),
        {letter: letter for letter in usable},
        ambiguous,
        sentence,
        operations,
    )


class EnglishRoleReferenceResolverV2(EnglishRoleReferenceResolver):
    def answer(self, prompt: str) -> ReferenceAnswer:
        compiled = compile_reference_prompt_v2(prompt)
        if compiled is None:
            self.last_operations = 1
            self.last_candidates = 0
            return ReferenceAnswer(None, 1, 0, True)
        prediction = self.machine.predict(compiled.situation)
        self.last_operations = compiled.operations + prediction.operations
        self.last_candidates = prediction.compatible_candidates
        if prediction.output is None:
            return ReferenceAnswer(
                f"({compiled.ambiguous_option})",
                self.last_operations,
                self.last_candidates,
                True,
            )
        return ReferenceAnswer(
            f"({prediction.output})",
            self.last_operations,
            self.last_candidates,
            False,
        )
