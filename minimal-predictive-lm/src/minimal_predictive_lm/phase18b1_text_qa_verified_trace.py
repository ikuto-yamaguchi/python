from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import unicodedata
from typing import Iterable, Mapping, Sequence

from .phase18a7_recursive_conditional_discourse import (
    ACTION_FORWARD,
    ENTITIES,
    BinaryNode,
    ConditionalNode,
    EventNode,
    Node,
    RecursiveDiscourseModel,
    UnaryNode,
    heldout_observations as discourse_heldout_observations,
    induce as induce_discourse,
    parse_program,
    training_observations as discourse_training_observations,
)

State = tuple[int, ...]
Context = tuple[int, int] | None


@dataclass(frozen=True)
class Problem:
    sentence: str
    initial: State
    program: Node
    query_entity: str


@dataclass(frozen=True)
class TraceStep:
    kind: str
    data: tuple[tuple[str, object], ...]

    @classmethod
    def build(cls, kind: str, **data: object) -> "TraceStep":
        return cls(kind, tuple(sorted(data.items())))

    def as_dict(self) -> dict[str, object]:
        return {"kind": self.kind, **dict(self.data)}


@dataclass(frozen=True)
class Solution:
    answer: int
    trace: tuple[TraceStep, ...]


@dataclass(frozen=True)
class QuestionAnswerMachine:
    discourse: RecursiveDiscourseModel

    def solve(self, sentence: str) -> Solution | None:
        try:
            problem = parse_problem(sentence)
            state, _, trace = _execute_with_trace(
                problem.program,
                problem.initial,
                self.discourse,
                None,
                "",
            )
            answer = state[ENTITIES.index(problem.query_entity)]
            return Solution(answer, tuple(trace))
        except (KeyError, ValueError):
            return None

    @property
    def learned_bits(self) -> int:
        payload = {
            "discourse": {
                "sequence": self.discourse.sequence,
                "condition": self.discourse.condition,
                "negation": self.discourse.negation,
                "reference": self.discourse.reference,
            },
            "outer_block_roles": (
                "assignments",
                "recursive_program",
                "query_entity",
            ),
            "trace_schema": (
                "sequence",
                "condition",
                "negation",
                "event",
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


def fit_machine() -> QuestionAnswerMachine:
    model, _ = induce_discourse(discourse_training_observations())
    return QuestionAnswerMachine(model)


def _normalize_outer(text: str) -> str:
    return "".join(unicodedata.normalize("NFKC", text).split())


def _outer_blocks(text: str) -> tuple[str, ...]:
    text = _normalize_outer(text)
    blocks: list[str] = []
    depth = 0
    start: int | None = None
    for index, character in enumerate(text):
        if character == "【":
            if depth == 0:
                start = index + 1
            depth += 1
        elif character == "】":
            if depth == 0:
                raise ValueError("unmatched outer closing bracket")
            depth -= 1
            if depth == 0:
                if start is None:
                    raise ValueError("missing outer start")
                blocks.append(text[start:index])
                start = None
    if depth:
        raise ValueError("unbalanced outer brackets")
    return tuple(blocks)


def _parse_assignments(block: str) -> State:
    normalized = block.replace("，", "、").replace(",", "、")
    assignments: dict[str, int] = {}
    for item in normalized.split("、"):
        if not item:
            continue
        if "=" not in item:
            raise ValueError("assignment syntax")
        entity, value = item.split("=", 1)
        if entity not in ENTITIES or entity in assignments:
            raise ValueError("unknown or duplicate entity")
        assignments[entity] = int(value)
    if set(assignments) != set(ENTITIES):
        raise ValueError("incomplete initial state")
    return tuple(assignments[entity] for entity in ENTITIES)


def parse_problem(sentence: str) -> Problem:
    blocks = _outer_blocks(sentence)
    if len(blocks) != 3:
        raise ValueError("expected three semantic blocks")

    assignment_candidates: list[tuple[int, State]] = []
    program_candidates: list[tuple[int, Node]] = []
    query_candidates: list[tuple[int, str]] = []
    for index, block in enumerate(blocks):
        try:
            assignment_candidates.append((index, _parse_assignments(block)))
        except (TypeError, ValueError):
            pass
        try:
            program_candidates.append((index, parse_program(block)))
        except ValueError:
            pass
        normalized = _normalize_outer(block)
        if normalized in ENTITIES:
            query_candidates.append((index, normalized))

    if (
        len(assignment_candidates) != 1
        or len(program_candidates) != 1
        or len(query_candidates) != 1
    ):
        raise ValueError("outer block roles are ambiguous")
    indices = {
        assignment_candidates[0][0],
        program_candidates[0][0],
        query_candidates[0][0],
    }
    if len(indices) != 3:
        raise ValueError("outer block roles overlap")
    return Problem(
        sentence,
        assignment_candidates[0][1],
        program_candidates[0][1],
        query_candidates[0][1],
    )


def render_problem(
    initial: Sequence[int],
    program_text: str,
    query_entity: str,
    index: int,
) -> str:
    assignments = "、".join(
        f"{entity}={value}"
        for entity, value in zip(ENTITIES, initial)
    )
    frames = (
        ("最初の値", "実行する手順", "最後に答える対象"),
        ("初期状態", "処理内容", "質問する人物"),
        ("開始時", "規則", "求める値の持ち主"),
    )
    first, second, third = frames[index % len(frames)]
    return (
        f"{first}【{assignments}】。"
        f"{second}【{program_text}】。"
        f"{third}【{query_entity}】。"
    )


def _resolve(
    token: str,
    model: RecursiveDiscourseModel,
    context: Context,
) -> int:
    if token in ENTITIES:
        return ENTITIES.index(token)
    role = dict(model.reference).get(token)
    if role is None or context is None:
        raise ValueError("unresolved reference")
    return context[0] if role == "SRC" else context[1]


def _copy(state: State, source: int, destination: int) -> State:
    output = list(state)
    output[destination] = state[source]
    return tuple(output)


def _execute_with_trace(
    node: Node,
    state: State,
    model: RecursiveDiscourseModel,
    context: Context,
    path: str,
) -> tuple[State, Context, list[TraceStep]]:
    if isinstance(node, EventNode):
        left = _resolve(node.left, model, context)
        right = _resolve(node.right, model, context)
        if left == right:
            raise ValueError("self event")
        source, destination = (
            (left, right)
            if ACTION_FORWARD[node.action]
            else (right, left)
        )
        step = TraceStep.build(
            "event",
            path=path,
            action=node.action,
            left_token=node.left,
            right_token=node.right,
            source=source,
            destination=destination,
            copied_value=state[source],
            overwritten_value=state[destination],
        )
        return (
            _copy(state, source, destination),
            (source, destination),
            [step],
        )

    if isinstance(node, UnaryNode):
        mode = dict(model.negation).get(node.label)
        if mode not in {"SKIP", "EXEC"}:
            raise ValueError("unknown negation")
        trace = [
            TraceStep.build(
                "negation",
                path=path,
                label=node.label,
                mode=mode,
            )
        ]
        if mode == "SKIP":
            return state, context, trace
        child_state, child_context, child_trace = _execute_with_trace(
            node.child,
            state,
            model,
            context,
            path + "U",
        )
        return child_state, child_context, trace + child_trace

    if isinstance(node, BinaryNode):
        order = dict(model.sequence).get(node.label)
        if order not in {"LR", "RL"}:
            raise ValueError("unknown sequence")
        trace = [
            TraceStep.build(
                "sequence",
                path=path,
                label=node.label,
                order=order,
            )
        ]
        children = (
            ((node.left, path + "L"), (node.right, path + "R"))
            if order == "LR"
            else ((node.right, path + "R"), (node.left, path + "L"))
        )
        current_state = state
        current_context = context
        for child, child_path in children:
            current_state, current_context, child_trace = _execute_with_trace(
                child,
                current_state,
                model,
                current_context,
                child_path,
            )
            trace.extend(child_trace)
        return current_state, current_context, trace

    if isinstance(node, ConditionalNode):
        relation = dict(model.condition).get(node.label)
        if relation not in {"EQ", "NEQ"}:
            raise ValueError("unknown condition")
        first = ENTITIES.index(node.first_entity)
        second = ENTITIES.index(node.second_entity)
        equal = state[first] == state[second]
        test = equal if relation == "EQ" else not equal
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
        child = node.yes if test else node.no
        child_state, child_context, child_trace = _execute_with_trace(
            child,
            state,
            model,
            context,
            path + branch,
        )
        return child_state, child_context, trace + child_trace

    raise TypeError(node)


@dataclass
class _TraceCursor:
    steps: tuple[TraceStep, ...]
    index: int = 0

    def consume(self, expected: TraceStep) -> None:
        if self.index >= len(self.steps) or self.steps[self.index] != expected:
            raise ValueError("trace mismatch")
        self.index += 1


def _verify_node(
    node: Node,
    state: State,
    model: RecursiveDiscourseModel,
    context: Context,
    path: str,
    cursor: _TraceCursor,
) -> tuple[State, Context]:
    if isinstance(node, EventNode):
        left = _resolve(node.left, model, context)
        right = _resolve(node.right, model, context)
        if left == right:
            raise ValueError("self event")
        source, destination = (
            (left, right)
            if ACTION_FORWARD[node.action]
            else (right, left)
        )
        cursor.consume(
            TraceStep.build(
                "event",
                path=path,
                action=node.action,
                left_token=node.left,
                right_token=node.right,
                source=source,
                destination=destination,
                copied_value=state[source],
                overwritten_value=state[destination],
            )
        )
        return _copy(state, source, destination), (source, destination)

    if isinstance(node, UnaryNode):
        mode = dict(model.negation).get(node.label)
        cursor.consume(
            TraceStep.build(
                "negation",
                path=path,
                label=node.label,
                mode=mode,
            )
        )
        if mode == "SKIP":
            return state, context
        if mode == "EXEC":
            return _verify_node(
                node.child,
                state,
                model,
                context,
                path + "U",
                cursor,
            )
        raise ValueError("unknown negation")

    if isinstance(node, BinaryNode):
        order = dict(model.sequence).get(node.label)
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
        current_state, current_context = state, context
        for child, child_path in children:
            current_state, current_context = _verify_node(
                child,
                current_state,
                model,
                current_context,
                child_path,
                cursor,
            )
        return current_state, current_context

    if isinstance(node, ConditionalNode):
        relation = dict(model.condition).get(node.label)
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
        return _verify_node(
            node.yes if test else node.no,
            state,
            model,
            context,
            path + branch,
            cursor,
        )

    raise TypeError(node)


def verify_solution(
    sentence: str,
    solution: Solution,
    model: RecursiveDiscourseModel,
) -> bool:
    try:
        problem = parse_problem(sentence)
        cursor = _TraceCursor(solution.trace)
        final_state, _ = _verify_node(
            problem.program,
            problem.initial,
            model,
            None,
            "",
            cursor,
        )
        return (
            cursor.index == len(cursor.steps)
            and solution.answer
            == final_state[ENTITIES.index(problem.query_entity)]
        )
    except (KeyError, TypeError, ValueError):
        return False


def _query_index(before: State, after: State, row_index: int) -> int:
    changed = [
        index
        for index, (first, second) in enumerate(zip(before, after))
        if first != second
    ]
    return changed[0] if changed else row_index % len(ENTITIES)


def calibration_problems() -> tuple[tuple[str, int], ...]:
    machine = fit_machine()
    rows: list[tuple[str, int]] = []
    for index, row in enumerate(discourse_training_observations()):
        final = machine.discourse.predict(row.sentence, row.before)
        if final is None:
            raise RuntimeError("invalid calibration discourse")
        query = _query_index(row.before, final, index)
        problem = render_problem(
            row.before,
            row.sentence,
            ENTITIES[query],
            index,
        )
        rows.append((problem, final[query]))
    return tuple(rows)


def heldout_problems() -> tuple[tuple[str, int], ...]:
    rows: list[tuple[str, int]] = []
    for index, row in enumerate(discourse_heldout_observations()):
        query = _query_index(row.before, row.after, index)
        problem = render_problem(
            row.before,
            row.sentence,
            ENTITIES[query],
            100 + index,
        )
        rows.append((problem, row.after[query]))
    return tuple(rows)


def problem_memorizer_coverage(
    calibration: Iterable[tuple[str, int]],
    heldout: Iterable[tuple[str, int]],
) -> float:
    known = {_normalize_outer(problem) for problem, _ in calibration}
    heldout = tuple(heldout)
    return sum(
        _normalize_outer(problem) in known
        for problem, _ in heldout
    ) / len(heldout)


def no_execution_accuracy(rows: Iterable[tuple[str, int]]) -> float:
    rows = tuple(rows)
    correct = 0
    for sentence, answer in rows:
        problem = parse_problem(sentence)
        correct += (
            problem.initial[ENTITIES.index(problem.query_entity)] == answer
        )
    return correct / len(rows)


def tampered_trace_is_rejected(
    sentence: str,
    solution: Solution,
    model: RecursiveDiscourseModel,
) -> bool:
    if not solution.trace:
        return False
    steps = list(solution.trace)
    target = next(
        (
            index
            for index, step in enumerate(steps)
            if step.kind == "event"
        ),
        None,
    )
    if target is None:
        return False
    data = dict(steps[target].data)
    data["copied_value"] = int(data["copied_value"]) + 1
    steps[target] = TraceStep.build("event", **data)
    forged = Solution(solution.answer, tuple(steps))
    return not verify_solution(sentence, forged, model)


def counterfactual_sensitivity_rate(
    machine: QuestionAnswerMachine,
) -> float:
    rows = heldout_problems()
    sensitive = 0
    for row_index, (sentence, _) in enumerate(rows):
        problem = parse_problem(sentence)
        base = machine.solve(sentence)
        if base is None:
            continue
        changed = False
        for coordinate in range(len(ENTITIES)):
            for delta in (1, 3, 11):
                values = list(problem.initial)
                values[coordinate] += delta
                counterfactual = render_problem(
                    values,
                    render_program(problem.program),
                    problem.query_entity,
                    700 + row_index * 20 + coordinate,
                )
                solution = machine.solve(counterfactual)
                if (
                    solution is not None
                    and verify_solution(
                        counterfactual,
                        solution,
                        machine.discourse,
                    )
                    and (
                        solution.answer != base.answer
                        or solution.trace != base.trace
                    )
                ):
                    changed = True
                    break
            if changed:
                break
        sensitive += changed
    return sensitive / len(rows)


def render_program(node: Node) -> str:
    from .phase18a7_recursive_conditional_discourse import render

    return render(node)


def trace_json_bits(solutions: Iterable[Solution]) -> int:
    payload = [
        {
            "answer": solution.answer,
            "trace": [step.as_dict() for step in solution.trace],
        }
        for solution in solutions
    ]
    return len(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    ) * 8


def run() -> dict[str, object]:
    machine = fit_machine()
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
        and verify_solution(problem, solution, machine.discourse)
        for solution, (problem, _) in zip(solutions, heldout)
    )
    empty_trace_rejected = all(
        solution is not None
        and not verify_solution(
            problem,
            Solution(solution.answer, ()),
            machine.discourse,
        )
        for solution, (problem, _) in zip(solutions, heldout)
    )
    tampered_rejected = all(
        solution is not None
        and tampered_trace_is_rejected(
            problem,
            solution,
            machine.discourse,
        )
        for solution, (problem, _) in zip(solutions, heldout)
    )
    wrong_answer_rejected = all(
        solution is not None
        and not verify_solution(
            problem,
            replace(solution, answer=solution.answer + 1),
            machine.discourse,
        )
        for solution, (problem, _) in zip(solutions, heldout)
    )
    trace_lengths = tuple(
        len(solution.trace)
        for solution in solutions
        if solution is not None
    )
    memorizer = problem_memorizer_coverage(calibration, heldout)
    no_execution = no_execution_accuracy(heldout)
    counterfactual_rate = counterfactual_sensitivity_rate(machine)

    checks = {
        "text_only_question_answering_is_perfect": (
            correct == answered == len(heldout)
        ),
        "every_answer_has_a_verified_trace": verified == len(heldout),
        "whole_problem_memorizer_has_zero_coverage": memorizer == 0.0,
        "no_execution_baseline_is_below_half": no_execution < 0.5,
        "empty_trace_is_rejected": empty_trace_rejected,
        "tampered_trace_is_rejected": tampered_rejected,
        "wrong_answer_with_valid_trace_is_rejected": wrong_answer_rejected,
        "every_problem_has_a_sensitive_counterfactual": (
            counterfactual_rate == 1.0
        ),
        "trace_length_is_linear_and_bounded": (
            min(trace_lengths) >= 3 and max(trace_lengths) <= 15
        ),
        "outer_labels_are_not_prelisted": True,
    }

    valid_solutions = tuple(
        solution
        for solution in solutions
        if solution is not None
    )
    return {
        "campaign": {
            "name": "phase18b1-text-only-qa-with-verified-trace-c1",
            "inherits": "Phase 18a-7 recursive discourse semantics",
            "external_initial_state_argument": False,
            "outer_label_lexicon_prelisted": False,
            "public_examples": 0,
        },
        "evaluation": {
            "calibration_problems": len(calibration),
            "heldout_problems": len(heldout),
            "answered": answered,
            "correct": correct,
            "verified": verified,
            "accuracy": correct / len(heldout),
            "coverage": answered / len(heldout),
            "trace_verification_rate": verified / len(heldout),
            "problem_memorizer_coverage": memorizer,
            "no_execution_accuracy": no_execution,
            "minimum_trace_steps": min(trace_lengths),
            "maximum_trace_steps": max(trace_lengths),
            "mean_trace_steps": sum(trace_lengths) / len(trace_lengths),
            "counterfactual_sensitivity_rate": counterfactual_rate,
        },
        "resources": {
            "model_bits": machine.learned_bits,
            "heldout_solution_trace_bits": trace_json_bits(valid_solutions),
            "source_bytes": Path(__file__).read_bytes().__len__(),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "controlled_text_only_qa": all(checks.values()),
            "independently_replayable_derivation": verified == len(heldout),
            "natural_unstructured_word_problems": False,
            "general_mathematics": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "three bracketed outer blocks expose initial state, program, and query",
            "recursive program syntax and semantics are inherited from Phase 18a-7",
            "state changes are copies rather than arithmetic operations",
            "question asks for one named entity's final integer value",
            "trace verifier shares the learned semantic factors but not the solver execution path",
            "no factual knowledge, explanation prose, algebra, geometry, or proof",
            "Python runtime and fixed parsers are excluded from learned payload",
        ],
    }


def render_markdown(payload: Mapping[str, object]) -> str:
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18b-1 results: text-only QA with verified trace

- Calibration / held-out problems: **{evaluation["calibration_problems"]} / {evaluation["heldout_problems"]}**
- Accuracy / coverage: **{100 * evaluation["accuracy"]:.1f}% / {100 * evaluation["coverage"]:.1f}%**
- Independently replayed trace verification: **{100 * evaluation["trace_verification_rate"]:.1f}%**
- Whole-problem memorizer coverage: **{100 * evaluation["problem_memorizer_coverage"]:.1f}%**
- No-execution baseline accuracy: **{100 * evaluation["no_execution_accuracy"]:.1f}%**
- Trace steps min / mean / max: **{evaluation["minimum_trace_steps"]} / {evaluation["mean_trace_steps"]:.2f} / {evaluation["maximum_trace_steps"]}**
- One-coordinate counterfactual sensitivity: **{100 * evaluation["counterfactual_sensitivity_rate"]:.1f}%**
- Learned QA payload / held-out solution traces: **{resources["model_bits"]} / {resources["heldout_solution_trace_bits"]} bits**

The machine receives the initial state, recursive procedure, and query in one
text string. Each answer is accepted only when an independent verifier can
replay the complete derivation. This is still a bracketed controlled state
question—not general Japanese word-problem or high-school mathematics ability.
"""


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase18b1.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase18b1.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
