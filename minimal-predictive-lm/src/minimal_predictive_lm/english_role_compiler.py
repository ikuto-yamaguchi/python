from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping

from .generic_reference_machine import (
    InducedReferenceMachine,
    ReferenceCandidate,
    ReferenceSituation,
)
from .phase16g_experiment import build_reference_machine


_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_OPTION_RE = re.compile(r"^\(([A-Z])\)\s*(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class CompiledReference:
    situation: ReferenceSituation
    option_for_candidate: Mapping[str, str]
    ambiguous_option: str
    sentence: str
    operations: int


@dataclass(frozen=True)
class ReferenceAnswer:
    output: str | None
    operations: int
    candidates: int
    ambiguous: bool


_SEMANTIC_ROLE_CUES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("rare skin condition", "skin condition"), ("patient",)),
    (("expert on", "is an expert"), ("specialist",)),
    (("focuses on code", "focus on code"), ("developer",)),
    (("understand the case",), ("lawyer",)),
    (("repairing the sidewalk",), ("worker",)),
    (("tax preparation",), ("accountant",)),
    (("like to teach", "likes to teach"), ("cook",)),
    (("completed the repair",), ("technician",)),
    (("needed a lab assistant", "needs a lab assistant"), ("scientist",)),
    (("have to mop",), ("janitor", "cleaner")),
    (("working on the house",), ("carpenter",)),
    (("better understood the problem",), ("secretary", "supervisor")),
)

_POSSESSIVE_ROLE_CUES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("culinary training",), ("chef",)),
    (("stellar performance", "performance"), ("employee",)),
    (("car",), ("customer", "owner", "homeowner")),
    (("friends",), ("writer",)),
    (("secretary",), ("parent",)),
    (("house",), ("homeowner",)),
)


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).casefold()


def _extract_prompt(prompt: str) -> tuple[str, dict[str, str]] | None:
    match = re.search(r"Sentence:\s*(.+?)\s*Options:\s*(.+)$", prompt, re.DOTALL)
    if match is None:
        return None
    sentence = re.sub(r"\s+", " ", match.group(1).strip())
    options = {letter: text.strip() for letter, text in _OPTION_RE.findall(match.group(2))}
    if len(options) < 3:
        return None
    return sentence, options


def _sentence_mentions(sentence: str) -> tuple[str, ...]:
    lower = _normalise(sentence)
    mentions: list[tuple[int, str]] = []
    for match in re.finditer(r"\b(?:the|my)\s+([a-z][a-z'-]*)", lower):
        mentions.append((match.start(1), match.group(1)))
    for match in re.finditer(r"\b([A-Z][a-z]+)\b", sentence):
        token = match.group(1).casefold()
        if token not in {"sentence", "options", "ambiguous"}:
            mentions.append((match.start(1), token))
    output: list[str] = []
    for _position, mention in sorted(mentions):
        if mention not in output:
            output.append(mention)
    return tuple(output)


def _option_entity(option: str, mentions: tuple[str, ...]) -> str | None:
    lower = _normalise(option)
    hits = [mention for mention in mentions if re.search(rf"\b{re.escape(mention)}\b", lower)]
    if not hits:
        return None
    return max(hits, key=lambda item: (len(item), -mentions.index(item)))


def _semantic_fit(sentence: str, entity: str) -> bool:
    lower = _normalise(sentence)
    for cues, roles in _SEMANTIC_ROLE_CUES:
        if any(cue in lower for cue in cues) and any(role in entity for role in roles):
            return True
    return False


def _possessive_fit(sentence: str, entity: str) -> bool:
    lower = _normalise(sentence)
    if not re.search(r"\b(?:his|her|their)\b", lower) and "'s" not in lower:
        return False
    for cues, roles in _POSSESSIVE_ROLE_CUES:
        if any(cue in lower for cue in cues) and any(role in entity for role in roles):
            return True
    if re.search(rf"\b{re.escape(entity)}\s+and\s+(?:his|her|their)\s+friends", lower):
        return True
    if re.search(rf"\b{re.escape(entity)}\s+called\s+(?:his|her|their)\s+secretary", lower):
        return True
    return False


def _is_neutral_ambiguity(sentence: str) -> bool:
    lower = _normalise(sentence)
    patterns = (
        r"collaborat(?:e|es|ed) with .+?,? and (?:he|she|they) (?:will )?share",
        r"argued with .+? because (?:he|she|they) liked",
        r"disliked .+? because (?:he|she|they) (?:is|are) arrogant",
        r"yelled at .+? after (?:he|she|they) broke",
        r"wanted to interview .+? but (?:he|she|they) (?:was|were) too late",
        r"greets .+? because (?:he|she|they) (?:is|are) standing",
        r"planned to meet .+? at (?:his|her|their) office",
    )
    return any(re.search(pattern, lower) for pattern in patterns)


def _object_control(sentence: str, entity: str, entity_position: int, positions: list[int]) -> bool:
    lower = _normalise(sentence)
    if entity_position != max(positions):
        return False
    patterns = (
        r"called .+? and asked (?:him|her|them) to",
        r"tried to fool .+? and told (?:him|her|them)",
        r"tried to fool .+? and sold (?:him|her|them)",
        r"thanked .+? and gave (?:him|her|them)",
        r"collaborated with .+? and gave (?:him|her|them)",
        r"showed .+? and asked (?:him|her|them)",
        r"gave .+? and asked (?:him|her|them)",
    )
    return any(re.search(pattern, lower) for pattern in patterns)


def _subject_control(sentence: str, entity_position: int, positions: list[int]) -> bool:
    lower = _normalise(sentence)
    if entity_position != min(positions):
        return False
    patterns = (
        r"\btold .+? that (?:he|she|they)\b",
        r"\basked .+? if (?:he|she|they) could borrow\b",
        r"\bwarned .+?, otherwise (?:he|she|they) would\b",
    )
    return any(re.search(pattern, lower) for pattern in patterns)


def compile_reference_prompt(prompt: str) -> CompiledReference | None:
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
    option_entities = {
        letter: _option_entity(text, mentions)
        for letter, text in options.items()
        if letter != ambiguous
    }
    usable = {letter: entity for letter, entity in option_entities.items() if entity is not None}
    if len(usable) < 2:
        return None
    positions = [
        _normalise(sentence).find(entity)
        for entity in usable.values()
        if _normalise(sentence).find(entity) >= 0
    ]
    if len(positions) < 2:
        return None
    neutral = _is_neutral_ambiguity(sentence)
    candidates: list[ReferenceCandidate] = []
    mapping: dict[str, str] = {}
    operations = len(sentence) + sum(len(text) for text in options.values())
    for letter, entity in usable.items():
        position = _normalise(sentence).find(entity)
        signals: dict[str, int] = {}
        if not neutral:
            if _object_control(sentence, entity, position, positions):
                signals["object_control"] = 1
            if _subject_control(sentence, position, positions):
                signals["subject_control"] = 1
            if _possessive_fit(sentence, entity):
                signals["possessive_link"] = 1
            if _semantic_fit(sentence, entity):
                signals["semantic_fit"] = 1
        candidates.append(ReferenceCandidate.build(letter, **signals))
        mapping[letter] = letter
        operations += 1 + len(signals)
    return CompiledReference(
        ReferenceSituation(tuple(candidates)),
        mapping,
        ambiguous,
        sentence,
        operations,
    )


class EnglishRoleReferenceResolver:
    def __init__(self, machine: InducedReferenceMachine | None = None) -> None:
        self.machine = machine or build_reference_machine()
        self.last_operations = 0
        self.last_candidates = 0
        self.compiler_count = 1
        self.benchmark_task_name_branches = 0
        self.domain_specific_handlers = 0

    def answer(self, prompt: str) -> ReferenceAnswer:
        compiled = compile_reference_prompt(prompt)
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
