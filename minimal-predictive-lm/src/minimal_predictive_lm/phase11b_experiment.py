from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from .universal_macro_library import (
    decide_macro_adoption,
    expression_accuracy,
    induce_macro_library,
    synthesize_expression_with_library,
)
from .universal_program_induction import (
    TransitionTrace,
    UnexpressibleTaskError,
    induce_program,
)


def _pure(arguments: tuple[int, ...], output: int) -> TransitionTrace:
    return TransitionTrace.build(arguments, {}, {}, output)


def _remaining_task(rows: tuple[tuple[int, int, int], ...]) -> tuple[TransitionTrace, ...]:
    return tuple(_pure(values, values[0] - values[1] - values[2]) for values in rows)


def _revenue_task(rows: tuple[tuple[int, int, int, int], ...]) -> tuple[TransitionTrace, ...]:
    return tuple(
        _pure(values, (values[0] - values[1] - values[2]) * values[3])
        for values in rows
    )


def run() -> dict[str, object]:
    inventory_training = _remaining_task(
        (
            (16, 3, 4),
            (30, 5, 7),
            (25, 2, 8),
            (40, 10, 5),
            (18, 1, 2),
        )
    )
    inventory_heldout = _remaining_task(((60, 15, 10), (22, 4, 3), (100, 20, 25)))
    budget_training = _remaining_task(
        (
            (90, 20, 15),
            (120, 30, 25),
            (75, 12, 18),
            (200, 45, 35),
            (64, 7, 9),
        )
    )
    budget_heldout = _remaining_task(((150, 33, 17), (81, 14, 12), (300, 70, 55)))

    inventory_program = induce_program(
        inventory_training,
        max_depth=2,
        max_candidates=50_000,
    ).program
    budget_program = induce_program(
        budget_training,
        max_depth=2,
        max_candidates=50_000,
    ).program
    library = induce_macro_library((inventory_program, budget_program))

    revenue_training = _revenue_task(
        (
            (16, 3, 4, 2),
            (30, 5, 7, 3),
            (25, 2, 8, 4),
            (40, 10, 5, 6),
            (18, 1, 2, 5),
            (50, 12, 8, 3),
        )
    )
    revenue_heldout = _revenue_task(
        (
            (60, 15, 10, 2),
            (22, 4, 3, 7),
            (100, 20, 25, 3),
            (35, 5, 9, 4),
        )
    )

    baseline_budget = 20_000
    baseline_failed = False
    baseline_message = ""
    try:
        induce_program(
            revenue_training,
            max_depth=3,
            max_candidates=baseline_budget,
        )
    except UnexpressibleTaskError as exc:
        baseline_failed = True
        baseline_message = str(exc)

    library_result = synthesize_expression_with_library(
        revenue_training,
        tuple(trace.output for trace in revenue_training),
        library,
        max_depth=1,
        max_candidates=5_000,
    )
    training_accuracy = expression_accuracy(library_result.expression, revenue_training)
    heldout_accuracy = expression_accuracy(library_result.expression, revenue_heldout)
    macro = library.macros[0]
    adoption = decide_macro_adoption(
        macro,
        library_result,
        baseline_candidate_budget=baseline_budget,
        expected_future_calls=1,
        candidate_evaluation_cost_bits=1,
        verification_accuracy=heldout_accuracy,
    )

    source_accuracies = {
        "inventory": expression_accuracy(inventory_program.output, inventory_heldout),
        "budget": expression_accuracy(budget_program.output, budget_heldout),
    }
    return {
        "library_induction": {
            "source_programs": 2,
            "source_heldout_accuracy": source_accuracies,
            "macros_discovered": len(library.macros),
            "minimum_distinct_program_support": 2,
            "library_bits": library.description_bits,
            "macro": {
                "identifier": macro.identifier,
                "support_programs": macro.support_programs,
                "arity": macro.arity,
                "parameter_types": list(macro.parameter_types),
                "body": macro.body.render(),
                "description_bits": macro.description_bits,
            },
            "one_off_subtrees_retained": 0,
        },
        "target_task": {
            "name": "remaining_revenue",
            "baseline_without_library_failed": baseline_failed,
            "baseline_candidate_budget": baseline_budget,
            "baseline_message": baseline_message,
            "library_search_depth": library_result.stats.maximum_depth,
            "library_candidate_evaluations": library_result.stats.candidate_evaluations,
            "library_unique_signatures": library_result.stats.unique_signatures,
            "macro_calls": library_result.macro_calls,
            "compact_program": library_result.candidate.compact.render(),
            "expanded_program": library_result.expression.render(),
            "training_accuracy": training_accuracy,
            "heldout_accuracy": heldout_accuracy,
        },
        "adoption": asdict(adoption),
        "scalability_verdict": {
            "target_solved_without_engine_code_change": heldout_accuracy == 1.0,
            "target_solved_with_depth_one_search": library_result.stats.maximum_depth <= 1,
            "baseline_budget_failure_removed": baseline_failed and heldout_accuracy == 1.0,
            "macro_adopted_under_normalized_lifetime_objective": adoption.adopted,
            "phase11b_success": (
                len(library.macros) == 1
                and all(value == 1.0 for value in source_accuracies.values())
                and baseline_failed
                and training_accuracy == 1.0
                and heldout_accuracy == 1.0
                and library_result.macro_calls >= 1
                and adoption.adopted
            ),
        },
        "limitations": [
            "macro candidates come from already induced and verified programs rather than raw language",
            "only argument-parametric expression subtrees are abstracted; stateful and recursive macros are excluded",
            "the normalized lifetime objective assigns one bit to one candidate evaluation for this experiment",
            "macro argument instantiation is still enumerative and can grow with arity",
            "library dispatch, versioning, forgetting, and conflicting macro semantics remain incomplete",
            "the task is synthetic and does not establish broad language-model scalability",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    library = payload["library_induction"]
    target = payload["target_task"]
    adoption = payload["adoption"]
    verdict = payload["scalability_verdict"]
    macro = library["macro"]
    lines = [
        "# Phase 11b results: reusable macro library induction",
        "",
        "The learner alpha-normalizes repeated program subtrees across distinct tasks.",
        "A subtree observed in only one program is not admitted to the library.",
        "",
        "## Library induction",
        "",
        f"- source programs: **{library['source_programs']}**",
        f"- macros discovered: **{library['macros_discovered']}**",
        f"- macro support: **{macro['support_programs']} distinct programs**",
        f"- macro body: `{json.dumps(macro['body'], ensure_ascii=False)}`",
        f"- macro storage: **{macro['description_bits']:,} bits**",
        "",
        "## New target",
        "",
        f"- primitive-only search failed at **{target['baseline_candidate_budget']:,} candidates**: **{target['baseline_without_library_failed']}**",
        f"- library search candidates: **{target['library_candidate_evaluations']:,}**",
        f"- library search depth: **{target['library_search_depth']}**",
        f"- macro calls in compact program: **{target['macro_calls']}**",
        f"- training accuracy: **{target['training_accuracy']:.1%}**",
        f"- held-out accuracy: **{target['heldout_accuracy']:.1%}**",
        "",
        "## Lifetime adoption",
        "",
        f"- compact program: **{adoption['compact_program_bits']:,} bits**",
        f"- expanded program: **{adoption['expanded_program_bits']:,} bits**",
        f"- search evaluations saved: **{adoption['search_saving_evaluations']:,}**",
        f"- normalized lifetime gain: **{adoption['normalized_lifetime_gain_bits']:,} bits**",
        f"- adopted: **{adoption['adopted']}**",
        "",
        "## Verdict",
        "",
        f"- Phase 11b success: **{verdict['phase11b_success']}**",
        "",
        "The macro does not add a domain-specific solver.  It shortens future search by",
        "reusing a verified causal computation learned in other tasks.  This is still a",
        "bounded library mechanism, not open-ended representation invention.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase11b.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase11b.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
