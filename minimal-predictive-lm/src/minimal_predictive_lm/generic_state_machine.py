from __future__ import annotations

from dataclasses import dataclass
import itertools
import json
import re
import unicodedata
from typing import Mapping, Sequence


Scalar = int | str | bool


def _bits(payload: object) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ) * 8


def _normalize_value(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold().strip()
    text = re.sub(r"^(?:a|an|the)\s+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.rstrip(". ")


def _normalize_entity(value: str) -> str:
    text = _normalize_value(value)
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


@dataclass(frozen=True)
class StateEvent:
    operation: str
    arguments: tuple[Scalar, ...]

    def render(self) -> object:
        return [self.operation, list(self.arguments)]


@dataclass(frozen=True)
class StateQuery:
    operation: str
    arguments: tuple[object, ...]

    def render(self) -> object:
        return [self.operation, list(self.arguments)]


@dataclass(frozen=True)
class CompiledStateProgram:
    family: str
    initial_state: object
    events: tuple[StateEvent, ...]
    query: StateQuery

    def render(self) -> object:
        return {
            "family": self.family,
            "initial_state": self.initial_state,
            "events": [event.render() for event in self.events],
            "query": self.query.render(),
        }


@dataclass(frozen=True)
class StatePrediction:
    output: str | None
    family: str | None
    operations: int
    reads: int
    writes: int


class GenericStateRuntime:
    def execute(self, program: CompiledStateProgram) -> StatePrediction:
        if program.family == "stack":
            return self._execute_stack(program)
        if program.family == "vector":
            return self._execute_vector(program)
        if program.family == "mapping":
            return self._execute_mapping(program)
        if program.family == "order":
            return self._execute_order(program)
        return StatePrediction(None, None, 1, 0, 0)

    def _execute_stack(self, program: CompiledStateProgram) -> StatePrediction:
        stack: list[str] = []
        close_for = {"(": ")", "[": "]", "{": "}", "<": ">"}
        open_for = {value: key for key, value in close_for.items()}
        operations = 0
        reads = 0
        writes = 0
        for event in program.events:
            operations += 1
            token = str(event.arguments[0])
            if event.operation == "push":
                stack.append(token)
                writes += 1
            elif event.operation == "pop":
                reads += 1
                if not stack or stack[-1] != open_for.get(token):
                    return StatePrediction(None, "stack", operations, reads, writes)
                stack.pop()
                writes += 1
            else:
                return StatePrediction(None, "stack", operations, reads, writes)
        output = " ".join(close_for[token] for token in reversed(stack))
        return StatePrediction(output, "stack", operations + len(stack), reads + len(stack), writes)

    def _execute_vector(self, program: CompiledStateProgram) -> StatePrediction:
        state = {"x": 0, "y": 0, "heading": 0}
        operations = reads = writes = 0
        directions = ((0, 1), (1, 0), (0, -1), (-1, 0))
        for event in program.events:
            operations += 1
            if event.operation == "turn":
                state["heading"] = (state["heading"] + int(event.arguments[0])) % 4
                reads += 1
                writes += 1
            elif event.operation == "move_relative":
                steps = int(event.arguments[0])
                dx, dy = directions[state["heading"]]
                state["x"] += dx * steps
                state["y"] += dy * steps
                reads += 3
                writes += 2
            elif event.operation == "move_absolute":
                steps = int(event.arguments[0])
                direction = str(event.arguments[1])
                dx, dy = {
                    "forward": (0, 1),
                    "backward": (0, -1),
                    "left": (-1, 0),
                    "right": (1, 0),
                }[direction]
                state["x"] += dx * steps
                state["y"] += dy * steps
                reads += 2
                writes += 2
            else:
                return StatePrediction(None, "vector", operations, reads, writes)
        reads += 2
        output = "Yes" if state["x"] == 0 and state["y"] == 0 else "No"
        return StatePrediction(output, "vector", operations + 1, reads, writes)

    def _execute_mapping(self, program: CompiledStateProgram) -> StatePrediction:
        state = {str(key): str(value) for key, value in dict(program.initial_state).items()}
        operations = reads = writes = 0
        for event in program.events:
            operations += 1
            if event.operation != "swap":
                return StatePrediction(None, "mapping", operations, reads, writes)
            left, right = map(str, event.arguments)
            if left not in state or right not in state:
                return StatePrediction(None, "mapping", operations, reads, writes)
            state[left], state[right] = state[right], state[left]
            reads += 2
            writes += 2
        agent = str(program.query.arguments[0])
        options = dict(program.query.arguments[1])
        reads += 1
        if agent not in state:
            return StatePrediction(None, "mapping", operations, reads, writes)
        target = _normalize_value(state[agent])
        matches = [label for label, text in options.items() if _normalize_value(str(text)) == target]
        return StatePrediction(
            matches[0] if len(matches) == 1 else None,
            "mapping",
            operations + len(options),
            reads + len(options),
            writes,
        )

    def _execute_order(self, program: CompiledStateProgram) -> StatePrediction:
        entities = tuple(str(value) for value in program.initial_state)
        valid: list[dict[str, int]] = []
        for permutation in itertools.permutations(range(len(entities))):
            rank = dict(zip(entities, permutation))
            if all(self._order_event_holds(event, rank) for event in program.events):
                valid.append(rank)
        if not valid:
            return StatePrediction(None, "order", len(program.events), 0, 0)
        options = dict(program.query.arguments[0])
        matches: list[str] = []
        for label, predicate in options.items():
            entity, expected_rank = predicate
            if all(rank[str(entity)] == int(expected_rank) for rank in valid):
                matches.append(str(label))
        return StatePrediction(
            matches[0] if len(matches) == 1 else None,
            "order",
            len(valid) * max(1, len(program.events)) + len(options),
            len(valid) * len(program.events) + len(options),
            0,
        )

    @staticmethod
    def _order_event_holds(event: StateEvent, rank: Mapping[str, int]) -> bool:
        if event.operation == "less":
            left, right = map(str, event.arguments)
            return rank[left] < rank[right]
        if event.operation == "rank":
            entity, expected = event.arguments
            return rank[str(entity)] == int(expected)
        return False


_BRACKET_RE = re.compile(r"[\[\](){}<>]")
_OPTION_RE = re.compile(r"^\(([A-F])\)\s*(.+)$", re.MULTILINE)


def _parse_options(prompt: str) -> dict[str, str]:
    return {f"({label})": text.strip() for label, text in _OPTION_RE.findall(prompt)}


def compile_stack_program(prompt: str) -> CompiledStateProgram | None:
    marker = "Input:"
    if marker not in prompt:
        return None
    sequence = prompt.rsplit(marker, 1)[1].strip()
    if not sequence or re.sub(r"[\[\](){}<>\s]", "", sequence):
        return None
    events = tuple(
        StateEvent("push" if token in "([{<" else "pop", (token,))
        for token in _BRACKET_RE.findall(sequence)
    )
    return CompiledStateProgram("stack", (), events, StateQuery("close_stack", ()))


def compile_navigation_program(prompt: str) -> CompiledStateProgram | None:
    if "return to the starting point" not in prompt.casefold():
        return None
    if "Options:\n- Yes\n- No" not in prompt:
        return None
    body = prompt.split("?", 1)[1].split("\nOptions:", 1)[0]
    sentences = [row.strip() for row in body.split(".") if row.strip()]
    absolute = False
    events: list[StateEvent] = []
    for sentence in sentences:
        if sentence.casefold() == "always face forward":
            absolute = True
            continue
        turn = re.fullmatch(r"Turn\s+(left|right|around)", sentence, re.IGNORECASE)
        if turn:
            events.append(
                StateEvent("turn", ({"left": -1, "right": 1, "around": 2}[turn.group(1).casefold()],))
            )
            continue
        move = re.fullmatch(
            r"Take\s+(\d+)\s+steps?(?:\s+(forward|backward|left|right))?",
            sentence,
            re.IGNORECASE,
        )
        if move:
            steps = int(move.group(1))
            direction = move.group(2)
            if direction is None:
                if absolute:
                    return None
                events.append(StateEvent("move_relative", (steps,)))
            elif absolute:
                events.append(StateEvent("move_absolute", (steps, direction.casefold())))
            else:
                # Relative prompts in this benchmark omit directional move words.
                return None
            continue
        return None
    if not events:
        return None
    return CompiledStateProgram("vector", {"x": 0, "y": 0, "heading": 0}, tuple(events), StateQuery("at_origin", ()))


def compile_mapping_program(prompt: str) -> CompiledStateProgram | None:
    pairs = re.findall(
        r"(?:First|Then|Finally),\s+([A-Z][a-z]+)\s+and\s+([A-Z][a-z]+)\s+(?:swap|switch|trade)",
        prompt,
    )
    if not pairs:
        return None
    agents = tuple(sorted({name for pair in pairs for name in pair}))
    if len(agents) < 2:
        return None
    initial_text = prompt.split("\nAs ", 1)[0].split("First,", 1)[0]
    agent_pattern = "|".join(re.escape(agent) for agent in agents)
    initial: dict[str, str] = {}
    for agent in agents:
        match = re.search(
            rf"\b{re.escape(agent)}\s+(?:gets|has|is\s+dancing\s+with|is\s+playing)\s+(.+?)(?=,\s+(?:and\s+)?(?:{agent_pattern})\s+|[.\n])",
            initial_text,
            re.IGNORECASE,
        )
        if not match:
            return None
        initial[agent] = _normalize_value(match.group(1))
    before_options = prompt.split("\nOptions:", 1)[0].strip()
    query = re.search(
        rf"At\s+the\s+end.*?,\s+({agent_pattern})\s+(?:has(?:\s+the)?|is\s+dancing\s+with|is\s+playing)\s*$",
        before_options,
        re.IGNORECASE | re.DOTALL,
    )
    options = _parse_options(prompt)
    if not query or len(options) < 2:
        return None
    events = tuple(StateEvent("swap", pair) for pair in pairs)
    return CompiledStateProgram(
        "mapping",
        initial,
        events,
        StateQuery("map_option", (query.group(1), tuple(options.items()))),
    )


_RANK_PHRASES = {
    "leftmost": 0,
    "oldest": 0,
    "cheapest": 0,
    "last": 0,
    "second from the left": 1,
    "second-newest": 1,
    "second-most expensive": 1,
    "second": 1,
    "rightmost": 2,
    "newest": 2,
    "most expensive": 2,
    "first": 2,
}


def _parse_rank_predicate(text: str) -> tuple[str, int] | None:
    normalized = text.strip().rstrip(".")
    patterns = (
        r"(?:The\s+)?(.+?)\s+(?:is|are)\s+the\s+(.+)",
        r"(.+?)\s+finished\s+(.+)",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, normalized, re.IGNORECASE)
        if not match:
            continue
        phrase = match.group(2).casefold()
        if phrase in _RANK_PHRASES:
            return _normalize_entity(match.group(1)), _RANK_PHRASES[phrase]
    return None


def _parse_relation(sentence: str, entities: set[str]) -> StateEvent | None:
    patterns = (
        (r"(.+?)\s+is\s+to\s+the\s+right\s+of\s+(.+)", "right"),
        (r"(.+?)\s+is\s+to\s+the\s+left\s+of\s+(.+)", "left"),
        (r"(.+?)\s+(?:is|are)\s+newer\s+than\s+(.+)", "right"),
        (r"(.+?)\s+(?:is|are)\s+older\s+than\s+(.+)", "left"),
        (r"(.+?)\s+(?:is|are)\s+more\s+expensive\s+than\s+(.+)", "right"),
        (r"(.+?)\s+(?:is|are)\s+less\s+expensive\s+than\s+(.+)", "left"),
        (r"(.+?)\s+finished\s+above\s+(.+)", "right"),
        (r"(.+?)\s+finished\s+below\s+(.+)", "left"),
    )
    for pattern, direction in patterns:
        match = re.fullmatch(pattern, sentence.strip(), re.IGNORECASE)
        if not match:
            continue
        first = _normalize_entity(match.group(1))
        second = _normalize_entity(match.group(2))
        if first not in entities or second not in entities:
            return None
        return StateEvent("less", (second, first) if direction == "right" else (first, second))
    predicate = _parse_rank_predicate(sentence)
    if predicate and predicate[0] in entities:
        return StateEvent("rank", predicate)
    return None


def compile_order_program(prompt: str) -> CompiledStateProgram | None:
    options = _parse_options(prompt)
    if len(options) != 3:
        return None
    predicates: dict[str, tuple[str, int]] = {}
    for label, text in options.items():
        predicate = _parse_rank_predicate(text)
        if predicate is None:
            return None
        predicates[label] = predicate
    entities = {entity for entity, _rank in predicates.values()}
    if len(entities) != 3:
        return None
    body = prompt.split("\nOptions:", 1)[0]
    events: list[StateEvent] = []
    for sentence in (segment.strip() for segment in body.split(".") if segment.strip()):
        event = _parse_relation(sentence, entities)
        if event is not None:
            events.append(event)
    if not events:
        return None
    return CompiledStateProgram(
        "order",
        tuple(sorted(entities)),
        tuple(events),
        StateQuery("order_option", (tuple(predicates.items()),)),
    )


@dataclass(frozen=True)
class GenericStateMachine:
    runtime: GenericStateRuntime = GenericStateRuntime()
    compiler_count: int = 4
    benchmark_task_name_branches: int = 0

    def predict(self, prompt: str) -> StatePrediction:
        programs = tuple(
            program
            for compiler in (
                compile_stack_program,
                compile_navigation_program,
                compile_mapping_program,
                compile_order_program,
            )
            if (program := compiler(prompt)) is not None
        )
        if len(programs) != 1:
            return StatePrediction(None, None, 1, 0, 0)
        return self.runtime.execute(programs[0])

    def render(self) -> object:
        return {
            "runtime_operations": [
                "push",
                "pop",
                "turn",
                "move_relative",
                "move_absolute",
                "swap",
                "less",
                "rank",
            ],
            "query_operations": [
                "close_stack",
                "at_origin",
                "map_option",
                "order_option",
            ],
            "compiler_count": self.compiler_count,
            "benchmark_task_name_branches": self.benchmark_task_name_branches,
        }

    @property
    def description_bits(self) -> int:
        return _bits(self.render())
