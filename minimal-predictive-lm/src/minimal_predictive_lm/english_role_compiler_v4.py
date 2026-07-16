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
)
from .english_role_compiler_v2 import _semantic_fit_v2
from .english_role_compiler_v3 import (
    _PRONOUN_ALIASES,
    _causal_semantic_fit,
    _entity_position,
    _main_clause_possessor,
    _mentions_v3,
    _option_entity_v3,
    _recipient_control,
)
from .generic_reference_machine import ReferenceCandidate, ReferenceSituation


def _mentions_v4(sentence: str) -> tuple[str, ...]:
    output = [item[:-2] if item.endswith("'s") else item for item in _mentions_v3(sentence)]
    lower = _normalise(sentence)
    for match in re.finditer(r"\b(?:his|her|their)\s+([a-z][a-z'-]*)", lower):
        noun = match.group(1).removesuffix("'s")
        if noun not in output:
            output.append(noun)
    return tuple(dict.fromkeys(output))


def _option_entity_v4(option: str, mentions: tuple[str, ...]) -> str | None:
    entity = _option_entity_v3(option, mentions)
    if entity is not None:
        return entity
    lower = _normalise(option)
    for canonical, aliases in _PRONOUN_ALIASES.items():
        if any(re.search(rf"\b{re.escape(alias)}\b", lower) for alias in aliases):
            return canonical
    return None


def _complement_role(sentence: str) -> str | None:
    lower = _normalise(sentence)
    pronoun = r"(?:he|she|they)"
    # Recipient-oriented directives, permissions, diagnoses and obligations.
    object_patterns = (
        rf"\b(?:informed|warned) .+? that {pronoun} (?:would need to|needed to|should|must|had to|could pay)",
        rf"\btold .+? that {pronoun} (?:could pay|had cancer|was diagnosed|needed to get|should|must)",
        rf"\b(?:physician|doctor|surgeon|nurse|therapist) told .+? that {pronoun} had ",
        rf"\bhelped {pronoun} to\b",
    )
    if any(re.search(pattern, lower) for pattern in object_patterns):
        return "object"
    # Speaker-oriented reports and disclosures.
    subject_patterns = (
        rf"\bdisclosed to .+? that {pronoun} ",
        rf"\btold .+? that {pronoun} (?:took|liked|like|could not|would not|had completed|completed|had a history)",
        rf"\btells .+? that {pronoun} (?:like|likes)",
    )
    if any(re.search(pattern, lower) for pattern in subject_patterns):
        return "subject"
    return None


def _my_subject_possession(sentence: str, entity: str, position: int, positions: list[int]) -> bool:
    lower = _normalise(sentence)
    if position != min(positions):
        return False
    return bool(
        re.match(r"^my\s+[a-z][a-z'-]*\s+.+?\b(?:his|her)\s+[a-z][a-z'-]*", lower)
    )


def _helped_recipient(sentence: str, position: int, positions: list[int]) -> bool:
    lower = _normalise(sentence)
    return position == max(positions) and bool(
        re.search(r"\band helped (?:him|her|them) to\b", lower)
    )


def compile_reference_prompt_v4(prompt: str) -> CompiledReference | None:
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
    mentions = _mentions_v4(sentence)
    usable = {
        letter: entity
        for letter, text in options.items()
        if letter != ambiguous
        and (entity := _option_entity_v4(text, mentions)) is not None
    }
    if len(usable) < 2:
        return None
    positions = [_entity_position(sentence, entity) for entity in usable.values()]
    positions = [position for position in positions if position >= 0]
    if len(positions) < 2:
        return None
    neutral = _is_neutral_ambiguity(sentence)
    complement = _complement_role(sentence)
    candidates: list[ReferenceCandidate] = []
    operations = len(sentence) + sum(len(text) for text in options.values())
    for letter, entity in usable.items():
        position = _entity_position(sentence, entity)
        signals: dict[str, int] = {}
        if not neutral:
            object_role = position == max(positions)
            subject_role = position == min(positions)
            if (
                _object_control(sentence, entity, position, positions)
                or _recipient_control(sentence, entity, position, positions)
                or _helped_recipient(sentence, position, positions)
                or (complement == "object" and object_role)
            ):
                signals["object_control"] = 1
            if complement == "subject" and subject_role:
                signals["subject_control"] = 1
            possessive = _possessive_fit(sentence, entity) or _my_subject_possession(
                sentence, entity, position, positions
            )
            # Main-clause possessors are reliable only for singular his/her; plural
            # 'their' remains ambiguous unless another cue resolves it.
            if not possessive and not re.search(r"\btheir\b", _normalise(sentence)):
                possessive = _main_clause_possessor(sentence, entity)
            if possessive:
                signals["possessive_link"] = 1
            causal = _causal_semantic_fit(sentence, entity, position, positions)
            semantic = causal or (
                not re.search(r"\bbetter understood\b", _normalise(sentence))
                and _semantic_fit_v2(sentence, entity)
            )
            if semantic:
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


class EnglishRoleReferenceResolverV4(EnglishRoleReferenceResolver):
    def answer(self, prompt: str) -> ReferenceAnswer:
        compiled = compile_reference_prompt_v4(prompt)
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
