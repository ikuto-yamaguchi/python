from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import permutations
import json
from pathlib import Path
import random
import re
from typing import Iterable, Mapping, Sequence

from .phase18a7_recursive_conditional_discourse import (
    BinaryNode,
    ConditionalNode,
    ENTITIES,
    RecursiveDiscourseModel,
    UnaryNode,
    induce as induce_discourse,
    training_observations as discourse_training_observations,
)
from .phase18b1_text_qa_verified_trace import (
    Solution,
    TraceStep,
    _normalize_outer,
    _outer_blocks,
    _parse_assignments,
)

TRUE_OPERATIONS = {
    "増やす": "ADD",
    "減らす": "SUB",
    "倍にする": "MUL",
}
REPETITIONS = 9
FLIPS = 1

State = tuple[int, ...]


@dataclass(frozen=True)
class ArithmeticNode:
    target: str
    amount: int
    label: str


Node = ArithmeticNode | UnaryNode | BinaryNode | ConditionalNode


class NonIdentifiableArithmeticError(ValueError):
    pass


@dataclass(frozen=True)
class ArithmeticObservation:
    sentence: str
    before: State
    after: State


@dataclass(frozen=True)
class ArithmeticModel:
    discourse: RecursiveDiscourseModel
    operations: tuple[tuple[str, str], ...]

    @property
    def description_bits(self) -> int:
        payload = {
            "control": {
                "sequence": self.discourse.sequence,
                "condition": self.discourse.condition,
                "negation": self.discourse.negation,
            },
            "operations": self.operations,
            "entities": ENTITIES,
            "atom_schema": "ENTITYをINTEGERだけLABEL",
        }
        return len(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ) * 8

    def execute(self, text: str, initial: Sequence[int]) -> State | None:
        try:
            return execute(parse_program(text), tuple(initial), self)
        except (KeyError, ValueError):
            return None


@dataclass(frozen=True)
class ArithmeticProblem:
    sentence: str
    initial: State
    program: Node
    query_entity: str


@dataclass(frozen=True)
class ArithmeticQuestionMachine:
    model: ArithmeticModel

    def solve(self, sentence: str) -> Solution | None:
        try:
            problem = parse_problem(sentence)
            final, trace = execute_with_trace(
                problem.program,
                problem.initial,
                self.model,
                "",
            )
            return Solution(
                final[ENTITIES.index(problem.query_entity)],
                tuple(trace),
            )
        except (KeyError, ValueError):
            return None


def _control_model() -> RecursiveDiscourseModel:
    model, _ = induce_discourse(discourse_training_observations())
    return model


def arithmetic(
    target: str,
    amount: int,
    label: str,
) -> ArithmeticNode:
    return ArithmeticNode(target, amount, label)


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


def render(node: Node) -> str:
    if isinstance(node, ArithmeticNode):
        return f"{node.target}を{node.amount}だけ{node.label}"
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


def _blocks(text: str, start: int) -> tuple[str, ...]:
    rows: list[str] = []
    index = start
    while index < len(text):
        if text[index] != "【":
            raise ValueError("opening bracket")
        depth = 1
        end = index + 1
        while end < len(text) and depth:
            if text[end] == "【":
                depth += 1
            elif text[end] == "】":
                depth -= 1
            end += 1
        if depth:
            raise ValueError("unbalanced")
        rows.append(text[index + 1 : end - 1])
        index = end
    return tuple(rows)


def parse_program(text: str) -> Node:
    text = _normalize_outer(text)
    for character in "。、，,！？!?":
        text = text.replace(character, "")
    if "【" not in text:
        match = re.fullmatch(r"(.+?)を(-?\d+)だけ(.+)", text)
        if match is None:
            raise ValueError("not arithmetic atom")
        target, amount, label = match.groups()
        if target not in ENTITIES:
            raise ValueError("unknown arithmetic target")
        return ArithmeticNode(target, int(amount), label)

    first = text.index("【")
    prefix = text[:first]
    blocks = _blocks(text, first)
    match = re.fullmatch(r"(.+?)\((.+?)と(.+?)\)", prefix)
    if match is not None:
        if len(blocks) != 2:
            raise ValueError("condition arity")
        return ConditionalNode(
            match.group(1),
            match.group(2),
            match.group(3),
            parse_program(blocks[0]),
            parse_program(blocks[1]),
        )
    if len(blocks) == 2:
        return BinaryNode(
            prefix,
            parse_program(blocks[0]),
            parse_program(blocks[1]),
        )
    if len(blocks) == 1:
        return UnaryNode(prefix, parse_program(blocks[0]))
    raise ValueError("operator arity")


def _apply_value(value: int, amount: int, operation: str) -> int:
    if operation == "ADD":
        return value + amount
    if operation == "SUB":
        return value - amount
    if operation == "MUL":
        return value * amount
    raise ValueError(operation)


def execute(node: Node, state: State, model: ArithmeticModel) -> State:
    if isinstance(node, ArithmeticNode):
        operation = dict(model.operations).get(node.label)
        if operation is None:
            raise ValueError("unknown arithmetic label")
        output = list(state)
        index = ENTITIES.index(node.target)
        output[index] = _apply_value(
            state[index],
            node.amount,
            operation,
        )
        return tuple(output)

    if isinstance(node, UnaryNode):
        mode = dict(model.discourse.negation).get(node.label)
        if mode == "SKIP":
            return state
        if mode == "EXEC":
            return execute(node.child, state, model)
        raise ValueError("unknown unary")

    if isinstance(node, BinaryNode):
        order = dict(model.discourse.sequence).get(node.label)
        if order == "LR":
            return execute(node.right, execute(node.left, state, model), model)
        if order == "RL":
            return execute(node.left, execute(node.right, state, model), model)
        raise ValueError("unknown sequence")

    if isinstance(node, ConditionalNode):
        relation = dict(model.discourse.condition).get(node.label)
        first = ENTITIES.index(node.first_entity)
        second = ENTITIES.index(node.second_entity)
        equal = state[first] == state[second]
        if relation == "EQ":
            choice = equal
        elif relation == "NEQ":
            choice = not equal
        else:
            raise ValueError("unknown condition")
        return execute(node.yes if choice else node.no, state, model)

    raise TypeError(node)


TRAINING_PROGRAMS: tuple[Node, ...] = (
    arithmetic("アキ", 3, "増やす"),
    arithmetic("ボブ", 2, "減らす"),
    arithmetic("チカ", 4, "倍にする"),
    sequence(
        "続いて",
        arithmetic("ダイ", 2, "増やす"),
        arithmetic("ダイ", 3, "倍にする"),
    ),
    sequence(
        "先立ち",
        arithmetic("エリ", 5, "減らす"),
        arithmetic("エリ", 2, "倍にする"),
    ),
    condition(
        "同じなら",
        "アキ",
        "ボブ",
        arithmetic("フミ", 7, "増やす"),
        arithmetic("フミ", 3, "減らす"),
    ),
)


HELDOUT_PROGRAMS: tuple[Node, ...] = (
    sequence(
        "続いて",
        arithmetic("アキ", 5, "増やす"),
        sequence(
            "先立ち",
            arithmetic("アキ", 2, "倍にする"),
            arithmetic("アキ", 3, "減らす"),
        ),
    ),
    condition(
        "違うなら",
        "アキ",
        "ボブ",
        sequence(
            "続いて",
            arithmetic("チカ", 4, "減らす"),
            arithmetic("チカ", 3, "倍にする"),
        ),
        sequence(
            "先立ち",
            arithmetic("チカ", 2, "増やす"),
            arithmetic("チカ", 5, "倍にする"),
        ),
    ),
    sequence(
        "先立ち",
        condition(
            "同じなら",
            "ダイ",
            "エリ",
            arithmetic("ボブ", 6, "増やす"),
            arithmetic("ボブ", 2, "倍にする"),
        ),
        arithmetic("ボブ", 4, "減らす"),
    ),
    sequence(
        "続いて",
        arithmetic("エリ", 3, "倍にする"),
        negate(
            sequence(
                "続いて",
                arithmetic("エリ", 100, "増やす"),
                arithmetic("エリ", 5, "減らす"),
            )
        ),
    ),
    condition(
        "同じなら",
        "アキ",
        "チカ",
        sequence(
            "続いて",
            arithmetic("フミ", 2, "倍にする"),
            condition(
                "違うなら",
                "ボブ",
                "ダイ",
                arithmetic("フミ", 9, "増やす"),
                arithmetic("フミ", 4, "減らす"),
            ),
        ),
        sequence(
            "先立ち",
            arithmetic("フミ", 3, "減らす"),
            arithmetic("フミ", 4, "倍にする"),
        ),
    ),
    sequence(
        "続いて",
        arithmetic("ダイ", 8, "増やす"),
        condition(
            "違うなら",
            "ダイ",
            "エリ",
            sequence(
                "先立ち",
                arithmetic("ダイ", 2, "倍にする"),
                arithmetic("ダイ", 1, "減らす"),
            ),
            negate(arithmetic("ダイ", 99, "増やす")),
        ),
    ),
)


def _true_model() -> ArithmeticModel:
    return ArithmeticModel(
        _control_model(),
        tuple(sorted(TRUE_OPERATIONS.items())),
    )


def _corrupt(state: State, index: int) -> State:
    output = list(state)
    output[index % len(output)] += 101
    return tuple(output)


def training_observations() -> tuple[ArithmeticObservation, ...]:
    rng = random.Random(314)
    model = _true_model()
    rows: list[ArithmeticObservation] = []
    for cell, program in enumerate(TRAINING_PROGRAMS):
        for repetition in range(REPETITIONS):
            values = [rng.randint(-5, 8) for _ in ENTITIES]
            if repetition % 2 == 0:
                values[(cell + 1) % 6] = values[cell % 6]
            before = tuple(values)
            after = execute(program, before, model)
            if repetition < FLIPS:
                after = _corrupt(after, cell)
            rows.append(
                ArithmeticObservation(
                    render(program),
                    before,
                    after,
                )
            )
    return tuple(rows)


def candidate_models(
    rows: Iterable[ArithmeticObservation],
) -> tuple[ArithmeticModel, ...]:
    labels: set[str] = set()

    def visit(node: Node) -> None:
        if isinstance(node, ArithmeticNode):
            labels.add(node.label)
        elif isinstance(node, UnaryNode):
            visit(node.child)
        elif isinstance(node, BinaryNode):
            visit(node.left)
            visit(node.right)
        elif isinstance(node, ConditionalNode):
            visit(node.yes)
            visit(node.no)
        else:
            raise TypeError(node)

    for row in rows:
        visit(parse_program(row.sentence))
    if len(labels) != 3:
        raise NonIdentifiableArithmeticError("expected three arithmetic labels")
    control = _control_model()
    return tuple(
        ArithmeticModel(
            control,
            tuple(sorted(zip(labels, values))),
        )
        for values in permutations(("ADD", "SUB", "MUL"), 3)
    )


def _error(
    model: ArithmeticModel,
    rows: Iterable[ArithmeticObservation],
) -> int:
    return sum(
        model.execute(row.sentence, row.before) != row.after
        for row in rows
    )


def induce(
    rows: Iterable[ArithmeticObservation],
) -> tuple[ArithmeticModel, dict[str, int | None]]:
    rows = tuple(rows)
    scored = sorted(
        (
            _error(model, rows),
            repr(model.operations),
            model,
        )
        for model in candidate_models(rows)
    )
    best_error = scored[0][0]
    best = [row for row in scored if row[0] == best_error]
    if len(best) != 1:
        raise NonIdentifiableArithmeticError(
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


def fit_question_machine() -> ArithmeticQuestionMachine:
    model, _ = induce(training_observations())
    return ArithmeticQuestionMachine(model)


def parse_problem(sentence: str) -> ArithmeticProblem:
    blocks = _outer_blocks(sentence)
    if len(blocks) != 3:
        raise ValueError("three outer blocks required")
    assignments: list[tuple[int, State]] = []
    programs: list[tuple[int, Node]] = []
    queries: list[tuple[int, str]] = []
    for index, block in enumerate(blocks):
        try:
            assignments.append((index, _parse_assignments(block)))
        except (TypeError, ValueError):
            pass
        try:
            programs.append((index, parse_program(block)))
        except ValueError:
            pass
        value = _normalize_outer(block)
        if value in ENTITIES:
            queries.append((index, value))
    if (
        len(assignments) != 1
        or len(programs) != 1
        or len(queries) != 1
    ):
        raise ValueError("ambiguous arithmetic problem blocks")
    if len({assignments[0][0], programs[0][0], queries[0][0]}) != 3:
        raise ValueError("arithmetic problem block roles overlap")
    return ArithmeticProblem(
        sentence,
        assignments[0][1],
        programs[0][1],
        queries[0][1],
    )


def render_problem(
    initial: Sequence[int],
    program: Node,
    query: str,
    index: int,
) -> str:
    assignment = "、".join(
        f"{entity}={value}"
        for entity, value in zip(ENTITIES, initial)
    )
    labels = (
        ("初期数値", "計算手順", "答える対象"),
        ("開始状態", "操作", "最後に調べる人"),
        ("はじめ", "規則", "質問対象"),
    )[index % 3]
    return (
        f"{labels[0]}【{assignment}】。"
        f"{labels[1]}【{render(program)}】。"
        f"{labels[2]}【{query}】。"
    )


def execute_with_trace(
    node: Node,
    state: State,
    model: ArithmeticModel,
    path: str,
) -> tuple[State, list[TraceStep]]:
    if isinstance(node, ArithmeticNode):
        operation = dict(model.operations).get(node.label)
        if operation is None:
            raise ValueError("unknown operation")
        index = ENTITIES.index(node.target)
        after_value = _apply_value(state[index], node.amount, operation)
        step = TraceStep.build(
            "arithmetic",
            path=path,
            target=node.target,
            label=node.label,
            operation=operation,
            amount=node.amount,
            before_value=state[index],
            after_value=after_value,
        )
        output = list(state)
        output[index] = after_value
        return tuple(output), [step]

    if isinstance(node, UnaryNode):
        mode = dict(model.discourse.negation).get(node.label)
        trace = [
            TraceStep.build(
                "negation",
                path=path,
                label=node.label,
                mode=mode,
            )
        ]
        if mode == "SKIP":
            return state, trace
        if mode == "EXEC":
            child_state, child_trace = execute_with_trace(
                node.child,
                state,
                model,
                path + "U",
            )
            return child_state, trace + child_trace
        raise ValueError("unknown negation")

    if isinstance(node, BinaryNode):
        order = dict(model.discourse.sequence).get(node.label)
        trace = [
            TraceStep.build(
                "sequence",
                path=path,
                label=node.label,
                order=order,
            )
        ]
        if order == "LR":
            children = ((node.left, path + "L"), (node.right, path + "R"))
        elif order == "RL":
            children = ((node.right, path + "R"), (node.left, path + "L"))
        else:
            raise ValueError("unknown sequence")
        current = state
        for child, child_path in children:
            current, child_trace = execute_with_trace(
                child,
                current,
                model,
                child_path,
            )
            trace.extend(child_trace)
        return current, trace

    if isinstance(node, ConditionalNode):
        relation = dict(model.discourse.condition).get(node.label)
        first = ENTITIES.index(node.first_entity)
        second = ENTITIES.index(node.second_entity)
        equal = state[first] == state[second]
        if relation == "EQ":
            test = equal
        elif relation == "NEQ":
            test = not equal
        else:
            raise ValueError("unknown condition")
        branch = "Y" if test else "N"
        trace = [
            TraceStep.build(
                "condition",
                path=path,
                label=node.label,
                relation=relation,
                first_entity=node.first_entity,
                second_entity=node.second_entity,
                first_value=state[first],
                second_value=state[second],
                branch=branch,
            )
        ]
        child_state, child_trace = execute_with_trace(
            node.yes if test else node.no,
            state,
            model,
            path + branch,
        )
        return child_state, trace + child_trace

    raise TypeError(node)


@dataclass
class _Cursor:
    steps: tuple[TraceStep, ...]
    index: int = 0

    def consume(self, step: TraceStep) -> None:
        if self.index >= len(self.steps) or self.steps[self.index] != step:
            raise ValueError("trace mismatch")
        self.index += 1


def verify_node(
    node: Node,
    state: State,
    model: ArithmeticModel,
    path: str,
    cursor: _Cursor,
) -> State:
    if isinstance(node, ArithmeticNode):
        operation = dict(model.operations).get(node.label)
        index = ENTITIES.index(node.target)
        after_value = _apply_value(state[index], node.amount, operation)
        cursor.consume(
            TraceStep.build(
                "arithmetic",
                path=path,
                target=node.target,
                label=node.label,
                operation=operation,
                amount=node.amount,
                before_value=state[index],
                after_value=after_value,
            )
        )
        output = list(state)
        output[index] = after_value
        return tuple(output)

    if isinstance(node, UnaryNode):
        mode = dict(model.discourse.negation).get(node.label)
        cursor.consume(
            TraceStep.build(
                "negation",
                path=path,
                label=node.label,
                mode=mode,
            )
        )
        if mode == "SKIP":
            return state
        if mode == "EXEC":
            return verify_node(
                node.child,
                state,
                model,
                path + "U",
                cursor,
            )
        raise ValueError("unknown negation")

    if isinstance(node, BinaryNode):
        order = dict(model.discourse.sequence).get(node.label)
        cursor.consume(
            TraceStep.build(
                "sequence",
                path=path,
                label=node.label,
                order=order,
            )
        )
        if order == "LR":
            children = ((node.left, path + "L"), (node.right, path + "R"))
        elif order == "RL":
            children = ((node.right, path + "R"), (node.left, path + "L"))
        else:
            raise ValueError("unknown sequence")
        current = state
        for child, child_path in children:
            current = verify_node(
                child,
                current,
                model,
                child_path,
                cursor,
            )
        return current

    if isinstance(node, ConditionalNode):
        relation = dict(model.discourse.condition).get(node.label)
        first = ENTITIES.index(node.first_entity)
        second = ENTITIES.index(node.second_entity)
        equal = state[first] == state[second]
        if relation == "EQ":
            test = equal
        elif relation == "NEQ":
            test = not equal
        else:
            raise ValueError("unknown condition")
        branch = "Y" if test else "N"
        cursor.consume(
            TraceStep.build(
                "condition",
                path=path,
                label=node.label,
                relation=relation,
                first_entity=node.first_entity,
                second_entity=node.second_entity,
                first_value=state[first],
                second_value=state[second],
                branch=branch,
            )
        )
        return verify_node(
            node.yes if test else node.no,
            state,
            model,
            path + branch,
            cursor,
        )

    raise TypeError(node)


def verify_solution(
    sentence: str,
    solution: Solution,
    model: ArithmeticModel,
) -> bool:
    try:
        problem = parse_problem(sentence)
        cursor = _Cursor(solution.trace)
        final = verify_node(
            problem.program,
            problem.initial,
            model,
            "",
            cursor,
        )
        return (
            cursor.index == len(cursor.steps)
            and solution.answer
            == final[ENTITIES.index(problem.query_entity)]
        )
    except (KeyError, TypeError, ValueError):
        return False


def heldout_problems() -> tuple[tuple[str, int], ...]:
    model = _true_model()
    rng = random.Random(2718)
    rows: list[tuple[str, int]] = []
    for cell, program in enumerate(HELDOUT_PROGRAMS):
        for variant in range(2):
            values = [rng.randint(-6, 9) for _ in ENTITIES]
            if variant == 0:
                values[(cell + 1) % 6] = values[cell % 6]
            initial = tuple(values)
            final = execute(program, initial, model)
            target = next(
                (
                    index
                    for index, (before, after) in enumerate(
                        zip(initial, final)
                    )
                    if before != after
                ),
                cell % 6,
            )
            problem = render_problem(
                initial,
                program,
                ENTITIES[target],
                100 + cell + variant,
            )
            rows.append((problem, final[target]))
    return tuple(rows)


def calibration_problems() -> tuple[tuple[str, int], ...]:
    model, _ = induce(training_observations())
    rows: list[tuple[str, int]] = []
    for index, observation in enumerate(training_observations()):
        final = model.execute(observation.sentence, observation.before)
        if final is None:
            raise RuntimeError("invalid arithmetic calibration")
        target = next(
            (
                coordinate
                for coordinate, (before, after) in enumerate(
                    zip(observation.before, final)
                )
                if before != after
            ),
            index % 6,
        )
        rows.append(
            (
                render_problem(
                    observation.before,
                    parse_program(observation.sentence),
                    ENTITIES[target],
                    index,
                ),
                final[target],
            )
        )
    return tuple(rows)


def program_memorizer_coverage(
    train: Iterable[tuple[str, int]],
    test: Iterable[tuple[str, int]],
) -> float:
    known = {_normalize_outer(problem) for problem, _ in train}
    test = tuple(test)
    return sum(
        _normalize_outer(problem) in known
        for problem, _ in test
    ) / len(test)


def no_execution_accuracy(rows: Iterable[tuple[str, int]]) -> float:
    rows = tuple(rows)
    return sum(
        parse_problem(problem).initial[
            ENTITIES.index(parse_problem(problem).query_entity)
        ]
        == answer
        for problem, answer in rows
    ) / len(rows)


def orderless_bound(model: ArithmeticModel) -> float:
    first = sequence(
        "続いて",
        arithmetic("アキ", 3, "増やす"),
        arithmetic("アキ", 2, "倍にする"),
    )
    second = sequence(
        "先立ち",
        first.left,
        first.right,
    )
    initial = (4, 0, 0, 0, 0, 0)
    outputs = [
        execute(first, initial, model),
        execute(second, initial, model),
    ]
    return max(outputs.count(output) for output in set(outputs)) / len(outputs)


def nonidentifiability_controls() -> dict[str, bool]:
    control = _control_model()
    add = ArithmeticModel(
        control,
        (("x", "ADD"),),
    )
    sub = ArithmeticModel(
        control,
        (("x", "SUB"),),
    )
    mul = ArithmeticModel(
        control,
        (("x", "MUL"),),
    )
    zero = ArithmeticNode("アキ", 0, "x")
    one = ArithmeticNode("アキ", 1, "x")
    ambiguous = ArithmeticNode("アキ", 2, "x")
    state = (2, 0, 0, 0, 0, 0)
    return {
        "zero_does_not_distinguish_add_and_sub": (
            execute(zero, state, add) == execute(zero, state, sub)
        ),
        "multiply_by_one_is_identity": execute(one, state, mul) == state,
        "two_plus_two_equals_two_times_two": (
            execute(ambiguous, state, add)
            == execute(ambiguous, state, mul)
        ),
    }


def operation_intervention_changes_prediction(
    model: ArithmeticModel,
) -> bool:
    probe = arithmetic("アキ", 3, "増やす")
    initial = (5, 0, 0, 0, 0, 0)
    original = execute(probe, initial, model)
    swapped_rows = []
    for label, operation in model.operations:
        if label == "増やす":
            swapped_rows.append((label, "SUB"))
        elif operation == "SUB":
            swapped_rows.append((label, "ADD"))
        else:
            swapped_rows.append((label, operation))
    swapped = ArithmeticModel(
        model.discourse,
        tuple(sorted(swapped_rows)),
    )
    return original != execute(probe, initial, swapped)


def tampered_trace_rejected(
    problem: str,
    solution: Solution,
    model: ArithmeticModel,
) -> bool:
    steps = list(solution.trace)
    target = next(
        (
            index
            for index, step in enumerate(steps)
            if step.kind == "arithmetic"
        ),
        None,
    )
    if target is None:
        return False
    data = dict(steps[target].data)
    data["after_value"] = int(data["after_value"]) + 1
    steps[target] = TraceStep.build("arithmetic", **data)
    return not verify_solution(
        problem,
        Solution(solution.answer, tuple(steps)),
        model,
    )


def run() -> dict[str, object]:
    training = training_observations()
    model, fit = induce(training)
    machine = ArithmeticQuestionMachine(model)
    calibration = calibration_problems()
    heldout = heldout_problems()
    solutions = tuple(machine.solve(problem) for problem, _ in heldout)
    answered = sum(solution is not None for solution in solutions)
    correct = sum(
        solution is not None and solution.answer == answer
        for solution, (_, answer) in zip(solutions, heldout)
    )
    verified = sum(
        solution is not None
        and verify_solution(problem, solution, model)
        for solution, (problem, _) in zip(solutions, heldout)
    )
    tampered = all(
        solution is not None
        and tampered_trace_rejected(problem, solution, model)
        for solution, (problem, _) in zip(solutions, heldout)
    )
    wrong_answer = all(
        solution is not None
        and not verify_solution(
            problem,
            replace(solution, answer=solution.answer + 1),
            model,
        )
        for solution, (problem, _) in zip(solutions, heldout)
    )
    empty = all(
        solution is not None
        and not verify_solution(
            problem,
            Solution(solution.answer, ()),
            model,
        )
        for solution, (problem, _) in zip(solutions, heldout)
    )
    memorizer = program_memorizer_coverage(calibration, heldout)
    no_execution = no_execution_accuracy(heldout)
    order_bound = orderless_bound(model)
    controls = nonidentifiability_controls()
    trace_lengths = tuple(
        len(solution.trace)
        for solution in solutions
        if solution is not None
    )

    checks = {
        "operation_mapping_is_recovered": dict(model.operations) == TRUE_OPERATIONS,
        "bounded_noise_is_recovered": fit["errors"] == len(TRAINING_PROGRAMS) * FLIPS,
        "strict_positive_margin": fit["second"] is not None and fit["second"] > fit["errors"],
        "recursive_arithmetic_qa_is_perfect": correct == answered == len(heldout),
        "all_traces_verify": verified == len(heldout),
        "program_memorizer_has_zero_coverage": memorizer == 0.0,
        "no_execution_baseline_is_below_half": no_execution < 0.5,
        "orderless_operation_bound_is_half": order_bound == 0.5,
        "empty_trace_is_rejected": empty,
        "tampered_trace_is_rejected": tampered,
        "wrong_answer_is_rejected": wrong_answer,
        "operation_intervention_changes_prediction": (
            operation_intervention_changes_prediction(model)
        ),
        "nonidentifiability_controls_hold": all(controls.values()),
        "trace_length_is_bounded": max(trace_lengths) <= 12,
    }

    return {
        "campaign": {
            "name": "phase18b2-induced-integer-operations-c1",
            "inherits": "Phase 18a-7 control semantics and Phase 18b-1 trace discipline",
            "operation_names_preassigned": False,
            "public_examples": 0,
        },
        "induction": {
            **fit,
            "operations": [list(item) for item in model.operations],
        },
        "evaluation": {
            "training_programs": len(TRAINING_PROGRAMS),
            "training_rows": len(training),
            "heldout_programs": len(HELDOUT_PROGRAMS),
            "heldout_questions": len(heldout),
            "accuracy": correct / len(heldout),
            "coverage": answered / len(heldout),
            "trace_verification_rate": verified / len(heldout),
            "program_memorizer_coverage": memorizer,
            "no_execution_accuracy": no_execution,
            "orderless_bound": order_bound,
            "minimum_trace_steps": min(trace_lengths),
            "maximum_trace_steps": max(trace_lengths),
            "mean_trace_steps": sum(trace_lengths) / len(trace_lengths),
        },
        "controls": controls,
        "resources": {
            "model_bits": model.description_bits,
            "source_bytes": Path(__file__).read_bytes().__len__(),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "controlled_recursive_integer_arithmetic": all(checks.values()),
            "natural_word_problems": False,
            "algebra": False,
            "high_school_mathematics": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "outer problem roles and recursive constituents are bracketed",
            "only addition, subtraction, and integer multiplication are induced",
            "no division, fractions, equations, geometry, probability, or symbolic proof",
            "control semantics are inherited rather than relearned jointly",
            "fixed parser and Python runtime are excluded from learned payload",
        ],
    }


def render_markdown(payload: Mapping[str, object]) -> str:
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18b-2 results: induced integer operations

- Candidate operation mappings: **{induction["candidates"]}**
- Training errors / second best: **{induction["errors"]} / {induction["second"]}**
- Recovered operations: **{induction["operations"]}**
- Training programs / rows: **{evaluation["training_programs"]} / {evaluation["training_rows"]}**
- Held-out recursive questions: **{evaluation["heldout_questions"]}**
- Accuracy / coverage: **{100 * evaluation["accuracy"]:.1f}% / {100 * evaluation["coverage"]:.1f}%**
- Verified trace rate: **{100 * evaluation["trace_verification_rate"]:.1f}%**
- Problem memorizer coverage: **{100 * evaluation["program_memorizer_coverage"]:.1f}%**
- No-execution baseline: **{100 * evaluation["no_execution_accuracy"]:.1f}%**
- Orderless-operation upper bound: **{100 * evaluation["orderless_bound"]:.1f}%**
- Trace steps min / mean / max: **{evaluation["minimum_trace_steps"]} / {evaluation["mean_trace_steps"]:.2f} / {evaluation["maximum_trace_steps"]}**
- Learned payload: **{resources["model_bits"]} bits**

This is controlled recursive integer arithmetic with induced ADD/SUB/MUL
lexemes and verified traces. It is not natural Japanese word-problem,
algebra, or high-school mathematics ability.
"""


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase18b2.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase18b2.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
