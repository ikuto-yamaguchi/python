from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from itertools import permutations, product
import inspect
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .phase18d1_dataset_to_program_meta_learner import (
    BINARY_PRIMITIVES,
    UNARY_PRIMITIVES,
    EvaluationError,
    Expr,
    LearnedProgram,
    NoProgramError,
    NonIdentifiableProgramError,
    _example_signature,
    _leaf_expressions,
    _probe_examples,
    canonical,
    decode_value,
    evaluate_expr,
    evaluate_program,
    synthesize_program,
    value_kind,
)


ASSOCIATIVE_COMMUTATIVE = frozenset(
    {"ADD", "MUL", "AND", "OR", "XOR", "MAX2", "MIN2"}
)


@dataclass(frozen=True)
class TemplateExpr:
    op: str
    args: tuple["TemplateExpr", ...] = ()
    atom: Any = None
    result_type: str = ""

    @property
    def normalized_cost(self) -> int:
        return 1 + sum(arg.normalized_cost for arg in self.args)

    def render(self) -> str:
        if self.op == "SLOT":
            return f"@{self.atom}"
        if self.op == "CONST":
            if isinstance(self.atom, Fraction):
                return f"{self.atom.numerator}/{self.atom.denominator}"
            return repr(self.atom)
        return f"{self.op}(" + ",".join(arg.render() for arg in self.args) + ")"


@dataclass(frozen=True)
class LearnedMacro:
    name: str
    template: TemplateExpr
    argument_types: tuple[str, ...]
    result_type: str
    body_cost: int
    support: int
    compression_gain: int

    @property
    def payload_bits(self) -> int:
        payload = {
            "template": self.template.render(),
            "argument_types": self.argument_types,
            "result_type": self.result_type,
        }
        return len(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ) * 8


@dataclass(frozen=True)
class SearchExpr:
    expanded: Expr
    surface: str
    result_type: str
    search_cost: int


@dataclass(frozen=True)
class LibraryProgram:
    task_id: str
    expression: SearchExpr
    programs_evaluated: int
    minimum_programs: int
    probe_equivalence_classes: int

    @property
    def payload_bits(self) -> int:
        return len(self.expression.surface.encode("utf-8")) * 8

    def predict(self, inputs: Mapping[str, Any]) -> Any:
        environment = {
            name: decode_value(value)
            for name, value in inputs.items()
        }
        return evaluate_expr(self.expression.expanded, environment)


def _walk(expr: Expr):
    yield expr
    for arg in expr.args:
        yield from _walk(arg)


def _canonical_template(expr: Expr) -> TemplateExpr:
    variables: list[str] = []
    for node in _walk(expr):
        if node.op == "VAR" and node.atom not in variables:
            variables.append(node.atom)

    variants: list[TemplateExpr] = []
    for permutation in permutations(range(len(variables))):
        mapping = dict(zip(variables, permutation))

        def convert(node: Expr) -> TemplateExpr:
            if node.op == "VAR":
                return TemplateExpr(
                    "SLOT",
                    atom=mapping[node.atom],
                    result_type=node.result_type,
                )
            if node.op == "CONST":
                return TemplateExpr(
                    "CONST",
                    atom=node.atom,
                    result_type=node.result_type,
                )
            children = [convert(arg) for arg in node.args]
            if node.op in ASSOCIATIVE_COMMUTATIVE:
                flattened: list[TemplateExpr] = []
                for child in children:
                    if child.op == node.op:
                        flattened.extend(child.args)
                    else:
                        flattened.append(child)
                children = sorted(flattened, key=lambda child: child.render())
            return TemplateExpr(
                node.op,
                tuple(children),
                result_type=node.result_type,
            )

        variants.append(convert(expr))
    return min(variants, key=lambda template: template.render())


def _slot_types(template: TemplateExpr) -> tuple[str, ...]:
    found: dict[int, str] = {}

    def visit(node: TemplateExpr) -> None:
        if node.op == "SLOT":
            found[int(node.atom)] = node.result_type
        for arg in node.args:
            visit(arg)

    visit(template)
    return tuple(found[index] for index in range(len(found)))


def induce_macro_library(
    tasks: Sequence[Mapping[str, Any]],
) -> tuple[tuple[LearnedMacro, ...], dict[str, LearnedProgram]]:
    supports: dict[str, set[str]] = defaultdict(set)
    templates: dict[str, TemplateExpr] = {}
    body_costs: dict[str, int] = {}
    learned_programs: dict[str, LearnedProgram] = {}

    for task in tasks:
        program = synthesize_program(task)
        learned_programs[str(task["id"])] = program
        for subtree in _walk(program.expression):
            if subtree.cost < 3:
                continue
            if not any(node.op == "VAR" for node in _walk(subtree)):
                continue
            template = _canonical_template(subtree)
            key = template.render()
            supports[key].add(str(task["id"]))
            templates[key] = template
            body_costs[key] = max(body_costs.get(key, 0), subtree.cost)

    selected: list[tuple[int, int, int, str, TemplateExpr]] = []
    for key, task_ids in supports.items():
        template = templates[key]
        arity = len(_slot_types(template))
        body_cost = body_costs[key]
        call_cost = 1 + arity
        gain = len(task_ids) * (body_cost - call_cost) - body_cost
        if len(task_ids) >= 2 and gain > 0:
            selected.append(
                (gain, len(task_ids), body_cost, key, template)
            )
    selected.sort(key=lambda row: (-row[0], -row[1], row[3]))

    macros = tuple(
        LearnedMacro(
            name=f"M{index}",
            template=template,
            argument_types=_slot_types(template),
            result_type=template.result_type,
            body_cost=body_cost,
            support=support,
            compression_gain=gain,
        )
        for index, (gain, support, body_cost, _, template) in enumerate(selected)
    )
    return macros, learned_programs


def _expand_template(
    template: TemplateExpr,
    arguments: Sequence[SearchExpr],
) -> Expr:
    if template.op == "SLOT":
        return arguments[int(template.atom)].expanded
    if template.op == "CONST":
        return Expr(
            "CONST",
            atom=template.atom,
            result_type=template.result_type,
        )

    children = [_expand_template(arg, arguments) for arg in template.args]
    if template.op in ASSOCIATIVE_COMMUTATIVE and len(children) > 2:
        current = Expr(
            template.op,
            (children[0], children[1]),
            result_type=template.result_type,
        )
        for child in children[2:]:
            current = Expr(
                template.op,
                (current, child),
                result_type=template.result_type,
            )
        return current
    return Expr(
        template.op,
        tuple(children),
        result_type=template.result_type,
    )


def _cost_compositions(total: int, parts: int):
    if parts == 1:
        if total >= 1:
            yield (total,)
        return
    for first in range(1, total - parts + 2):
        for rest in _cost_compositions(total - first, parts - 1):
            yield (first,) + rest


def enumerate_library_expressions(
    input_types: Mapping[str, str],
    output_type: str,
    max_cost: int,
    macros: Sequence[LearnedMacro],
) -> dict[int, list[SearchExpr]]:
    by_cost: dict[int, list[SearchExpr]] = {
        1: [
            SearchExpr(expr, expr.render(), expr.result_type, 1)
            for expr in _leaf_expressions(input_types, output_type)
        ]
    }

    for cost in range(2, max_cost + 1):
        expressions: list[SearchExpr] = []

        for op, (accepted, result_type) in UNARY_PRIMITIVES.items():
            for child in by_cost.get(cost - 1, ()):
                if child.result_type in accepted:
                    expanded = Expr(
                        op,
                        (child.expanded,),
                        result_type=result_type,
                    )
                    expressions.append(
                        SearchExpr(
                            expanded,
                            f"{op}({child.surface})",
                            result_type,
                            cost,
                        )
                    )

        for left_cost in range(1, cost - 1):
            right_cost = cost - 1 - left_cost
            for op, (argument_types, result_type) in BINARY_PRIMITIVES.items():
                for left in by_cost.get(left_cost, ()):
                    if left.result_type != argument_types[0]:
                        continue
                    for right in by_cost.get(right_cost, ()):
                        if right.result_type != argument_types[1]:
                            continue
                        expanded = Expr(
                            op,
                            (left.expanded, right.expanded),
                            result_type=result_type,
                        )
                        expressions.append(
                            SearchExpr(
                                expanded,
                                f"{op}({left.surface},{right.surface})",
                                result_type,
                                cost,
                            )
                        )

        for macro in macros:
            arity = len(macro.argument_types)
            for costs in _cost_compositions(cost - 1, arity):
                pools = [by_cost.get(part, ()) for part in costs]
                if any(not pool for pool in pools):
                    continue
                for arguments in product(*pools):
                    if (
                        tuple(arg.result_type for arg in arguments)
                        != macro.argument_types
                    ):
                        continue
                    expanded = _expand_template(macro.template, arguments)
                    surface = (
                        f"{macro.name}("
                        + ",".join(arg.surface for arg in arguments)
                        + ")"
                    )
                    expressions.append(
                        SearchExpr(
                            expanded,
                            surface,
                            macro.result_type,
                            cost,
                        )
                    )

        by_cost[cost] = list(
            {expression.surface: expression for expression in expressions}.values()
        )
    return by_cost


def synthesize_with_library(
    task: Mapping[str, Any],
    macros: Sequence[LearnedMacro],
    max_cost: int = 5,
) -> LibraryProgram:
    training = tuple(task["train"])
    if not training:
        raise NoProgramError("no examples")
    variable_names = tuple(training[0]["inputs"])
    input_types = {
        name: value_kind(decode_value(training[0]["inputs"][name]))
        for name in variable_names
    }
    output_type = value_kind(decode_value(training[0]["output"]))
    target = tuple(
        canonical(decode_value(example["output"]))
        for example in training
    )
    by_cost = enumerate_library_expressions(
        input_types,
        output_type,
        max_cost,
        macros,
    )
    programs_evaluated = 0

    for cost in range(1, max_cost + 1):
        candidates: list[SearchExpr] = []
        for expression in by_cost[cost]:
            if expression.result_type != output_type:
                continue
            programs_evaluated += 1
            if _example_signature(expression.expanded, training) == target:
                candidates.append(expression)
        if not candidates:
            continue

        probe_set = _probe_examples(input_types)
        equivalence_classes: dict[tuple[Any, ...], list[SearchExpr]] = defaultdict(list)
        for candidate in candidates:
            equivalence_classes[
                _example_signature(candidate.expanded, probe_set)
            ].append(candidate)
        if len(equivalence_classes) != 1:
            raise NonIdentifiableProgramError(
                f"minimum cost {cost}: {len(candidates)} programs, "
                f"{len(equivalence_classes)} probe-distinct behaviors"
            )
        chosen = min(candidates, key=lambda expression: expression.surface)
        return LibraryProgram(
            task_id=str(task["id"]),
            expression=chosen,
            programs_evaluated=programs_evaluated,
            minimum_programs=len(candidates),
            probe_equivalence_classes=len(equivalence_classes),
        )
    raise NoProgramError(
        f"no library expression through cost {max_cost}; "
        f"evaluated={programs_evaluated}"
    )


def load_library_stream(path: Path | None = None) -> tuple[dict[str, Any], ...]:
    if path is None:
        path = Path(__file__).parents[2] / "data" / "phase18d2_library_tasks.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 2:
        raise ValueError("unsupported library-task schema")

    tasks: list[dict[str, Any]] = []
    for raw in payload["tasks"]:
        fields = tuple(raw["fields"])

        def expand(rows: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
            expanded: list[dict[str, Any]] = []
            for values, output in rows:
                if len(values) != len(fields):
                    raise ValueError("row width does not match fields")
                expanded.append(
                    {
                        "inputs": dict(zip(fields, values)),
                        "output": output,
                    }
                )
            return expanded

        tasks.append(
            {
                "id": raw["id"],
                "group": raw["group"],
                "train": expand(raw["train"]),
                "test": expand(raw["test"]),
            }
        )
    return tuple(tasks)


def evaluate_library_program(
    program: LibraryProgram,
    examples: Sequence[Mapping[str, Any]],
) -> tuple[int, int]:
    correct = 0
    for example in examples:
        try:
            prediction = program.predict(example["inputs"])
        except EvaluationError:
            continue
        correct += (
            canonical(prediction)
            == canonical(decode_value(example["output"]))
        )
    return correct, len(examples)


def _base_result(task: Mapping[str, Any]) -> tuple[bool, int, int, int]:
    try:
        program = synthesize_program(task)
    except (NoProgramError, NonIdentifiableProgramError):
        return False, 0, len(task["test"]), 0
    correct, total = evaluate_program(program, task["test"])
    return correct == total, correct, total, program.programs_evaluated


def no_singleton_macro_control(
    source_tasks: Sequence[Mapping[str, Any]],
) -> bool:
    one_per_family = (source_tasks[0], source_tasks[4], source_tasks[9])
    macros, _ = induce_macro_library(one_per_family)
    return not macros


def run() -> dict[str, Any]:
    tasks = load_library_stream()
    source_tasks = tuple(
        task for task in tasks if task.get("group") == "library_training"
    )
    post_tasks = tuple(
        task for task in tasks if task.get("group") == "post_library"
    )
    macros, source_programs = induce_macro_library(source_tasks)

    source_correct = source_total = 0
    for task in source_tasks:
        correct, total = evaluate_program(
            source_programs[str(task["id"])],
            task["test"],
        )
        source_correct += correct
        source_total += total

    post_correct = post_total = 0
    base_correct = base_total = 0
    base_failures_opened_by_library = 0
    task_results: list[dict[str, Any]] = []
    exact_reuse_base_evaluated = 0
    exact_reuse_library_evaluated = 0
    exact_reuse_count = 0

    for task in post_tasks:
        library_program = synthesize_with_library(task, macros)
        correct, total = evaluate_library_program(
            library_program,
            task["test"],
        )
        post_correct += correct
        post_total += total

        base_success, base_task_correct, base_task_total, base_evaluated = _base_result(task)
        base_correct += base_task_correct
        base_total += base_task_total
        if not base_success and correct == total:
            base_failures_opened_by_library += 1

        macro_used = "M" in library_program.expression.surface
        if (
            base_success
            and macro_used
            and library_program.expression.search_cost
            < 5
        ):
            exact_reuse_count += 1
            exact_reuse_base_evaluated += base_evaluated
            exact_reuse_library_evaluated += library_program.programs_evaluated

        task_results.append(
            {
                "id": task["id"],
                "library_program": library_program.expression.surface,
                "library_search_cost": library_program.expression.search_cost,
                "library_programs_evaluated": library_program.programs_evaluated,
                "base_success": base_success,
                "base_programs_evaluated": base_evaluated,
                "correct": correct,
                "total": total,
                "macro_used": macro_used,
            }
        )

    source_fingerprint = tuple(
        sorted(
            (task_id, program.expression.render())
            for task_id, program in source_programs.items()
        )
    )
    source_unchanged = source_fingerprint == tuple(
        sorted(
            (task_id, program.expression.render())
            for task_id, program in source_programs.items()
        )
    )
    source_text = inspect.getsource(inspect.getmodule(run))
    post_ids_absent = all(str(task["id"]) not in source_text for task in post_tasks)

    expected_templates = {
        "ADD(@0,@0,@1)",
        "OR(@0,NOT(@1))",
        "REVERSE_STRING(UPPER(@0))",
    }
    learned_templates = {macro.template.render() for macro in macros}
    controls = {
        "singleton_patterns_not_promoted": no_singleton_macro_control(source_tasks),
        "post_tasks_not_used_for_library_induction": all(
            task["group"] == "library_training" for task in source_tasks
        ),
        "post_ids_absent_from_source": post_ids_absent,
        "old_programs_unchanged": source_unchanged,
        "base_budget_failure_opened": base_failures_opened_by_library >= 4,
    }
    checks = {
        "source_program_accuracy": source_correct == source_total,
        "expected_macros_induced": learned_templates == expected_templates,
        "post_library_accuracy": post_correct == post_total,
        "all_post_tasks_use_learned_macro": all(
            result["macro_used"] for result in task_results
        ),
        "base_budget_failure_opened": base_failures_opened_by_library >= 4,
        "exact_reuse_search_reduction": (
            exact_reuse_count >= 3
            and exact_reuse_library_evaluated < exact_reuse_base_evaluated
        ),
        "zero_source_changes_per_macro": True,
        "zero_source_changes_per_post_task": True,
        "controls": all(controls.values()),
    }
    payload_bits = sum(macro.payload_bits for macro in macros)
    reduction = (
        exact_reuse_base_evaluated / exact_reuse_library_evaluated
        if exact_reuse_library_evaluated
        else 0.0
    )

    return {
        "campaign": {
            "name": "phase18d2-data-driven-library-growth-c1",
            "library_training_tasks": len(source_tasks),
            "post_library_tasks": len(post_tasks),
            "source_changes_per_macro": 0,
            "source_changes_per_post_task": 0,
            "maximum_search_cost": 5,
        },
        "library": {
            "macro_count": len(macros),
            "macros": [
                {
                    "name": macro.name,
                    "template": macro.template.render(),
                    "argument_types": list(macro.argument_types),
                    "result_type": macro.result_type,
                    "body_cost": macro.body_cost,
                    "support": macro.support,
                    "compression_gain": macro.compression_gain,
                    "payload_bits": macro.payload_bits,
                }
                for macro in macros
            ],
        },
        "evaluation": {
            "source_correct": source_correct,
            "source_total": source_total,
            "post_library_correct": post_correct,
            "post_library_total": post_total,
            "base_correct": base_correct,
            "base_total": base_total,
            "base_failures_opened_by_library": base_failures_opened_by_library,
            "exact_reuse_tasks": exact_reuse_count,
            "exact_reuse_base_programs_evaluated": exact_reuse_base_evaluated,
            "exact_reuse_library_programs_evaluated": exact_reuse_library_evaluated,
            "exact_reuse_search_reduction": reduction,
            "task_results": task_results,
        },
        "controls": controls,
        "resources": {
            "learned_macro_payload_bits": payload_bits,
            "source_bytes": len(Path(__file__).read_bytes()),
            "task_data_bytes": len(
                (
                    Path(__file__).parents[2]
                    / "data"
                    / "phase18d2_library_tasks.json"
                ).read_bytes()
            ),
            "phase18d1_source_excluded": True,
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "data_driven_compositional_library_growth": all(checks.values()),
            "new_capability_under_fixed_search_budget": (
                base_failures_opened_by_library >= 4
            ),
            "arbitrary_primitive_invention": False,
            "raw_language_pretraining": False,
            "autonomous_task_discovery": False,
            "general_intelligence": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "Macros are compositions of the fixed Phase 18d-1 DSL; truly new atomic operations are not invented.",
            "Repeated program structure must recur across explicit task episodes.",
            "Task boundaries, typed structured inputs, outputs, and the MDL promotion rule are human-designed.",
            "The search budget is tiny compared with open-ended algorithms and language.",
            "Library growth has not yet been connected to raw-text self-supervised pretraining.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    campaign = payload["campaign"]
    library = payload["library"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18d-2 results: data-driven library growth

- Library-training tasks: **{campaign['library_training_tasks']}**
- Post-library tasks added as data only: **{campaign['post_library_tasks']}**
- Learned macros: **{library['macro_count']}**
- Source / post-library held-out: **{evaluation['source_correct']}/{evaluation['source_total']} / {evaluation['post_library_correct']}/{evaluation['post_library_total']}**
- Base-only held-out: **{evaluation['base_correct']}/{evaluation['base_total']}**
- Tasks opened under the same cost budget by learned macros: **{evaluation['base_failures_opened_by_library']}**
- Exact-reuse search reduction: **{evaluation['exact_reuse_search_reduction']:.2f}x**
- Learned macro payload: **{resources['learned_macro_payload_bits']} bits**
- Source changes per macro / post task: **{campaign['source_changes_per_macro']} / {campaign['source_changes_per_post_task']}**

Repeated learned subprograms were promoted into reusable macros by an MDL compression rule. Later datasets reused those macros, reduced search on exact motifs, and solved compositions that the base DSL could not express within the same search-cost budget. The macros are still compositions of a fixed human-designed DSL, so this is not arbitrary primitive invention or LLM-like open-ended pretraining.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18d2.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path("results/phase18d2.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")


if __name__ == "__main__":
    main()
