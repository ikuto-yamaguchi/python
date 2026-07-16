from __future__ import annotations

import re

from .english_role_compiler import (
    CompiledReference,
    EnglishRoleReferenceResolver,
    ReferenceAnswer,
    _extract_prompt,
    _is_neutral_ambiguity,
    _normalise,
    _object_control,
    _possessive_fit,
    _sentence_mentions,
)
from .english_role_compiler_v2 import _semantic_fit_v2
from .generic_reference_machine import ReferenceCandidate, ReferenceSituation


_PRONOUN_ALIASES = {
    "we": ("we", "us", "our", "ours"),
    "i": ("i", "me", "my", "mine"),
}


def _mentions_v3(sentence: str) -> tuple[str, ...]:
    output = list(_sentence_mentions(sentence))
    lower = _normalise(sentence)
    for canonical, aliases in _PRONOUN_ALIASES.items():
        if any(re.search(rf"\b{re.escape(alias)}\b", lower) for alias in aliases):
            if canonical not in output:
                output.append(canonical)
    return tuple(output)


def _option_entity_v3(option: str, mentions: tuple[str, ...]) -> str | None:
    lower = _normalise(option)
    hits: list[str] = []
    for mention in mentions:
        aliases = _PRONOUN_ALIASES.get(mention, (mention,))
        if any(re.search(rf"\b{re.escape(alias)}\b", lower) for alias in aliases):
            hits.append(mention)
    if not hits:
        return None
    return max(hits, key=lambda item: (len(item), -mentions.index(item)))


def _entity_position(sentence: str, entity: str) -> int:
    lower = _normalise(sentence)
    aliases = _PRONOUN_ALIASES.get(entity, (entity,))
    positions = [
        match.start()
        for alias in aliases
        for match in re.finditer(rf"\b{re.escape(alias)}\b", lower)
    ]
    return min(positions) if positions else -1


def _main_clause_possessor(sentence: str, entity: str) -> bool:
    lower = _normalise(sentence)
    position = _entity_position(sentence, entity)
    if position < 0 or not re.search(r"\b(?:his|her|their)\b", lower):
        return False
    # A fronted adjunct followed by a comma leaves the following participant as
    # the main-clause subject and therefore the default possessor.
    comma = lower.find(",")
    if comma >= 0 and position > comma:
        tail = lower[position + len(entity) :]
        if re.search(r"\b(?:went|goes|will go|returned|returns|walked|walks|drove|drives|headed|heads)\b", tail):
            return True
    return False


def _recipient_control(sentence: str, entity: str, position: int, positions: list[int]) -> bool:
    lower = _normalise(sentence)
    if position != max(positions):
        return False
    patterns = (
        r"\basked .+? if (?:he|she|they) could (?:send|give|provide|share|show|deliver|return|forward)",
        r"\btold .+? that (?:he|she|they) (?:should|must|needed to|ought to|had to)",
        r"\bcalled .+? and told (?:him|her|them)\b",
        r"\bhanded .+? .+? because (?:he|she|they) asked for\b",
    )
    return any(re.search(pattern, lower) for pattern in patterns)


def _speaker_control(sentence: str, entity: str, position: int, positions: list[int]) -> bool:
    lower = _normalise(sentence)
    if position != min(positions):
        return False
    patterns = (
        r"\btell(?:s|ing|ed)? .+? that (?:he|she|they) (?:like|likes|liked|had|has|was|were|could not|would not|completed|understood)",
        r"\basked .+? if (?:he|she|they) could (?:borrow|use|take|have|keep)",
        r"\bwarned .+?, otherwise (?:he|she|they) would\b",
    )
    return any(re.search(pattern, lower) for pattern in patterns)


def _causal_semantic_fit(sentence: str, entity: str, position: int, positions: list[int]) -> bool:
    lower = _normalise(sentence)
    scope = lower[lower.rfind(" because ") + 9 :] if " because " in lower else lower
    if re.search(r"\b(?:felt|was) (?:gravely )?(?:ill|sick|injured|unwell)\b", scope):
        return "patient" in entity
    if re.search(r"\b(?:better understood|understood|knew|upholds? the peace|was qualified|had expertise)\b", scope):
        return position == min(positions)
    return False


def compile_reference_prompt_v3(prompt: str) -> CompiledReference | None:
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
    mentions = _mentions_v3(sentence)
    usable = {
        letter: entity
        for letter, text in options.items()
        if letter != ambiguous
        and (entity := _option_entity_v3(text, mentions)) is not None
    }
    if len(usable) < 2:
        return None
    positions = [_entity_position(sentence, entity) for entity in usable.values()]
    positions = [position for position in positions if position >= 0]
    if len(positions) < 2:
        return None
    neutral = _is_neutral_ambiguity(sentence)
    candidates: list[ReferenceCandidate] = []
    operations = len(sentence) + sum(len(text) for text in options.values())
    for letter, entity in usable.items():
        position = _entity_position(sentence, entity)
        signals: dict[str, int] = {}
        if not neutral:
            if _object_control(sentence, entity, position, positions) or _recipient_control(
                sentence, entity, position, positions
            ):
                signals["object_control"] = 1
            if _speaker_control(sentence, entity, position, positions):
                signals["subject_control"] = 1
            if _possessive_fit(sentence, entity) or _main_clause_possessor(
                sentence, entity
            ):
                signals["possessive_link"] = 1
            if _semantic_fit_v2(sentence, entity) or _causal_semantic_fit(
                sentence, entity, position, positions
            ):
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


class EnglishRoleReferenceResolverV3(EnglishRoleReferenceResolver):
    def answer(self, prompt: str) -> ReferenceAnswer:
        compiled = compile_reference_prompt_v3(prompt)
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
