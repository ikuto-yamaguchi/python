from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping


_AGENT = "<AGENT>"
_AGENT_PREFIX = "<AGENT"
_OBJECT = "<OBJECT>"
_VALUE = "<VALUE>"


def _normalise(text: str) -> str:
    return re.sub(r"\s+", "", text.strip().replace("?", "？").replace("!", "！"))


def _answer_value(text: str) -> str:
    value = text.strip().strip("。！？ ")
    return re.sub(r"^(?:答えは|実際は|場所は|原因は)", "", value)


def _replace_all(text: str, replacements: Mapping[str, str]) -> str:
    output = text
    for source in sorted(replacements, key=lambda item: (-len(item), item)):
        output = output.replace(source, replacements[source])
    return output


def _template_regex(template: str) -> re.Pattern[str]:
    pieces: list[str] = []
    cursor = 0
    token_re = re.compile(r"<(?:AGENT\d+|OBJECT|VALUE)>")
    for match in token_re.finditer(template):
        pieces.append(re.escape(template[cursor : match.start()]))
        token = match.group(0)
        if token == _OBJECT:
            pieces.append(r"(?P<object>.+?)")
        elif token == _VALUE:
            pieces.append(r"(?P<value>.+?)")
        else:
            index = token[len(_AGENT_PREFIX) : -1]
            pieces.append(fr"(?P<agent{index}>.+?)")
        cursor = match.end()
    pieces.append(re.escape(template[cursor:]))
    return re.compile("^" + "".join(pieces) + "$")


@dataclass(frozen=True)
class StateFact:
    value: str
    source_id: str
    event_id: int | None = None


@dataclass(frozen=True)
class EventRecord:
    text: str
    source_id: str
    object_name: str
    attribute: str
    previous_value: str | None
    new_value: str
    updated_agents: tuple[str, ...]


@dataclass(frozen=True)
class TransitionExample:
    text: str
    before_world: Mapping[tuple[str, str], str]
    after_world: Mapping[tuple[str, str], str]
    before_beliefs: Mapping[tuple[str, str, str], str]
    after_beliefs: Mapping[tuple[str, str, str], str]
    entity_kinds: Mapping[str, str]


@dataclass(frozen=True)
class FocusedQueryExample:
    focus: tuple[tuple[str, str], ...]
    question: str
    answer: str


@dataclass(frozen=True)
class EventProgram:
    attribute: str
    update_agent_slots: tuple[int, ...]
    object_from_focus: bool
    support: int


@dataclass(frozen=True)
class EventSchema:
    template: str
    program_id: int
    support: int


@dataclass(frozen=True)
class QueryProgram:
    mode: str
    attribute: str
    agent_from_focus: bool = False
    object_from_focus: bool = False


@dataclass(frozen=True)
class QuerySchema:
    template: str
    program_id: int
    support: int


@dataclass(frozen=True)
class CauseProgram:
    attribute: str
    object_from_focus: bool = False


@dataclass(frozen=True)
class CauseSchema:
    template: str
    program_id: int
    support: int
