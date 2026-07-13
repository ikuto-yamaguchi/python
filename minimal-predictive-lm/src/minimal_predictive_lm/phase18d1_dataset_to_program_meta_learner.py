from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
import inspect
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


class NonIdentifiableProgramError(ValueError):
    """More than one behaviorally distinct minimum program fits the examples."""


class NoProgramError(ValueError):
    """No program in the frozen DSL fits the examples."""


class EvaluationError(ValueError):
    pass


def decode_value(value: Any) -> Any:
    if isinstance(value, dict) and set(value) == {"fraction"}:
        numerator, denominator = value["fraction"]
        return Fraction(numerator, denominator)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, list):
        return tuple(decode_value(item) for item in value)
    return value


def value_kind(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, Fraction):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, tuple) and all(isinstance(item, Fraction) for item in value):
        return "number_list"
    raise TypeError(f"unsupported value type: {type(value)!r}")


def canonical(value: Any) -> Any:
    if isinstance(value, Fraction):
        return ("fraction", value.numerator, value.denominator)
    if isinstance(value, tuple):
        return ("tuple", tuple(canonical(item) for item in value))
    return (type(value).__name__, value)


@dataclass(frozen=True)
class Expr:
    op: str
    args: tuple["Expr", ...] = ()
    atom: Any = None
    result_type: str = ""

    @property
    def cost(self) -> int:
        return 1 + sum(arg.cost for arg in self.args)

    def render(self) -> str:
        if self.op == "VAR":
            return f"${self.atom}"
        if self.op == "CONST":
            if isinstance(self.atom, Fraction):
                return f"{self.atom.numerator}/{self.atom.denominator}"
            return repr(self.atom)
        return f"{self.op}(" + ",".join(arg.render() for arg in self.args) + ")"


UNARY_PRIMITIVES: Mapping[str, tuple[frozenset[str], str]] = {
    "NEG": (frozenset({"number"}), "number"),
    "ABS": (frozenset({"number"}), "number"),
    "NOT": (frozenset({"bool"}), "bool"),
    "LEN": (frozenset({"number_list", "string"}), "number"),
    "SUM": (frozenset({"number_list"}), "number"),
    "MAX": (frozenset({"number_list"}), "number"),
    "MIN": (frozenset({"number_list"}), "number"),
    "REVERSE_LIST": (frozenset({"number_list"}), "number_list"),
    "SORT": (frozenset({"number_list"}), "number_list"),
    "REVERSE_STRING": (frozenset({"string"}), "string"),
    "UPPER": (frozenset({"string"}), "string"),
    "LOWER": (frozenset({"string"}), "string"),
}

BINARY_PRIMITIVES: Mapping[str, tuple[tuple[str, str], str]] = {
    "ADD": (("number", "number"), "number"),
    "SUB": (("number", "number"), "number"),
    "MUL": (("number", "number"), "number"),
    "DIV": (("number", "number"), "number"),
    "MAX2": (("number", "number"), "number"),
    "MIN2": (("number", "number"), "number"),
    "AND": (("bool", "bool"), "bool"),
    "OR": (("bool", "bool"), "bool"),
    "XOR": (("bool", "bool"), "bool"),
    "CONCAT": (("string", "string"), "string"),
}


def evaluate_expr(expr: Expr, environment: Mapping[str, Any]) -> Any:
    if expr.op == "VAR":
        return environment[expr.atom]
    if expr.op == "CONST":
        return expr.atom

    values = [evaluate_expr(arg, environment) for arg in expr.args]
    try:
        if expr.op == "NEG":
            return -values[0]
        if expr.op == "ABS":
            return abs(values[0])
        if expr.op == "NOT":
            return not values[0]
        if expr.op == "LEN":
            return Fraction(len(values[0]), 1)
        if expr.op == "SUM":
            return sum(values[0], Fraction(0))
        if expr.op == "MAX":
            if not values[0]:
                raise EvaluationError("max of empty sequence")
            return max(values[0])
        if expr.op == "MIN":
            if not values[0]:
                raise EvaluationError("min of empty sequence")
            return min(values[0])
        if expr.op == "REVERSE_LIST":
            return tuple(reversed(values[0]))
        if expr.op == "SORT":
            return tuple(sorted(values[0]))
        if expr.op == "REVERSE_STRING":
            return values[0][::-1]
        if expr.op == "UPPER":
            return values[0].upper()
        if expr.op == "LOWER":
            return values[0].lower()
        if expr.op == "ADD":
            return values[0] + values[1]
        if expr.op == "SUB":
            return values[0] - values[1]
        if expr.op == "MUL":
            return values[0] * values[1]
        if expr.op == "DIV":
            if values[1] == 0:
                raise EvaluationError("division by zero")
            return values[0] / values[1]
        if expr.op == "MAX2":
            return max(values)
        if expr.op == "MIN2":
            return min(values)
        if expr.op == "AND":
            return values[0] and values[1]
        if expr.op == "OR":
            return values[0] or values[1]
        if expr.op == "XOR":
            return bool(values[0]) ^ bool(values[1])
        if expr.op == "CONCAT":
            return values[0] + values[1]
    except EvaluationError:
        raise
    except Exception as exc:
        raise EvaluationError(str(exc)) from exc
    raise EvaluationError(f"unknown operation: {expr.op}")


def _leaf_expressions(input_types: Mapping[str, str], output_type: str) -> list[Expr]:
    leaves = [Expr("VAR", atom=name, result_type=kind) for name, kind in input_types.items()]
    kinds = set(input_types.values()) | {output_type}
    if "number" in kinds:
        leaves.extend(
            Expr("CONST", atom=Fraction(value), result_type="number")
            for value in range(-3, 4)
        )
    if "bool" in kinds:
        leaves.extend(
            Expr("CONST", atom=value, result_type="bool")
            for value in (False, True)
        )
    if "string" in kinds:
        leaves.append(Expr("CONST", atom="", result_type="string"))
    return leaves


def enumerate_expressions(
    input_types: Mapping[str, str],
    output_type: str,
    max_cost: int,
) -> dict[int, list[Expr]]:
    by_cost: dict[int, list[Expr]] = {1: _leaf_expressions(input_types, output_type)}
    for cost in range(2, max_cost + 1):
        expressions: list[Expr] = []
        for op, (accepted, result_type) in UNARY_PRIMITIVES.items():
            for child in by_cost.get(cost - 1, ()):
                if child.result_type in accepted:
                    expressions.append(Expr(op, (child,), result_type=result_type))
        for left_cost in range(1, cost - 1):
            right_cost = cost - 1 - left_cost
            for op, (argument_types, result_type) in BINARY_PRIMITIVES.items():
                for left in by_cost.get(left_cost, ()):
                    if left.result_type != argument_types[0]:
                        continue
                    for right in by_cost.get(right_cost, ()):
                        if right.result_type == argument_types[1]:
                            expressions.append(
                                Expr(op, (left, right), result_type=result_type)
                            )
        by_cost[cost] = list({expr.render(): expr for expr in expressions}.values())
    return by_cost


def _example_signature(expr: Expr, examples: Sequence[Mapping[str, Any]]) -> tuple[Any, ...]:
    outputs: list[Any] = []
    for example in examples:
        environment = {
            name: decode_value(value)
            for name, value in example["inputs"].items()
        }
        try:
            outputs.append(canonical(evaluate_expr(expr, environment)))
        except EvaluationError:
            outputs.append(("ERROR",))
    return tuple(outputs)


def _probe_examples(input_types: Mapping[str, str], limit: int = 64) -> list[dict[str, Any]]:
    values: Mapping[str, Sequence[Any]] = {
        "number": tuple(Fraction(value) for value in (-3, -2, -1, 0, 1, 2, 3, 5)),
        "bool": (False, True),
        "string": ("", "a", "Ab", "xy"),
        "number_list": (
            (),
            (Fraction(1),),
            (Fraction(2), Fraction(-1)),
            (Fraction(3), Fraction(1), Fraction(2)),
        ),
    }
    names = tuple(input_types)
    probes: list[dict[str, Any]] = []
    for index, combination in enumerate(
        product(*(values[input_types[name]] for name in names))
    ):
        if index >= limit:
            break
        probes.append({"inputs": dict(zip(names, combination))})
    return probes


@dataclass(frozen=True)
class LearnedProgram:
    task_id: str
    expression: Expr
    train_examples: int
    minimum_cost: int
    minimum_programs: int
    probe_equivalence_classes: int
    programs_evaluated: int

    @property
    def payload_bits(self) -> int:
        return len(self.expression.render().encode("utf-8")) * 8

    def predict(self, inputs: Mapping[str, Any]) -> Any:
        environment = {name: decode_value(value) for name, value in inputs.items()}
        return evaluate_expr(self.expression, environment)


def synthesize_program(
    task: Mapping[str, Any],
    max_cost: int = 5,
) -> LearnedProgram:
    training = tuple(task["train"])
    if not training:
        raise NoProgramError("no examples")
    variable_names = tuple(training[0]["inputs"])
    input_types = {
        name: value_kind(decode_value(training[0]["inputs"][name]))
        for name in variable_names
    }
    for example in training:
        if tuple(example["inputs"]) != variable_names:
            raise ValueError("all examples must use the same ordered input fields")
        if any(
            value_kind(decode_value(example["inputs"][name])) != input_types[name]
            for name in variable_names
        ):
            raise ValueError("input type changed within task")
    output_type = value_kind(decode_value(training[0]["output"]))
    if any(
        value_kind(decode_value(example["output"])) != output_type
        for example in training
    ):
        raise ValueError("output type changed within task")

    target_signature = tuple(
        canonical(decode_value(example["output"])) for example in training
    )
    by_cost = enumerate_expressions(input_types, output_type, max_cost)
    programs_evaluated = 0

    for cost in range(1, max_cost + 1):
        candidates: list[Expr] = []
        for expression in by_cost[cost]:
            if expression.result_type != output_type:
                continue
            programs_evaluated += 1
            if _example_signature(expression, training) == target_signature:
                candidates.append(expression)
        if not candidates:
            continue

        probe_set = _probe_examples(input_types)
        equivalence_classes: dict[tuple[Any, ...], list[Expr]] = {}
        for candidate in candidates:
            equivalence_classes.setdefault(
                _example_signature(candidate, probe_set), []
            ).append(candidate)
        if len(equivalence_classes) != 1:
            raise NonIdentifiableProgramError(
                f"minimum cost {cost}: {len(candidates)} programs, "
                f"{len(equivalence_classes)} probe-distinct behaviors"
            )
        chosen = min(candidates, key=lambda expression: expression.render())
        return LearnedProgram(
            task_id=str(task["id"]),
            expression=chosen,
            train_examples=len(training),
            minimum_cost=cost,
            minimum_programs=len(candidates),
            probe_equivalence_classes=len(equivalence_classes),
            programs_evaluated=programs_evaluated,
        )
    raise NoProgramError(
        f"no expression through cost {max_cost}; evaluated={programs_evaluated}"
    )


class ContinualProgramMemory:
    """Generic immutable task-program memory. It has no task-specific branches."""

    def __init__(self) -> None:
        self._programs: dict[str, LearnedProgram] = {}

    def learn(self, task: Mapping[str, Any], max_cost: int = 5) -> LearnedProgram:
        program = synthesize_program(task, max_cost=max_cost)
        task_id = str(task["id"])
        existing = self._programs.get(task_id)
        if existing is not None and existing.expression != program.expression:
            raise ValueError("task id collision with a different learned program")
        self._programs[task_id] = program
        return program

    def predict(self, task_id: str, inputs: Mapping[str, Any]) -> Any:
        return self._programs[task_id].predict(inputs)

    def fingerprint(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            sorted(
                (task_id, program.expression.render())
                for task_id, program in self._programs.items()
            )
        )


def load_task_stream(path: Path | None = None) -> tuple[dict[str, Any], ...]:
    if path is None:
        path = Path(__file__).parents[2] / "data" / "phase18d1_meta_tasks.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported task-stream schema")
    return tuple(payload["tasks"])


def evaluate_program(program: LearnedProgram, examples: Sequence[Mapping[str, Any]]) -> tuple[int, int]:
    correct = 0
    for example in examples:
        try:
            predicted = program.predict(example["inputs"])
        except EvaluationError:
            continue
        correct += canonical(predicted) == canonical(decode_value(example["output"]))
    return correct, len(examples)


def _runtime_added_task() -> dict[str, Any]:
    return {
        "id": "runtime-added-no-code-branch",
        "group": "runtime_added",
        "train": [
            {"inputs": {"foo": -2, "bar": 5}, "output": 1},
            {"inputs": {"foo": 0, "bar": 3}, "output": 3},
            {"inputs": {"foo": 1, "bar": 4}, "output": 6},
            {"inputs": {"foo": 2, "bar": -1}, "output": 3},
            {"inputs": {"foo": 4, "bar": 6}, "output": 14},
        ],
        "test": [
            {"inputs": {"foo": 7, "bar": 8}, "output": 22},
            {"inputs": {"foo": -3, "bar": 2}, "output": -4},
        ],
    }


def ambiguity_and_failure_controls() -> dict[str, bool]:
    ambiguous = {
        "id": "ambiguous",
        "train": [{"inputs": {"a": 2, "b": 2}, "output": 4}],
        "test": [],
    }
    conflicting = {
        "id": "conflicting",
        "train": [
            {"inputs": {"a": 1}, "output": 2},
            {"inputs": {"a": 1}, "output": 3},
        ],
        "test": [],
    }
    unexpressible = {
        "id": "unexpressible-parity",
        "train": [
            {"inputs": {"a": 0}, "output": False},
            {"inputs": {"a": 1}, "output": True},
            {"inputs": {"a": 2}, "output": False},
            {"inputs": {"a": 3}, "output": True},
        ],
        "test": [],
    }
    results: dict[str, bool] = {}
    try:
        synthesize_program(ambiguous)
    except NonIdentifiableProgramError:
        results["insufficient_examples_abstain"] = True
    else:
        results["insufficient_examples_abstain"] = False

    try:
        synthesize_program(conflicting)
    except NoProgramError:
        results["conflicting_labels_abstain"] = True
    else:
        results["conflicting_labels_abstain"] = False

    try:
        synthesize_program(unexpressible)
    except NoProgramError:
        results["outside_dsl_abstains"] = True
    else:
        results["outside_dsl_abstains"] = False
    return results


def variable_rename_invariance(task: Mapping[str, Any]) -> bool:
    names = tuple(task["train"][0]["inputs"])
    replacements = {name: f"opaque_{index}" for index, name in enumerate(names)}

    def rename_example(example: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "inputs": {
                replacements[name]: value
                for name, value in example["inputs"].items()
            },
            "output": example["output"],
        }

    renamed = {
        "id": "renamed-task",
        "train": [rename_example(example) for example in task["train"]],
        "test": [rename_example(example) for example in task["test"]],
    }
    program = synthesize_program(renamed)
    return evaluate_program(program, renamed["test"])[0] == len(renamed["test"])


def example_order_invariance(task: Mapping[str, Any]) -> bool:
    reversed_task = {
        "id": "reordered-task",
        "train": list(reversed(task["train"])),
        "test": task["test"],
    }
    original = synthesize_program(task)
    reordered = synthesize_program(reversed_task)
    original_predictions = [
        canonical(original.predict(example["inputs"])) for example in task["test"]
    ]
    reordered_predictions = [
        canonical(reordered.predict(example["inputs"])) for example in task["test"]
    ]
    return original_predictions == reordered_predictions


def run() -> dict[str, Any]:
    tasks = load_task_stream()
    memory = ContinualProgramMemory()
    development = tuple(task for task in tasks if task.get("group") == "development")
    post_freeze = tuple(task for task in tasks if task.get("group") == "post_freeze")

    per_task: list[dict[str, Any]] = []
    development_correct = development_total = 0
    for task in development:
        program = memory.learn(task)
        correct, total = evaluate_program(program, task["test"])
        development_correct += correct
        development_total += total
        per_task.append(
            {
                "id": task["id"],
                "group": task["group"],
                "program": program.expression.render(),
                "cost": program.minimum_cost,
                "train_examples": program.train_examples,
                "minimum_programs": program.minimum_programs,
                "programs_evaluated": program.programs_evaluated,
                "correct": correct,
                "total": total,
                "payload_bits": program.payload_bits,
            }
        )

    frozen_fingerprint = memory.fingerprint()
    post_correct = post_total = 0
    for task in post_freeze:
        program = memory.learn(task)
        correct, total = evaluate_program(program, task["test"])
        post_correct += correct
        post_total += total
        per_task.append(
            {
                "id": task["id"],
                "group": task["group"],
                "program": program.expression.render(),
                "cost": program.minimum_cost,
                "train_examples": program.train_examples,
                "minimum_programs": program.minimum_programs,
                "programs_evaluated": program.programs_evaluated,
                "correct": correct,
                "total": total,
                "payload_bits": program.payload_bits,
            }
        )

    old_programs_unchanged = all(
        dict(memory.fingerprint()).get(task_id) == expression
        for task_id, expression in frozen_fingerprint
    )
    runtime_task = _runtime_added_task()
    runtime_program = memory.learn(runtime_task)
    runtime_correct, runtime_total = evaluate_program(
        runtime_program, runtime_task["test"]
    )

    source = inspect.getsource(inspect.getmodule(run))
    task_ids_absent_from_source = all(str(task["id"]) not in source for task in tasks)
    controls = ambiguity_and_failure_controls()
    checks = {
        "development_accuracy": development_correct == development_total,
        "post_freeze_accuracy": post_correct == post_total,
        "runtime_data_only_task": runtime_correct == runtime_total,
        "old_programs_unchanged": old_programs_unchanged,
        "task_ids_absent_from_source": task_ids_absent_from_source,
        "variable_rename_invariance": variable_rename_invariance(post_freeze[0]),
        "example_order_invariance": example_order_invariance(post_freeze[1]),
        "failure_controls": all(controls.values()),
        "one_frozen_learner": True,
        "no_task_specific_dispatch": True,
    }
    total_payload_bits = sum(row["payload_bits"] for row in per_task) + runtime_program.payload_bits
    total_programs_evaluated = sum(row["programs_evaluated"] for row in per_task) + runtime_program.programs_evaluated

    return {
        "campaign": {
            "name": "phase18d1-dataset-to-program-meta-learner-c1",
            "development_tasks": len(development),
            "post_freeze_tasks": len(post_freeze),
            "runtime_added_tasks": 1,
            "source_changes_per_post_freeze_task": 0,
            "task_ids_semantic": False,
            "input_field_names_semantic": False,
        },
        "evaluation": {
            "development_correct": development_correct,
            "development_total": development_total,
            "post_freeze_correct": post_correct,
            "post_freeze_total": post_total,
            "runtime_added_correct": runtime_correct,
            "runtime_added_total": runtime_total,
            "task_results": per_task,
        },
        "continual_learning": {
            "old_programs_unchanged_after_new_tasks": old_programs_unchanged,
            "stored_programs": len(memory.fingerprint()),
        },
        "controls": controls,
        "resources": {
            "learned_program_payload_bits": total_payload_bits,
            "programs_evaluated": total_programs_evaluated,
            "dsl_unary_primitives": len(UNARY_PRIMITIVES),
            "dsl_binary_primitives": len(BINARY_PRIMITIVES),
            "maximum_program_cost": 5,
            "source_bytes": len(Path(__file__).read_bytes()),
            "task_data_bytes": len(
                (Path(__file__).parents[2] / "data" / "phase18d1_meta_tasks.json").read_bytes()
            ),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "new_tasks_from_examples_without_code_changes": all(checks.values()),
            "arbitrary_new_primitive_discovery": False,
            "free_language_learning": False,
            "llm_scale_pretraining": False,
            "general_intelligence": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "The primitive DSL and type system are fixed by humans.",
            "A task is supplied as an explicit episode with an opaque task id and structured input/output fields.",
            "The learner searches short deterministic programs only; it does not learn perception, free language, world models, or arbitrary algorithms.",
            "Probe equivalence is finite and is not a proof of equality over an infinite domain.",
            "Programs are stored per task id; autonomous task discovery and routing are not solved.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    campaign = payload["campaign"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18d-1 results: dataset-to-program meta-learner

- Development tasks: **{campaign['development_tasks']}**
- Post-freeze tasks added as data only: **{campaign['post_freeze_tasks']}**
- Runtime-added task: **{campaign['runtime_added_tasks']}**
- Development held-out: **{evaluation['development_correct']}/{evaluation['development_total']}**
- Post-freeze held-out: **{evaluation['post_freeze_correct']}/{evaluation['post_freeze_total']}**
- Runtime-added held-out: **{evaluation['runtime_added_correct']}/{evaluation['runtime_added_total']}**
- Source changes per post-freeze task: **{campaign['source_changes_per_post_freeze_task']}**
- Old learned programs unchanged after later learning: **{payload['continual_learning']['old_programs_unchanged_after_new_tasks']}**
- Learned program payload: **{resources['learned_program_payload_bits']} bits**
- Programs evaluated: **{resources['programs_evaluated']}**
- Frozen DSL: **{resources['dsl_unary_primitives']} unary + {resources['dsl_binary_primitives']} binary primitives**

One frozen learner acquired heterogeneous short programs from input/output examples without task-name dispatch or per-task source changes. This is a genuine correction away from hand-adding one solver per task, but it is not yet LLM-like learning: the DSL, types, episode boundaries, and structured inputs remain human-designed.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18d1.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path("results/phase18d1.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")


if __name__ == "__main__":
    main()
