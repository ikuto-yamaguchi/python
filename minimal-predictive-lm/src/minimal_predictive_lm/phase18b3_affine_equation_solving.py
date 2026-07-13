from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
import json
from pathlib import Path
import random
from typing import Iterable, Mapping, Sequence

from .phase18a7_recursive_conditional_discourse import BinaryNode, ConditionalNode, ENTITIES, UnaryNode
from .phase18b1_text_qa_verified_trace import TraceStep, _normalize_outer, _outer_blocks
from .phase18b2_induced_integer_operations import (
    ArithmeticModel,
    ArithmeticNode,
    Node,
    _true_model,
    execute,
    parse_program,
    render,
)

Affine = tuple[Fraction, Fraction]
AffineState = tuple[Affine, ...]


class NonUniqueEquationError(ValueError):
    pass


@dataclass(frozen=True)
class EquationProblem:
    sentence: str
    symbolic_initial: AffineState
    known_initial: tuple[Fraction | None, ...]
    unknown_entity: str
    program: Node
    observed_entity: str
    observed_value: Fraction
    query_entity: str


@dataclass(frozen=True)
class EquationSolution:
    answer: Fraction
    trace: tuple[TraceStep, ...]


@dataclass(frozen=True)
class AffineEquationMachine:
    arithmetic: ArithmeticModel

    @property
    def description_bits(self) -> int:
        payload = {
            "arithmetic_operations": self.arithmetic.operations,
            "control": {
                "sequence": self.arithmetic.discourse.sequence,
                "condition": self.arithmetic.discourse.condition,
                "negation": self.arithmetic.discourse.negation,
            },
            "affine_state": "a*x+b",
            "solve": "(observed-b)/a",
            "outer_roles": (
                "one-unknown-state",
                "program",
                "observation",
                "query",
            ),
        }
        return len(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ) * 8

    def solve(self, sentence: str) -> EquationSolution | None:
        try:
            problem = parse_problem(sentence)
            if problem.query_entity != problem.unknown_entity:
                raise ValueError("query is not the unique unknown")
            final_state, trace = symbolic_execute(
                problem.program,
                problem.symbolic_initial,
                self.arithmetic,
                "",
            )
            a, b = final_state[ENTITIES.index(problem.observed_entity)]
            if a == 0:
                raise NonUniqueEquationError(
                    "observation does not uniquely constrain the unknown"
                )
            answer = (problem.observed_value - b) / a
            trace.append(
                TraceStep.build(
                    "solve_affine",
                    observed_entity=problem.observed_entity,
                    coefficient=_fraction_text(a),
                    offset=_fraction_text(b),
                    observed_value=_fraction_text(problem.observed_value),
                    solution=_fraction_text(answer),
                )
            )
            numeric_initial = tuple(
                answer if value is None else value
                for value in problem.known_initial
            )
            final_numeric = execute(
                problem.program,
                numeric_initial,
                self.arithmetic,
            )
            if (
                final_numeric[ENTITIES.index(problem.observed_entity)]
                != problem.observed_value
            ):
                raise ValueError("symbolic solution fails numeric replay")
            return EquationSolution(answer, tuple(trace))
        except (
            KeyError,
            NonUniqueEquationError,
            TypeError,
            ValueError,
            ZeroDivisionError,
        ):
            return None


def fit_machine() -> AffineEquationMachine:
    return AffineEquationMachine(_true_model())


def _fraction_text(value: Fraction) -> str:
    return (
        str(value.numerator)
        if value.denominator == 1
        else f"{value.numerator}/{value.denominator}"
    )


def _parse_fraction(text: str) -> Fraction:
    text = _normalize_outer(text)
    if "/" in text:
        numerator, denominator = text.split("/", 1)
        return Fraction(int(numerator), int(denominator))
    return Fraction(int(text), 1)


def _parse_unknown_state(
    block: str,
) -> tuple[AffineState, tuple[Fraction | None, ...], str]:
    normalized = block.replace("，", "、").replace(",", "、")
    assignments: dict[str, Fraction | None] = {}
    for item in normalized.split("、"):
        if not item or "=" not in item:
            raise ValueError("unknown-state assignment syntax")
        entity, value = item.split("=", 1)
        if entity not in ENTITIES or entity in assignments:
            raise ValueError("unknown or duplicate entity")
        assignments[entity] = (
            None if value == "?" else _parse_fraction(value)
        )
    if set(assignments) != set(ENTITIES):
        raise ValueError("incomplete unknown state")
    unknowns = [
        entity
        for entity, value in assignments.items()
        if value is None
    ]
    if len(unknowns) != 1:
        raise ValueError("exactly one unknown required")
    unknown = unknowns[0]
    known = tuple(assignments[entity] for entity in ENTITIES)
    symbolic = tuple(
        (Fraction(1), Fraction(0))
        if entity == unknown
        else (Fraction(0), assignments[entity])
        for entity in ENTITIES
    )
    return symbolic, known, unknown


def _parse_observation(block: str) -> tuple[str, Fraction]:
    normalized = _normalize_outer(block)
    if normalized.count("=") != 1:
        raise ValueError("single observation required")
    entity, value = normalized.split("=", 1)
    if entity not in ENTITIES or value == "?":
        raise ValueError("invalid observation")
    return entity, _parse_fraction(value)


def parse_problem(sentence: str) -> EquationProblem:
    blocks = _outer_blocks(sentence)
    if len(blocks) != 4:
        raise ValueError("four semantic blocks required")
    states = []
    programs = []
    observations = []
    queries = []
    for index, block in enumerate(blocks):
        try:
            states.append((index, *_parse_unknown_state(block)))
        except (TypeError, ValueError):
            pass
        try:
            programs.append((index, parse_program(block)))
        except ValueError:
            pass
        try:
            observations.append((index, *_parse_observation(block)))
        except (TypeError, ValueError):
            pass
        normalized = _normalize_outer(block)
        if normalized in ENTITIES:
            queries.append((index, normalized))
    if not (
        len(states)
        == len(programs)
        == len(observations)
        == len(queries)
        == 1
    ):
        raise ValueError("ambiguous equation problem block roles")
    indices = {
        states[0][0],
        programs[0][0],
        observations[0][0],
        queries[0][0],
    }
    if len(indices) != 4:
        raise ValueError("equation problem roles overlap")
    _, symbolic, known, unknown = states[0]
    _, program = programs[0]
    _, observed_entity, observed_value = observations[0]
    _, query = queries[0]
    return EquationProblem(
        sentence,
        symbolic,
        known,
        unknown,
        program,
        observed_entity,
        observed_value,
        query,
    )


def render_problem(
    known_initial: Sequence[Fraction | int | None],
    program: Node,
    observed_entity: str,
    observed_value: Fraction | int,
    query_entity: str,
    index: int,
) -> str:
    assignment = "、".join(
        f"{entity}={'?' if value is None else _fraction_text(Fraction(value))}"
        for entity, value in zip(ENTITIES, known_initial)
    )
    labels = (
        ("開始値", "実行した操作", "最後の観測", "求める初期値"),
        ("はじめの状態", "計算の流れ", "結果", "質問"),
        ("初期条件", "処理", "判明した値", "未知数の持ち主"),
    )[index % 3]
    return (
        f"{labels[0]}【{assignment}】。"
        f"{labels[1]}【{render(program)}】。"
        f"{labels[2]}【{observed_entity}="
        f"{_fraction_text(Fraction(observed_value))}】。"
        f"{labels[3]}【{query_entity}】。"
    )


def _affine_apply(
    value: Affine,
    amount: int,
    operation: str,
) -> Affine:
    a, b = value
    if operation == "ADD":
        return a, b + amount
    if operation == "SUB":
        return a, b - amount
    if operation == "MUL":
        return a * amount, b * amount
    raise ValueError(operation)


def _condition_value(
    first: Affine,
    second: Affine,
    relation: str,
) -> bool:
    if first == second:
        equal = True
    elif first[0] == 0 and second[0] == 0:
        equal = first[1] == second[1]
    else:
        raise NonUniqueEquationError("condition depends on unknown value")
    if relation == "EQ":
        return equal
    if relation == "NEQ":
        return not equal
    raise ValueError("unknown condition")


def symbolic_execute(
    node: Node,
    state: AffineState,
    model: ArithmeticModel,
    path: str,
) -> tuple[AffineState, list[TraceStep]]:
    if isinstance(node, ArithmeticNode):
        operation = dict(model.operations).get(node.label)
        if operation is None:
            raise ValueError("unknown arithmetic label")
        index = ENTITIES.index(node.target)
        before = state[index]
        after = _affine_apply(before, node.amount, operation)
        output = list(state)
        output[index] = after
        return tuple(output), [
            TraceStep.build(
                "symbolic_arithmetic",
                path=path,
                target=node.target,
                label=node.label,
                operation=operation,
                amount=node.amount,
                before_coefficient=_fraction_text(before[0]),
                before_offset=_fraction_text(before[1]),
                after_coefficient=_fraction_text(after[0]),
                after_offset=_fraction_text(after[1]),
            )
        ]

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
            child_state, child_trace = symbolic_execute(
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
            children = (
                (node.left, path + "L"),
                (node.right, path + "R"),
            )
        elif order == "RL":
            children = (
                (node.right, path + "R"),
                (node.left, path + "L"),
            )
        else:
            raise ValueError("unknown sequence")
        current = state
        for child, child_path in children:
            current, child_trace = symbolic_execute(
                child,
                current,
                model,
                child_path,
            )
            trace.extend(child_trace)
        return current, trace

    if isinstance(node, ConditionalNode):
        relation = dict(model.discourse.condition).get(node.label)
        first = state[ENTITIES.index(node.first_entity)]
        second = state[ENTITIES.index(node.second_entity)]
        test = _condition_value(first, second, relation)
        branch = "Y" if test else "N"
        trace = [
            TraceStep.build(
                "symbolic_condition",
                path=path,
                label=node.label,
                relation=relation,
                first_entity=node.first_entity,
                second_entity=node.second_entity,
                first_expression=(
                    f"{_fraction_text(first[0])}x+"
                    f"{_fraction_text(first[1])}"
                ),
                second_expression=(
                    f"{_fraction_text(second[0])}x+"
                    f"{_fraction_text(second[1])}"
                ),
                branch=branch,
            )
        ]
        child_state, child_trace = symbolic_execute(
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

    def consume(self, expected: TraceStep) -> None:
        if (
            self.index >= len(self.steps)
            or self.steps[self.index] != expected
        ):
            raise ValueError("trace mismatch")
        self.index += 1


def verify_solution(
    sentence: str,
    solution: EquationSolution,
    model: ArithmeticModel,
) -> bool:
    try:
        problem = parse_problem(sentence)
        if problem.query_entity != problem.unknown_entity:
            return False
        final, expected_trace = symbolic_execute(
            problem.program,
            problem.symbolic_initial,
            model,
            "",
        )
        cursor = _Cursor(solution.trace)
        for step in expected_trace:
            cursor.consume(step)
        a, b = final[ENTITIES.index(problem.observed_entity)]
        if a == 0:
            return False
        expected = (problem.observed_value - b) / a
        cursor.consume(
            TraceStep.build(
                "solve_affine",
                observed_entity=problem.observed_entity,
                coefficient=_fraction_text(a),
                offset=_fraction_text(b),
                observed_value=_fraction_text(problem.observed_value),
                solution=_fraction_text(expected),
            )
        )
        if (
            cursor.index != len(cursor.steps)
            or solution.answer != expected
        ):
            return False
        numeric_initial = tuple(
            expected if value is None else value
            for value in problem.known_initial
        )
        numeric_final = execute(problem.program, numeric_initial, model)
        return (
            numeric_final[ENTITIES.index(problem.observed_entity)]
            == problem.observed_value
        )
    except (
        KeyError,
        NonUniqueEquationError,
        TypeError,
        ValueError,
        ZeroDivisionError,
    ):
        return False


def _programs() -> tuple[tuple[str, Node], ...]:
    from .phase18b2_induced_integer_operations import (
        arithmetic,
        condition,
        negate,
        sequence,
    )

    return (
        (
            "アキ",
            sequence(
                "続いて",
                arithmetic("アキ", 5, "増やす"),
                arithmetic("アキ", 3, "倍にする"),
            ),
        ),
        (
            "ボブ",
            sequence(
                "先立ち",
                arithmetic("ボブ", 4, "減らす"),
                arithmetic("ボブ", 2, "倍にする"),
            ),
        ),
        (
            "チカ",
            sequence(
                "続いて",
                arithmetic("チカ", 5, "倍にする"),
                arithmetic("チカ", 7, "減らす"),
            ),
        ),
        (
            "ダイ",
            sequence(
                "続いて",
                arithmetic("ダイ", 9, "増やす"),
                sequence(
                    "先立ち",
                    arithmetic("ダイ", 2, "倍にする"),
                    arithmetic("ダイ", 3, "減らす"),
                ),
            ),
        ),
        (
            "エリ",
            condition(
                "同じなら",
                "アキ",
                "ボブ",
                sequence(
                    "続いて",
                    arithmetic("エリ", 4, "倍にする"),
                    arithmetic("エリ", 3, "増やす"),
                ),
                arithmetic("エリ", 8, "減らす"),
            ),
        ),
        (
            "フミ",
            sequence(
                "続いて",
                arithmetic("フミ", 2, "倍にする"),
                negate(
                    sequence(
                        "続いて",
                        arithmetic("フミ", 100, "増やす"),
                        arithmetic("フミ", 5, "減らす"),
                    )
                ),
            ),
        ),
    )


def heldout_problems() -> tuple[tuple[str, Fraction], ...]:
    model = _true_model()
    rng = random.Random(8183)
    rows: list[tuple[str, Fraction]] = []
    solutions = (
        Fraction(3, 2),
        Fraction(-5, 2),
        Fraction(7, 3),
        Fraction(-4),
        Fraction(11, 4),
        Fraction(5, 2),
    )
    for cell, ((unknown, program), answer) in enumerate(
        zip(_programs(), solutions)
    ):
        for variant in range(2):
            known: list[Fraction | None] = [
                Fraction(rng.randint(-6, 8))
                for _ in ENTITIES
            ]
            known[ENTITIES.index(unknown)] = None
            if cell == 4:
                known[ENTITIES.index("アキ")] = Fraction(2 + variant)
                known[ENTITIES.index("ボブ")] = Fraction(
                    2 if variant == 0 else 5
                )
            numeric_initial = tuple(
                answer if value is None else value
                for value in known
            )
            final = execute(program, numeric_initial, model)
            observed = final[ENTITIES.index(unknown)]
            rows.append(
                (
                    render_problem(
                        known,
                        program,
                        unknown,
                        observed,
                        unknown,
                        100 + cell + variant,
                    ),
                    answer,
                )
            )
    return tuple(rows)


def calibration_problems() -> tuple[tuple[str, Fraction], ...]:
    model = _true_model()
    rows: list[tuple[str, Fraction]] = []
    for index, (unknown, program) in enumerate(_programs()):
        answer = Fraction(index + 2)
        known: list[Fraction | None] = [
            Fraction(index + coordinate + 1)
            for coordinate in range(len(ENTITIES))
        ]
        known[ENTITIES.index(unknown)] = None
        if index == 4:
            known[0] = known[1] = Fraction(3)
        numeric = tuple(
            answer if value is None else value
            for value in known
        )
        final = execute(program, numeric, model)
        observed = final[ENTITIES.index(unknown)]
        rows.append(
            (
                render_problem(
                    known,
                    program,
                    unknown,
                    observed,
                    unknown,
                    index,
                ),
                answer,
            )
        )
    return tuple(rows)


def memorizer_coverage(
    train: Iterable[tuple[str, Fraction]],
    test: Iterable[tuple[str, Fraction]],
) -> float:
    known = {_normalize_outer(problem) for problem, _ in train}
    test = tuple(test)
    return sum(
        _normalize_outer(problem) in known
        for problem, _ in test
    ) / len(test)


def observed_value_baseline_accuracy(
    rows: Iterable[tuple[str, Fraction]],
) -> float:
    rows = tuple(rows)
    return sum(
        parse_problem(problem).observed_value == answer
        for problem, answer in rows
    ) / len(rows)


def counterfactual_observation_sensitivity(
    machine: AffineEquationMachine,
) -> float:
    rows = heldout_problems()
    changed = 0
    for problem, _ in rows:
        parsed = parse_problem(problem)
        base = machine.solve(problem)
        if base is None:
            continue
        altered = render_problem(
            parsed.known_initial,
            parsed.program,
            parsed.observed_entity,
            parsed.observed_value + 1,
            parsed.query_entity,
            999,
        )
        other = machine.solve(altered)
        changed += (
            other is not None
            and other.answer != base.answer
            and verify_solution(altered, other, machine.arithmetic)
        )
    return changed / len(rows)


def invalid_equations_abstain(
    machine: AffineEquationMachine,
) -> dict[str, bool]:
    from .phase18b2_induced_integer_operations import arithmetic, condition

    known: list[Fraction | None] = [
        None,
        Fraction(1),
        Fraction(2),
        Fraction(3),
        Fraction(4),
        Fraction(5),
    ]
    zero_coefficient = arithmetic("アキ", 0, "倍にする")
    no_unique = render_problem(
        known,
        zero_coefficient,
        "アキ",
        0,
        "アキ",
        0,
    )
    inconsistent = render_problem(
        known,
        zero_coefficient,
        "アキ",
        1,
        "アキ",
        1,
    )
    two_unknown = render_problem(
        [None, None, 2, 3, 4, 5],
        arithmetic("アキ", 2, "増やす"),
        "アキ",
        4,
        "アキ",
        2,
    )
    unknown_condition = condition(
        "同じなら",
        "アキ",
        "ボブ",
        arithmetic("アキ", 1, "増やす"),
        arithmetic("アキ", 1, "減らす"),
    )
    condition_problem = render_problem(
        known,
        unknown_condition,
        "アキ",
        4,
        "アキ",
        3,
    )
    wrong_query = render_problem(
        known,
        arithmetic("アキ", 2, "増やす"),
        "アキ",
        5,
        "ボブ",
        4,
    )
    return {
        "zero_coefficient_infinite_or_none": (
            machine.solve(no_unique) is None
            and machine.solve(inconsistent) is None
        ),
        "two_unknowns": machine.solve(two_unknown) is None,
        "condition_depending_on_unknown": (
            machine.solve(condition_problem) is None
        ),
        "query_must_match_unknown": machine.solve(wrong_query) is None,
    }


def tampered_trace_rejected(
    problem: str,
    solution: EquationSolution,
    model: ArithmeticModel,
) -> bool:
    steps = list(solution.trace)
    target = next(
        (
            index
            for index, step in enumerate(steps)
            if step.kind == "symbolic_arithmetic"
        ),
        None,
    )
    if target is None:
        return False
    data = dict(steps[target].data)
    data["after_offset"] = "999"
    steps[target] = TraceStep.build("symbolic_arithmetic", **data)
    return not verify_solution(
        problem,
        EquationSolution(solution.answer, tuple(steps)),
        model,
    )


def run() -> dict[str, object]:
    machine = fit_machine()
    calibration = calibration_problems()
    heldout = heldout_problems()
    solutions = tuple(
        machine.solve(problem)
        for problem, _ in heldout
    )
    answered = sum(solution is not None for solution in solutions)
    correct = sum(
        solution is not None and solution.answer == expected
        for solution, (_, expected) in zip(solutions, heldout)
    )
    verified = sum(
        solution is not None
        and verify_solution(problem, solution, machine.arithmetic)
        for solution, (problem, _) in zip(solutions, heldout)
    )
    tampered = all(
        solution is not None
        and tampered_trace_rejected(
            problem,
            solution,
            machine.arithmetic,
        )
        for solution, (problem, _) in zip(solutions, heldout)
    )
    wrong = all(
        solution is not None
        and not verify_solution(
            problem,
            replace(solution, answer=solution.answer + 1),
            machine.arithmetic,
        )
        for solution, (problem, _) in zip(solutions, heldout)
    )
    empty = all(
        solution is not None
        and not verify_solution(
            problem,
            EquationSolution(solution.answer, ()),
            machine.arithmetic,
        )
        for solution, (problem, _) in zip(solutions, heldout)
    )
    invalid = invalid_equations_abstain(machine)
    sensitivity = counterfactual_observation_sensitivity(machine)
    memorizer = memorizer_coverage(calibration, heldout)
    baseline = observed_value_baseline_accuracy(heldout)
    trace_lengths = tuple(
        len(solution.trace)
        for solution in solutions
        if solution is not None
    )
    checks = {
        "affine_equations_are_solved_exactly": (
            correct == answered == len(heldout)
        ),
        "all_derivations_verify": verified == len(heldout),
        "rational_and_negative_solutions_are_supported": (
            any(expected.denominator != 1 for _, expected in heldout)
            and any(expected < 0 for _, expected in heldout)
        ),
        "whole_problem_memorizer_has_zero_coverage": memorizer == 0,
        "observed_value_baseline_is_below_half": baseline < 0.5,
        "empty_trace_is_rejected": empty,
        "tampered_trace_is_rejected": tampered,
        "wrong_solution_is_rejected": wrong,
        "observation_counterfactual_changes_solution": sensitivity == 1,
        "invalid_or_nonunique_equations_abstain": all(invalid.values()),
        "trace_length_is_bounded": max(trace_lengths) <= 8,
    }
    return {
        "campaign": {
            "name": "phase18b3-symbolic-affine-equation-solving-c1",
            "inherits": (
                "Phase 18b-2 arithmetic lexemes and control semantics"
            ),
            "exposed_forward_initial_value": False,
            "public_examples": 0,
        },
        "evaluation": {
            "calibration_problems": len(calibration),
            "heldout_problems": len(heldout),
            "accuracy": correct / len(heldout),
            "coverage": answered / len(heldout),
            "verification_rate": verified / len(heldout),
            "memorizer_coverage": memorizer,
            "observed_value_baseline": baseline,
            "counterfactual_sensitivity": sensitivity,
            "min_trace_steps": min(trace_lengths),
            "max_trace_steps": max(trace_lengths),
            "mean_trace_steps": sum(trace_lengths) / len(trace_lengths),
        },
        "invalid_controls": invalid,
        "resources": {
            "model_bits": machine.description_bits,
            "source_bytes": Path(__file__).read_bytes().__len__(),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "controlled_affine_equation_solving": all(checks.values()),
            "natural_word_problems": False,
            "general_algebra": False,
            "high_school_mathematics": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "four bracketed semantic blocks expose the unknown state, program, observation, and query",
            "only one unknown and affine operations are supported",
            "conditions depending on the unknown are rejected",
            "operation meanings and control semantics are inherited",
            "no equation extraction from ordinary prose, geometry, proof, or world knowledge",
            "Python runtime and fixed parser are excluded from learned payload",
        ],
    }


def render_markdown(payload: Mapping[str, object]) -> str:
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18b-3 results: symbolic affine equation solving

- Calibration / held-out equations: **{evaluation["calibration_problems"]} / {evaluation["heldout_problems"]}**
- Accuracy / coverage: **{100 * evaluation["accuracy"]:.1f}% / {100 * evaluation["coverage"]:.1f}%**
- Independently verified derivations: **{100 * evaluation["verification_rate"]:.1f}%**
- Whole-problem memorizer coverage: **{100 * evaluation["memorizer_coverage"]:.1f}%**
- Observed-value-as-answer baseline: **{100 * evaluation["observed_value_baseline"]:.1f}%**
- Observation counterfactual sensitivity: **{100 * evaluation["counterfactual_sensitivity"]:.1f}%**
- Trace steps min / mean / max: **{evaluation["min_trace_steps"]} / {evaluation["mean_trace_steps"]:.2f} / {evaluation["max_trace_steps"]}**
- Learned payload: **{resources["model_bits"]} bits**

The machine constructs and solves exact one-variable affine equations from a
text-embedded unknown initial state and final observation. This is still a
bracketed controlled algebra task, not natural Japanese word-problem or
high-school mathematics ability.
"""


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(exist_ok=True)
    (output / "phase18b3.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase18b3.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
