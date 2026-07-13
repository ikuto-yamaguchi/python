from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import permutations
import json
from pathlib import Path
import random
import re
import unicodedata
from typing import Iterable, Mapping, Sequence

ENTITIES = ("アキ", "ボブ", "チカ", "ダイ", "エリ", "フミ")
ACTIONS = ("渡す", "受ける", "写す", "移す")
ACTION_FORWARD = {"渡す": True, "受ける": False, "写す": True, "移す": False}

TRUE_SEQUENCE = {"続いて": "LR", "先立ち": "RL"}
TRUE_CONDITION = {"同じなら": "EQ", "違うなら": "NEQ"}
TRUE_NEGATION = {"せず": "SKIP"}
TRUE_REFERENCE = {"その人": "DST", "相手": "SRC"}

REPETITIONS = 9
FLIPS = 1
PUNCTUATION = "。、，,！？!?"

State = tuple[int, ...]
Context = tuple[int, int] | None


class NonIdentifiableRecursiveDiscourseError(ValueError):
    pass


@dataclass(frozen=True)
class EventNode:
    left: str
    right: str
    action: str


@dataclass(frozen=True)
class UnaryNode:
    label: str
    child: object


@dataclass(frozen=True)
class BinaryNode:
    label: str
    left: object
    right: object


@dataclass(frozen=True)
class ConditionalNode:
    label: str
    first_entity: str
    second_entity: str
    yes: object
    no: object


Node = EventNode | UnaryNode | BinaryNode | ConditionalNode


@dataclass(frozen=True)
class Observation:
    sentence: str
    before: State
    after: State

    @property
    def text(self) -> str:
        return normalize(self.sentence)


@dataclass(frozen=True)
class RecursiveDiscourseModel:
    sequence: tuple[tuple[str, str], ...]
    condition: tuple[tuple[str, str], ...]
    negation: tuple[tuple[str, str], ...]
    reference: tuple[tuple[str, str], ...]

    @property
    def description_bits(self) -> int:
        payload = {
            "sequence": self.sequence,
            "condition": self.condition,
            "negation": self.negation,
            "reference": self.reference,
            "entities": ENTITIES,
            "actions": ACTION_FORWARD,
        }
        return len(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ) * 8

    def predict(self, sentence: str, before: Sequence[int]) -> State | None:
        try:
            node = parse_program(sentence)
            state, _ = execute(node, tuple(before), self, None)
            return state
        except (KeyError, ValueError):
            return None


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    for character in PUNCTUATION:
        text = text.replace(character, "")
    return "".join(text.split())


def render(node: Node) -> str:
    if isinstance(node, EventNode):
        return f"{node.left}が{node.right}に{node.action}"
    if isinstance(node, UnaryNode):
        return f"{node.label}【{render(node.child)}】"
    if isinstance(node, BinaryNode):
        return f"{node.label}【{render(node.left)}】【{render(node.right)}】"
    if isinstance(node, ConditionalNode):
        return (
            f"{node.label}({node.first_entity}と{node.second_entity})"
            f"【{render(node.yes)}】【{render(node.no)}】"
        )
    raise TypeError(node)


def punctuate(text: str, index: int) -> str:
    text = text.replace("】【。", "。】【" if index % 2 == 0 else "，】【")
    return text + ("。" if index % 3 else "！")


def _top_level_blocks(text: str, start: int) -> tuple[str, ...]:
    blocks: list[str] = []
    index = start
    while index < len(text):
        if text[index] != "【":
            raise ValueError("expected opening bracket")
        depth = 1
        end = index + 1
        while end < len(text) and depth:
            if text[end] == "【":
                depth += 1
            elif text[end] == "】":
                depth -= 1
            end += 1
        if depth:
            raise ValueError("unbalanced recursive brackets")
        blocks.append(text[index + 1 : end - 1])
        index = end
    return tuple(blocks)


def _parse_event(text: str) -> EventNode:
    for action in ACTIONS:
        if not text.endswith(action):
            continue
        body = text[: -len(action)]
        if "が" not in body or "に" not in body:
            continue
        left, residual = body.split("が", 1)
        right, tail = residual.split("に", 1)
        if left and right and not tail:
            return EventNode(left, right, action)
    raise ValueError("not an event")


def parse_program(text: str) -> Node:
    text = normalize(text)
    if "【" not in text:
        return _parse_event(text)

    first_bracket = text.index("【")
    prefix = text[:first_bracket]
    blocks = _top_level_blocks(text, first_bracket)

    condition = re.fullmatch(r"(.+?)\((.+?)と(.+?)\)", prefix)
    if condition is not None:
        if len(blocks) != 2:
            raise ValueError("condition arity")
        return ConditionalNode(
            condition.group(1),
            condition.group(2),
            condition.group(3),
            parse_program(blocks[0]),
            parse_program(blocks[1]),
        )

    if len(blocks) == 2:
        return BinaryNode(prefix, parse_program(blocks[0]), parse_program(blocks[1]))
    if len(blocks) == 1:
        return UnaryNode(prefix, parse_program(blocks[0]))
    raise ValueError("unknown recursive arity")


def _resolve_argument(
    token: str,
    model: RecursiveDiscourseModel,
    context: Context,
) -> int:
    if token in ENTITIES:
        return ENTITIES.index(token)
    role = dict(model.reference).get(token)
    if role is None or context is None:
        raise ValueError("unresolved discourse reference")
    return context[0] if role == "SRC" else context[1]


def _apply(state: State, event: tuple[int, int]) -> State:
    output = list(state)
    output[event[1]] = state[event[0]]
    return tuple(output)


def execute(
    node: Node,
    state: State,
    model: RecursiveDiscourseModel,
    context: Context,
) -> tuple[State, Context]:
    if isinstance(node, EventNode):
        left = _resolve_argument(node.left, model, context)
        right = _resolve_argument(node.right, model, context)
        if left == right:
            raise ValueError("self event")
        event = (
            (left, right)
            if ACTION_FORWARD[node.action]
            else (right, left)
        )
        return _apply(state, event), event

    if isinstance(node, UnaryNode):
        operator = dict(model.negation).get(node.label)
        if operator == "SKIP":
            return state, context
        if operator == "EXEC":
            return execute(node.child, state, model, context)
        raise ValueError("unknown unary operator")

    if isinstance(node, BinaryNode):
        operator = dict(model.sequence).get(node.label)
        if operator == "LR":
            middle, next_context = execute(node.left, state, model, context)
            return execute(node.right, middle, model, next_context)
        if operator == "RL":
            middle, next_context = execute(node.right, state, model, context)
            return execute(node.left, middle, model, next_context)
        raise ValueError("unknown binary operator")

    if isinstance(node, ConditionalNode):
        relation = dict(model.condition).get(node.label)
        first = ENTITIES.index(node.first_entity)
        second = ENTITIES.index(node.second_entity)
        test = state[first] == state[second]
        if relation == "NEQ":
            test = not test
        elif relation != "EQ":
            raise ValueError("unknown condition")
        return execute(node.yes if test else node.no, state, model, context)

    raise TypeError(node)


def _true_model() -> RecursiveDiscourseModel:
    return RecursiveDiscourseModel(
        tuple(sorted(TRUE_SEQUENCE.items())),
        tuple(sorted(TRUE_CONDITION.items())),
        tuple(sorted(TRUE_NEGATION.items())),
        tuple(sorted(TRUE_REFERENCE.items())),
    )


def event(left: str, right: str, action: str) -> EventNode:
    return EventNode(left, right, action)


def sequence(label: str, left: Node, right: Node) -> BinaryNode:
    return BinaryNode(label, left, right)


def condition(
    label: str,
    first: str,
    second: str,
    yes: Node,
    no: Node,
) -> ConditionalNode:
    return ConditionalNode(label, first, second, yes, no)


def negate(child: Node) -> UnaryNode:
    return UnaryNode("せず", child)


TRAINING_PROGRAMS: tuple[Node, ...] = (
    sequence(
        "続いて",
        event("アキ", "ボブ", "渡す"),
        sequence(
            "続いて",
            event("その人", "チカ", "写す"),
            event("相手", "ダイ", "受ける"),
        ),
    ),
    sequence(
        "先立ち",
        sequence(
            "続いて",
            event("その人", "エリ", "移す"),
            event("相手", "フミ", "写す"),
        ),
        event("アキ", "ボブ", "渡す"),
    ),
    condition(
        "同じなら",
        "アキ",
        "ボブ",
        sequence(
            "続いて",
            event("チカ", "ダイ", "渡す"),
            event("その人", "エリ", "写す"),
        ),
        sequence(
            "先立ち",
            event("その人", "フミ", "受ける"),
            event("チカ", "ダイ", "移す"),
        ),
    ),
    condition(
        "違うなら",
        "チカ",
        "ダイ",
        negate(
            sequence(
                "続いて",
                event("アキ", "ボブ", "渡す"),
                event("その人", "エリ", "写す"),
            )
        ),
        sequence(
            "続いて",
            event("フミ", "アキ", "受ける"),
            event("その人", "ボブ", "移す"),
        ),
    ),
    sequence(
        "続いて",
        event("アキ", "ボブ", "渡す"),
        condition(
            "違うなら",
            "チカ",
            "ダイ",
            sequence(
                "先立ち",
                event("その人", "エリ", "写す"),
                event("ボブ", "チカ", "移す"),
            ),
            negate(event("相手", "フミ", "受ける")),
        ),
    ),
    sequence(
        "先立ち",
        condition(
            "同じなら",
            "アキ",
            "チカ",
            event("その人", "ダイ", "渡す"),
            sequence(
                "続いて",
                event("その人", "エリ", "受ける"),
                event("相手", "フミ", "写す"),
            ),
        ),
        event("アキ", "ボブ", "移す"),
    ),
    negate(
        sequence(
            "続いて",
            event("アキ", "ボブ", "渡す"),
            sequence(
                "先立ち",
                event("その人", "チカ", "写す"),
                event("相手", "ダイ", "移す"),
            ),
        )
    ),
    sequence(
        "続いて",
        event("アキ", "ボブ", "写す"),
        condition(
            "同じなら",
            "ボブ",
            "チカ",
            negate(
                sequence(
                    "先立ち",
                    event("その人", "ダイ", "移す"),
                    event("エリ", "フミ", "渡す"),
                )
            ),
            sequence(
                "続いて",
                event("相手", "ダイ", "受ける"),
                event("その人", "エリ", "写す"),
            ),
        ),
    ),
)


HELDOUT_PROGRAMS: tuple[Node, ...] = (
    sequence(
        "続いて",
        event("アキ", "ボブ", "渡す"),
        condition(
            "同じなら",
            "チカ",
            "ダイ",
            sequence(
                "先立ち",
                event("その人", "エリ", "写す"),
                event("ボブ", "チカ", "移す"),
            ),
            negate(
                sequence(
                    "続いて",
                    event("相手", "フミ", "受ける"),
                    event("その人", "エリ", "写す"),
                )
            ),
        ),
    ),
    sequence(
        "先立ち",
        condition(
            "違うなら",
            "アキ",
            "エリ",
            sequence(
                "続いて",
                event("その人", "チカ", "写す"),
                event("相手", "ダイ", "移す"),
            ),
            negate(event("その人", "フミ", "受ける")),
        ),
        event("アキ", "ボブ", "渡す"),
    ),
    condition(
        "違うなら",
        "アキ",
        "ボブ",
        sequence(
            "先立ち",
            event("その人", "エリ", "受ける"),
            sequence(
                "続いて",
                event("チカ", "ダイ", "渡す"),
                event("その人", "フミ", "写す"),
            ),
        ),
        sequence(
            "続いて",
            event("エリ", "フミ", "移す"),
            event("その人", "アキ", "写す"),
        ),
    ),
    sequence(
        "続いて",
        event("チカ", "ダイ", "写す"),
        negate(
            condition(
                "同じなら",
                "アキ",
                "ボブ",
                sequence(
                    "続いて",
                    event("その人", "エリ", "渡す"),
                    event("相手", "フミ", "受ける"),
                ),
                sequence(
                    "先立ち",
                    event("相手", "エリ", "移す"),
                    event("その人", "フミ", "写す"),
                ),
            )
        ),
    ),
    condition(
        "同じなら",
        "アキ",
        "チカ",
        sequence(
            "続いて",
            event("ダイ", "エリ", "渡す"),
            condition(
                "違うなら",
                "ボブ",
                "フミ",
                event("その人", "アキ", "写す"),
                event("相手", "チカ", "受ける"),
            ),
        ),
        sequence(
            "先立ち",
            event("その人", "ボブ", "移す"),
            event("ダイ", "エリ", "写す"),
        ),
    ),
    sequence(
        "続いて",
        event("アキ", "エリ", "移す"),
        condition(
            "同じなら",
            "ボブ",
            "ダイ",
            sequence(
                "先立ち",
                event("その人", "フミ", "受ける"),
                event("チカ", "ボブ", "写す"),
            ),
            sequence(
                "続いて",
                event("相手", "チカ", "渡す"),
                event("その人", "フミ", "移す"),
            ),
        ),
    ),
)


def _rename(node: Node, mapping: Mapping[str, str]) -> Node:
    if isinstance(node, EventNode):
        return EventNode(
            mapping.get(node.left, node.left),
            mapping.get(node.right, node.right),
            node.action,
        )
    if isinstance(node, UnaryNode):
        return UnaryNode(node.label, _rename(node.child, mapping))
    if isinstance(node, BinaryNode):
        return BinaryNode(
            node.label,
            _rename(node.left, mapping),
            _rename(node.right, mapping),
        )
    if isinstance(node, ConditionalNode):
        return ConditionalNode(
            node.label,
            mapping.get(node.first_entity, node.first_entity),
            mapping.get(node.second_entity, node.second_entity),
            _rename(node.yes, mapping),
            _rename(node.no, mapping),
        )
    raise TypeError(node)


def _shift_mapping(shift: int) -> dict[str, str]:
    return {
        ENTITIES[index]: ENTITIES[(index + shift) % len(ENTITIES)]
        for index in range(len(ENTITIES))
    }


def _corrupt(state: State, index: int) -> State:
    output = list(state)
    output[index % len(output)] += 97
    return tuple(output)


def training_observations() -> tuple[Observation, ...]:
    rng = random.Random(123)
    true_model = _true_model()
    rows: list[Observation] = []
    for cell, base in enumerate(TRAINING_PROGRAMS):
        for repetition in range(REPETITIONS):
            node = _rename(base, _shift_mapping((cell + repetition) % 6))
            values = [rng.randrange(4) for _ in ENTITIES]
            if repetition % 2 == 0:
                first = (cell + repetition) % 6
                second = (first + 2) % 6
                values[second] = values[first]
            before = tuple(values)
            sentence = punctuate(render(node), cell + repetition)
            prediction = true_model.predict(sentence, before)
            if prediction is None:
                raise RuntimeError("invalid generated training row")
            after = (
                _corrupt(prediction, cell)
                if repetition < FLIPS
                else prediction
            )
            rows.append(Observation(sentence, before, after))
    return tuple(rows)


def heldout_observations() -> tuple[Observation, ...]:
    rng = random.Random(999)
    true_model = _true_model()
    rows: list[Observation] = []
    for cell, base in enumerate(HELDOUT_PROGRAMS):
        for variant in range(2):
            node = _rename(base, _shift_mapping((cell + 2 * variant + 1) % 6))
            for _ in range(1000):
                values = [rng.randrange(5) for _ in ENTITIES]
                if variant == 0:
                    first = cell % 6
                    values[(first + 2) % 6] = values[first]
                before = tuple(values)
                sentence = punctuate(render(node), 100 + cell + variant)
                prediction = true_model.predict(sentence, before)
                if prediction is not None:
                    rows.append(Observation(sentence, before, prediction))
                    break
            else:
                raise RuntimeError("could not generate held-out row")
    return tuple(rows)


def _collect_lexemes(
    node: Node,
    sequence_labels: set[str],
    condition_labels: set[str],
    negation_labels: set[str],
    reference_labels: set[str],
) -> None:
    if isinstance(node, EventNode):
        for token in (node.left, node.right):
            if token not in ENTITIES:
                reference_labels.add(token)
        return
    if isinstance(node, UnaryNode):
        negation_labels.add(node.label)
        _collect_lexemes(
            node.child,
            sequence_labels,
            condition_labels,
            negation_labels,
            reference_labels,
        )
        return
    if isinstance(node, BinaryNode):
        sequence_labels.add(node.label)
        _collect_lexemes(
            node.left,
            sequence_labels,
            condition_labels,
            negation_labels,
            reference_labels,
        )
        _collect_lexemes(
            node.right,
            sequence_labels,
            condition_labels,
            negation_labels,
            reference_labels,
        )
        return
    if isinstance(node, ConditionalNode):
        condition_labels.add(node.label)
        _collect_lexemes(
            node.yes,
            sequence_labels,
            condition_labels,
            negation_labels,
            reference_labels,
        )
        _collect_lexemes(
            node.no,
            sequence_labels,
            condition_labels,
            negation_labels,
            reference_labels,
        )
        return
    raise TypeError(node)


def candidate_models(rows: Iterable[Observation]) -> tuple[RecursiveDiscourseModel, ...]:
    sequence_labels: set[str] = set()
    condition_labels: set[str] = set()
    negation_labels: set[str] = set()
    reference_labels: set[str] = set()
    for row in rows:
        _collect_lexemes(
            parse_program(row.sentence),
            sequence_labels,
            condition_labels,
            negation_labels,
            reference_labels,
        )

    if (
        len(sequence_labels) != 2
        or len(condition_labels) != 2
        or len(negation_labels) != 1
        or len(reference_labels) != 2
    ):
        raise NonIdentifiableRecursiveDiscourseError("unexpected hypothesis arity")

    models: list[RecursiveDiscourseModel] = []
    for sequence_values in permutations(("LR", "RL"), 2):
        for condition_values in permutations(("EQ", "NEQ"), 2):
            for negation_value in ("SKIP", "EXEC"):
                for reference_values in permutations(("SRC", "DST"), 2):
                    models.append(
                        RecursiveDiscourseModel(
                            tuple(sorted(zip(sequence_labels, sequence_values))),
                            tuple(sorted(zip(condition_labels, condition_values))),
                            tuple(
                                (label, negation_value)
                                for label in sorted(negation_labels)
                            ),
                            tuple(sorted(zip(reference_labels, reference_values))),
                        )
                    )
    return tuple(models)


def _error(model: RecursiveDiscourseModel, rows: Iterable[Observation]) -> int:
    return sum(
        model.predict(row.sentence, row.before) != row.after
        for row in rows
    )


def induce(
    rows: Iterable[Observation],
) -> tuple[RecursiveDiscourseModel, dict[str, int | None]]:
    rows = tuple(rows)
    scored = sorted(
        (
            _error(model, rows),
            json.dumps(
                {
                    "sequence": model.sequence,
                    "condition": model.condition,
                    "negation": model.negation,
                    "reference": model.reference,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            model,
        )
        for model in candidate_models(rows)
    )
    best_error = scored[0][0]
    best = [entry for entry in scored if entry[0] == best_error]
    if len(best) != 1:
        raise NonIdentifiableRecursiveDiscourseError(
            f"optimal models={len(best)}"
        )
    second = next(
        (error for error, _, _ in scored if error > best_error),
        None,
    )
    return best[0][2], {
        "candidates": len(scored),
        "errors": best_error,
        "second": second,
    }


def score(
    model: RecursiveDiscourseModel,
    rows: Iterable[Observation],
) -> tuple[float, float]:
    rows = tuple(rows)
    answers = [model.predict(row.sentence, row.before) for row in rows]
    return (
        sum(answer == row.after for answer, row in zip(answers, rows))
        / len(rows),
        sum(answer is not None for answer in answers) / len(rows),
    )


def _shape(node: Node) -> object:
    if isinstance(node, EventNode):
        return ("E", node.action)
    if isinstance(node, UnaryNode):
        return ("U", node.label, _shape(node.child))
    if isinstance(node, BinaryNode):
        return ("B", node.label, _shape(node.left), _shape(node.right))
    if isinstance(node, ConditionalNode):
        return ("C", node.label, _shape(node.yes), _shape(node.no))
    raise TypeError(node)


def sentence_memorizer_coverage(
    train: Iterable[Observation],
    test: Iterable[Observation],
) -> float:
    known = {row.text for row in train}
    test = tuple(test)
    return sum(row.text in known for row in test) / len(test)


def tree_memorizer_coverage(
    train: Iterable[Observation],
    test: Iterable[Observation],
) -> float:
    known = {_shape(parse_program(row.sentence)) for row in train}
    test = tuple(test)
    return sum(
        _shape(parse_program(row.sentence)) in known
        for row in test
    ) / len(test)


def shallow_parser_coverage(rows: Iterable[Observation]) -> float:
    rows = tuple(rows)
    return sum(_depth(parse_program(row.sentence)) <= 2 for row in rows) / len(rows)


def _depth(node: Node) -> int:
    if isinstance(node, EventNode):
        return 0
    if isinstance(node, UnaryNode):
        return 1 + _depth(node.child)
    if isinstance(node, BinaryNode):
        return 1 + max(_depth(node.left), _depth(node.right))
    if isinstance(node, ConditionalNode):
        return 1 + max(_depth(node.yes), _depth(node.no))
    raise TypeError(node)


def _atom_count(node: Node) -> int:
    if isinstance(node, EventNode):
        return 1
    if isinstance(node, UnaryNode):
        return _atom_count(node.child)
    if isinstance(node, BinaryNode):
        return _atom_count(node.left) + _atom_count(node.right)
    if isinstance(node, ConditionalNode):
        return _atom_count(node.yes) + _atom_count(node.no)
    raise TypeError(node)


def observational_nonidentifiability_controls() -> dict[str, bool]:
    true = _true_model()

    swapped_sequence = RecursiveDiscourseModel(
        tuple(
            (label, "RL" if value == "LR" else "LR")
            for label, value in true.sequence
        ),
        true.condition,
        true.negation,
        true.reference,
    )
    commuting = sequence(
        "続いて",
        event("アキ", "ボブ", "渡す"),
        event("チカ", "ダイ", "写す"),
    )
    commuting_state = (1, 2, 3, 4, 5, 6)
    order_nonidentifiable = (
        execute(commuting, commuting_state, true, None)[0]
        == execute(commuting, commuting_state, swapped_sequence, None)[0]
    )

    swapped_condition = RecursiveDiscourseModel(
        true.sequence,
        tuple(
            (label, "NEQ" if value == "EQ" else "EQ")
            for label, value in true.condition
        ),
        true.negation,
        true.reference,
    )
    equivalent_branches = condition(
        "同じなら",
        "アキ",
        "ボブ",
        event("チカ", "ダイ", "渡す"),
        event("チカ", "ダイ", "渡す"),
    )
    condition_state = (1, 1, 2, 3, 4, 5)
    condition_nonidentifiable = (
        execute(equivalent_branches, condition_state, true, None)[0]
        == execute(equivalent_branches, condition_state, swapped_condition, None)[0]
    )

    executing_negation = RecursiveDiscourseModel(
        true.sequence,
        true.condition,
        (("せず", "EXEC"),),
        true.reference,
    )
    no_effect_child = negate(event("アキ", "ボブ", "渡す"))
    equal_value_state = (7, 7, 2, 3, 4, 5)
    negation_nonidentifiable = (
        execute(no_effect_child, equal_value_state, true, None)[0]
        == execute(no_effect_child, equal_value_state, executing_negation, None)[0]
    )

    swapped_reference = RecursiveDiscourseModel(
        true.sequence,
        true.condition,
        true.negation,
        tuple(
            (label, "SRC" if value == "DST" else "DST")
            for label, value in true.reference
        ),
    )
    equal_context = sequence(
        "続いて",
        event("アキ", "ボブ", "渡す"),
        event("その人", "チカ", "写す"),
    )
    reference_state = (9, 9, 3, 4, 5, 6)
    reference_nonidentifiable = (
        execute(equal_context, reference_state, true, None)[0]
        == execute(equal_context, reference_state, swapped_reference, None)[0]
    )

    return {
        "commuting_events_do_not_identify_order": order_nonidentifiable,
        "equivalent_branches_do_not_identify_condition": condition_nonidentifiable,
        "no_effect_subtree_does_not_identify_negation": negation_nonidentifiable,
        "equal_antecedent_values_do_not_identify_reference": reference_nonidentifiable,
    }


def causal_interventions(model: RecursiveDiscourseModel) -> dict[str, bool]:
    state = (1, 2, 3, 4, 5, 6)

    order_left = sequence(
        "続いて",
        event("アキ", "ボブ", "渡す"),
        event("ボブ", "チカ", "写す"),
    )
    order_right = BinaryNode("先立ち", order_left.left, order_left.right)
    order = (
        model.predict(render(order_left), state)
        != model.predict(render(order_right), state)
    )

    condition_left = condition(
        "同じなら",
        "アキ",
        "ボブ",
        event("チカ", "ダイ", "渡す"),
        event("エリ", "フミ", "写す"),
    )
    condition_right = ConditionalNode(
        "違うなら",
        condition_left.first_entity,
        condition_left.second_entity,
        condition_left.yes,
        condition_left.no,
    )
    condition_used = (
        model.predict(render(condition_left), (1, 1, 2, 3, 4, 5))
        != model.predict(render(condition_right), (1, 1, 2, 3, 4, 5))
    )

    child = event("アキ", "ボブ", "渡す")
    negation_used = (
        model.predict(render(negate(child)), state)
        != model.predict(render(child), state)
    )

    reference_probe = sequence(
        "続いて",
        event("アキ", "ボブ", "渡す"),
        event("チカ", "その人", "写す"),
    )
    swapped = RecursiveDiscourseModel(
        model.sequence,
        model.condition,
        model.negation,
        tuple(
            (label, "SRC" if value == "DST" else "DST")
            for label, value in model.reference
        ),
    )
    reference_used = (
        model.predict(render(reference_probe), state)
        != swapped.predict(render(reference_probe), state)
    )

    return {
        "sequence_intervention_changes_prediction": order,
        "condition_intervention_changes_prediction": condition_used,
        "negation_intervention_changes_prediction": negation_used,
        "reference_intervention_changes_prediction": reference_used,
    }


def unknowns_abstain(model: RecursiveDiscourseModel) -> bool:
    base = render(
        sequence(
            "続いて",
            event("アキ", "ボブ", "渡す"),
            event("その人", "チカ", "写す"),
        )
    )
    unknown_operator = base.replace("続いて", "それから", 1)
    unknown_reference = base.replace("その人", "彼")
    malformed = "続いて【アキがボブに渡す】【その人がチカに写す"
    state = (1, 2, 3, 4, 5, 6)
    return all(
        model.predict(text, state) is None
        for text in (unknown_operator, unknown_reference, malformed)
    )


def literal_heldout_bits(rows: Iterable[Observation]) -> int:
    table = [
        (row.text, row.before, row.after)
        for row in rows
    ]
    return len(
        json.dumps(table, ensure_ascii=False, separators=(",", ":")).encode()
    ) * 8


def run() -> dict[str, object]:
    training = training_observations()
    heldout = heldout_observations()
    model, fit = induce(training)
    accuracy, coverage = score(model, heldout)
    controls = observational_nonidentifiability_controls()
    interventions = causal_interventions(model)

    heldout_depths = tuple(_depth(parse_program(row.sentence)) for row in heldout)
    heldout_atoms = tuple(_atom_count(parse_program(row.sentence)) for row in heldout)
    sentence_coverage = sentence_memorizer_coverage(training, heldout)
    tree_coverage = tree_memorizer_coverage(training, heldout)
    shallow_coverage = shallow_parser_coverage(heldout)

    checks = {
        "sequence_semantics_are_recovered": dict(model.sequence) == TRUE_SEQUENCE,
        "condition_semantics_are_recovered": dict(model.condition) == TRUE_CONDITION,
        "negation_semantics_are_recovered": dict(model.negation) == TRUE_NEGATION,
        "reference_semantics_are_recovered": dict(model.reference) == TRUE_REFERENCE,
        "bounded_noise_is_recovered": fit["errors"] == len(TRAINING_PROGRAMS) * FLIPS,
        "strict_positive_margin": fit["second"] is not None and fit["second"] > fit["errors"],
        "recursive_heldout_is_perfect": accuracy == coverage == 1.0,
        "whole_sentence_memorizer_has_zero_coverage": sentence_coverage == 0.0,
        "tree_shape_memorizer_has_zero_coverage": tree_coverage == 0.0,
        "depth_two_parser_has_zero_coverage": shallow_coverage == 0.0,
        "heldout_has_three_to_five_events": min(heldout_atoms) >= 3 and max(heldout_atoms) <= 5,
        "heldout_depth_is_at_least_three": min(heldout_depths) >= 3,
        "all_nonidentifiability_controls_hold": all(controls.values()),
        "all_internal_interventions_hold": all(interventions.values()),
        "unknown_or_malformed_inputs_abstain": unknowns_abstain(model),
        "continuous_input_has_no_whitespace": all(
            not any(character.isspace() for character in row.sentence)
            for row in (*training, *heldout)
        ),
    }

    return {
        "campaign": {
            "name": "phase18a7-recursive-conditional-discourse-c1",
            "operator_spans_prelisted": False,
            "operator_hypothesis_class_fixed": True,
            "inherited_atoms": "entity/action/case atoms",
            "public_examples": 0,
        },
        "induction": {
            **fit,
            "sequence": [list(item) for item in model.sequence],
            "condition": [list(item) for item in model.condition],
            "negation": [list(item) for item in model.negation],
            "reference": [list(item) for item in model.reference],
        },
        "evaluation": {
            "training_programs": len(TRAINING_PROGRAMS),
            "training_rows": len(training),
            "heldout_programs": len(HELDOUT_PROGRAMS),
            "heldout_rows": len(heldout),
            "heldout_min_depth": min(heldout_depths),
            "heldout_max_depth": max(heldout_depths),
            "heldout_min_events": min(heldout_atoms),
            "heldout_max_events": max(heldout_atoms),
            "accuracy": accuracy,
            "coverage": coverage,
            "sentence_memorizer_coverage": sentence_coverage,
            "tree_memorizer_coverage": tree_coverage,
            "shallow_parser_coverage": shallow_coverage,
        },
        "controls": controls,
        "interventions": interventions,
        "resources": {
            "model_bits": model.description_bits,
            "literal_heldout_table_bits": literal_heldout_bits(heldout),
            "source_bytes": Path(__file__).read_bytes().__len__(),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "controlled_recursive_discourse": all(checks.values()),
            "unbracketed_general_japanese": False,
            "reading_comprehension": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "recursive brackets expose constituent boundaries",
            "entity/action/case atoms are inherited",
            "only equality and inequality conditions are available",
            "only two sequence labels, one subtree-negation label, and two references are induced",
            "maximum evaluated depth is four and maximum event count is five",
            "no open-domain knowledge, question answering, explanation, or proof",
            "Python runtime and fixed parser are excluded from learned payload",
        ],
    }


def render_markdown(payload: Mapping[str, object]) -> str:
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18a-7 results: recursive conditional discourse

- Candidate semantic systems: **{induction["candidates"]}**
- Training errors / second best: **{induction["errors"]} / {induction["second"]}**
- Sequence operators: **{induction["sequence"]}**
- Condition operators: **{induction["condition"]}**
- Negation operator: **{induction["negation"]}**
- Cross-clause references: **{induction["reference"]}**
- Training programs / rows: **{evaluation["training_programs"]} / {evaluation["training_rows"]}**
- Held-out programs / rows: **{evaluation["heldout_programs"]} / {evaluation["heldout_rows"]}**
- Held-out depth range: **{evaluation["heldout_min_depth"]}–{evaluation["heldout_max_depth"]}**
- Held-out event-count range: **{evaluation["heldout_min_events"]}–{evaluation["heldout_max_events"]}**
- Accuracy / coverage: **{100 * evaluation["accuracy"]:.1f}% / {100 * evaluation["coverage"]:.1f}%**
- Sentence / tree memorizer coverage: **{100 * evaluation["sentence_memorizer_coverage"]:.1f}% / {100 * evaluation["tree_memorizer_coverage"]:.1f}%**
- Depth-two parser coverage: **{100 * evaluation["shallow_parser_coverage"]:.1f}%**
- Learned payload / literal held-out table: **{resources["model_bits"]} / {resources["literal_heldout_table_bits"]} bits**

This is bracketed controlled recursion with equality conditions, subtree negation,
and cross-clause role references. It is not unrestricted Japanese reading
comprehension or Japanese high-school-level intelligence.
"""


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase18a7.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase18a7.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
