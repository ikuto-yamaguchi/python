from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from .universal_program_induction import (
    TransitionTrace,
    UnexpressibleTaskError,
    hypothesis_information_lower_bound,
    induce_program,
    program_accuracy,
    surface_memorization_bits,
)


@dataclass(frozen=True)
class TaskSpec:
    name: str
    group: str
    training: tuple[TransitionTrace, ...]
    heldout: tuple[TransitionTrace, ...]


def _pure(arguments: tuple[object, ...], output: object) -> TransitionTrace:
    return TransitionTrace.build(arguments, {}, {}, output)  # type: ignore[arg-type]


def _binary_task(name: str, operation: str, pairs: tuple[tuple[int, int], ...]) -> TaskSpec:
    def result(left: int, right: int) -> int:
        if operation == "add":
            return left + right
        if operation == "sub":
            return left - right
        if operation == "mul":
            return left * right
        raise ValueError(operation)

    training_pairs = pairs[:5]
    heldout_pairs = pairs[5:]
    return TaskSpec(
        name,
        "base",
        tuple(_pure((left, right), result(left, right)) for left, right in training_pairs),
        tuple(_pure((left, right), result(left, right)) for left, right in heldout_pairs),
    )


def _tasks() -> tuple[TaskSpec, ...]:
    addition = _binary_task(
        "addition",
        "add",
        ((2, 7), (5, 11), (13, 4), (21, 9), (34, 18), (55, 23), (89, 7), (144, 32)),
    )
    subtraction = _binary_task(
        "subtraction",
        "sub",
        ((12, 5), (31, 9), (44, 17), (70, 26), (95, 38), (120, 41), (81, 19), (200, 73)),
    )
    multiplication = _binary_task(
        "multiplication",
        "mul",
        ((3, 8), (6, 7), (9, 5), (11, 4), (13, 6), (14, 9), (17, 3), (21, 8)),
    )

    concat_train = (
        ("red", "fox"),
        ("blue", "bird"),
        ("small", "robot"),
        ("fast", "train"),
        ("quiet", "room"),
    )
    concat_heldout = (("green", "field"), ("bright", "star"), ("new", "task"))
    concatenate = TaskSpec(
        "concatenate",
        "base",
        tuple(_pure(pair, pair[0] + pair[1]) for pair in concat_train),
        tuple(_pure(pair, pair[0] + pair[1]) for pair in concat_heldout),
    )

    location_train = (
        ("box", "warehouse", "laboratory"),
        ("sample", "desk", "inspection"),
        ("tool", "shelf-a", "shelf-b"),
        ("sensor", "line-1", "line-2"),
    )
    location_heldout = (
        ("motor", "storage", "repair"),
        ("document", "inbox", "archive"),
        ("part", "rack-1", "rack-9"),
    )
    set_location = TaskSpec(
        "set_location",
        "base",
        tuple(
            TransitionTrace.build(
                (subject, destination),
                {f"location:{subject}": origin},
                {f"location:{subject}": destination},
                destination,
            )
            for subject, origin, destination in location_train
        ),
        tuple(
            TransitionTrace.build(
                (subject, destination),
                {f"location:{subject}": origin},
                {f"location:{subject}": destination},
                destination,
            )
            for subject, origin, destination in location_heldout
        ),
    )

    decision_training = tuple(
        _pure((status,), "ROLLBACK" if status == "FAIL" else "REPORT")
        for status in ("FAIL", "PASS", "FAIL", "PASS", "FAIL", "PASS")
    )
    decision_heldout = tuple(
        _pure((status,), "ROLLBACK" if status == "FAIL" else "REPORT")
        for status in ("PASS", "FAIL", "PASS", "FAIL")
    )
    conditional = TaskSpec(
        "conditional_decision",
        "base",
        decision_training,
        decision_heldout,
    )

    increment_train = ((2, 5), (7, 3), (11, 8), (20, 4), (31, 9))
    increment_heldout = ((4, 12), (18, 7), (50, 13), (100, 25))
    increment = TaskSpec(
        "increment_state",
        "novel",
        tuple(
            TransitionTrace.build(
                (delta,),
                {"count": current},
                {"count": current + delta},
                current + delta,
            )
            for current, delta in increment_train
        ),
        tuple(
            TransitionTrace.build(
                (delta,),
                {"count": current},
                {"count": current + delta},
                current + delta,
            )
            for current, delta in increment_heldout
        ),
    )

    revenue_train = (
        (16, 3, 4, 2),
        (30, 5, 7, 3),
        (25, 2, 8, 4),
        (40, 10, 5, 6),
        (18, 1, 2, 5),
        (50, 12, 8, 3),
    )
    revenue_heldout = (
        (60, 15, 10, 2),
        (22, 4, 3, 7),
        (100, 20, 25, 3),
        (35, 5, 9, 4),
    )
    revenue = TaskSpec(
        "remaining_revenue",
        "novel",
        tuple(_pure(values, (values[0] - values[1] - values[2]) * values[3]) for values in revenue_train),
        tuple(_pure(values, (values[0] - values[1] - values[2]) * values[3]) for values in revenue_heldout),
    )

    return (
        addition,
        subtraction,
        multiplication,
        concatenate,
        set_location,
        conditional,
        increment,
        revenue,
    )


def _unexpressible_task() -> tuple[TransitionTrace, ...]:
    return tuple(
        _pure((raw,), raw.upper())
        for raw in ("red", "blue", "green", "quiet", "robot", "field")
    )


def run() -> dict[str, object]:
    task_rows: list[dict[str, object]] = []
    total_program_bits = 0
    total_surface_bits = 0
    total_candidates = 0
    primitive_inventory: set[str] = set()

    for task in _tasks():
        result = induce_program(task.training, max_depth=3, max_candidates=250_000)
        training_accuracy = program_accuracy(result.program, task.training)
        heldout_accuracy = program_accuracy(result.program, task.heldout)
        program_bits = result.program.description_bits
        memorization_bits = surface_memorization_bits(task.training)
        total_program_bits += program_bits
        total_surface_bits += memorization_bits
        total_candidates += result.program.candidate_evaluations
        primitive_inventory.update(result.program.operations())
        task_rows.append(
            {
                "name": task.name,
                "group": task.group,
                "training_examples": len(task.training),
                "heldout_examples": len(task.heldout),
                "training_accuracy": training_accuracy,
                "heldout_accuracy": heldout_accuracy,
                "program_bits": program_bits,
                "surface_memorization_bits": memorization_bits,
                "compression_ratio": memorization_bits / program_bits,
                "candidate_evaluations": result.program.candidate_evaluations,
                "hypothesis_id_lower_bound_bits": hypothesis_information_lower_bound(
                    result.program.candidate_evaluations
                ),
                "operations": sorted(result.program.operations()),
                "program": {
                    "output": result.program.output.render(),
                    "updates": [
                        [key.render(), value.render()] for key, value in result.program.updates
                    ],
                },
            }
        )

    unexpressible_detected = False
    unexpressible_message = ""
    try:
        induce_program(_unexpressible_task(), max_depth=3, max_candidates=100_000)
    except UnexpressibleTaskError as exc:
        unexpressible_detected = True
        unexpressible_message = str(exc)

    engine_path = Path(__file__).with_name("universal_program_induction.py")
    engine_source_bytes = engine_path.stat().st_size
    novel_rows = [row for row in task_rows if row["group"] == "novel"]
    all_expressible_heldout = all(row["heldout_accuracy"] == 1.0 for row in task_rows)

    return {
        "architecture": {
            "learner": "one bounded typed MDL program synthesizer",
            "domain_specific_handlers": 0,
            "fixed_primitive_inventory": sorted(primitive_inventory),
            "primitive_count": len(primitive_inventory),
            "engine_source_bytes": engine_source_bytes,
            "human_engine_code_changes_for_novel_tasks": 0,
            "novel_tasks_added_by_traces_only": len(novel_rows),
        },
        "tasks": task_rows,
        "aggregate": {
            "expressible_tasks": len(task_rows),
            "all_training_accuracy": all(row["training_accuracy"] == 1.0 for row in task_rows),
            "all_heldout_accuracy": all_expressible_heldout,
            "total_program_bits": total_program_bits,
            "total_surface_memorization_bits": total_surface_bits,
            "aggregate_compression_ratio": total_surface_bits / total_program_bits,
            "total_candidate_evaluations": total_candidates,
            "average_program_bytes": total_program_bits / len(task_rows) / 8,
            "amortized_engine_plus_program_bytes_per_task": (
                engine_source_bytes + total_program_bits / 8
            ) / len(task_rows),
        },
        "representation_boundary": {
            "task": "uppercase text transformation",
            "unexpressible_detected": unexpressible_detected,
            "message": unexpressible_message,
            "automatic_primitive_invention_available": False,
        },
        "scalability_verdict": {
            "per_domain_manual_algorithm_required_for_expressible_tasks": False,
            "new_domain_data_or_grounding_still_required": True,
            "search_cost_eliminated": False,
            "fixed_grammar_is_open_ended": False,
            "phase11a_success": all_expressible_heldout and unexpressible_detected,
        },
        "limitations": [
            "the learner receives already structured arguments and before/after states",
            "task boundaries are supplied rather than discovered",
            "the grammar is bounded and cannot yet invent a missing primitive such as uppercase",
            "candidate search can still grow exponentially with program depth before pruning",
            "the experiment is synthetic and does not establish broad language-model scalability",
            "human effort moved from task algorithms toward data, grounding, and primitive design; it did not become zero",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    architecture = payload["architecture"]
    aggregate = payload["aggregate"]
    boundary = payload["representation_boundary"]
    lines = [
        "# Phase 11a results: domain-neutral typed program induction",
        "",
        "The same learner is used without domain labels or handwritten task handlers.",
        "New tasks are supplied only as transition traces.",
        "",
        "## Architecture",
        "",
        f"- domain-specific handlers: **{architecture['domain_specific_handlers']}**",
        f"- fixed primitives used: **{architecture['primitive_count']}**",
        f"- novel tasks added with engine code changes: **{architecture['human_engine_code_changes_for_novel_tasks']}**",
        f"- learner source size: **{architecture['engine_source_bytes']:,} bytes**",
        "",
        "## Task results",
        "",
        "| task | group | train | held-out | program bits | trace/program | candidates |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["tasks"]:
        lines.append(
            f"| {row['name']} | {row['group']} | {row['training_accuracy']:.1%} | "
            f"{row['heldout_accuracy']:.1%} | {row['program_bits']:,} | "
            f"{row['compression_ratio']:.2f}x | {row['candidate_evaluations']:,} |"
        )
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- expressible tasks: **{aggregate['expressible_tasks']}**",
            f"- all held-out tasks solved: **{aggregate['all_heldout_accuracy']}**",
            f"- total learned programs: **{aggregate['total_program_bits']:,} bits**",
            f"- training-trace memorization: **{aggregate['total_surface_memorization_bits']:,} bits**",
            f"- aggregate compression: **{aggregate['aggregate_compression_ratio']:.2f}x**",
            f"- total candidate evaluations: **{aggregate['total_candidate_evaluations']:,}**",
            "",
            "## Representation boundary",
            "",
            f"- unexpressible task detected: **{boundary['unexpressible_detected']}**",
            f"- automatic primitive invention: **{boundary['automatic_primitive_invention_available']}**",
            "",
            "The result removes per-domain handwritten algorithms only for tasks expressible",
            "in the current grammar. It does not remove grounding cost, induction search, or",
            "the need to invent new representations when the grammar is insufficient.",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase11a.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase11a.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
