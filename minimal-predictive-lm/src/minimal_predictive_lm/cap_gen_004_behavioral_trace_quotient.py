from __future__ import annotations

import json

from .cap_gen_004_btq_core import (
    build_trace_index,
    evaluate_search,
    guided_programs,
    induce_cross_domain_library,
    solve_task,
    source_ngram_overlap,
    total_search_executions,
)
from .cap_gen_004_btq_grid_domain import (
    grid_probe_inputs,
    grid_programs,
    heldout_grid_tasks,
)
from .cap_gen_004_btq_sequence_domains import (
    list_programs,
    string_programs,
    training_tasks,
)


def run_experiment() -> dict[str, object]:
    programs_by_domain = {
        "string": string_programs(),
        "list": list_programs(),
    }
    solved = tuple(
        solve_task(programs_by_domain[task.domain], task)
        for task in training_tasks()
    )
    library = induce_cross_domain_library(solved)
    syntax_overlap = source_ngram_overlap(solved, n=2)

    target_programs = grid_programs()
    trace_index, index_executions = build_trace_index(
        target_programs,
        grid_probe_inputs(),
    )
    restricted = guided_programs(trace_index, library)

    cold_results = tuple(
        evaluate_search(target_programs, task)
        for task in heldout_grid_tasks()
    )
    guided_results = tuple(
        evaluate_search(restricted, task)
        for task in heldout_grid_tasks()
    )

    training_candidate_executions = sum(
        len(programs_by_domain[task.domain])
        * len(task.train_examples)
        for task in training_tasks()
    )
    solved_trace_executions = sum(
        len(task.train_examples)
        for task in training_tasks()
    )
    cold_target_executions = total_search_executions(cold_results)
    guided_target_verification = total_search_executions(guided_results)
    incremental_guided_total = index_executions + guided_target_verification
    full_curriculum_total = (
        training_candidate_executions
        + solved_trace_executions
        + incremental_guided_total
    )

    all_guided_exact = all(
        result.train_exact and result.test_accuracy == 1.0
        for result in guided_results
    )
    same_solutions = all(
        cold.chosen_program == guided.chosen_program
        for cold, guided in zip(cold_results, guided_results)
    )

    result = {
        "capability_id": "CAP-GEN-004-BTQ-001",
        "central_hypothesis": (
            "Cross-DSL reusable control abstractions can be induced "
            "from quotient execution traces even when solved source "
            "programs share no syntax."
        ),
        "training": {
            "domains": sorted(programs_by_domain),
            "task_count": len(solved),
            "unique_solutions": [
                {
                    "task": row.task_name,
                    "domain": row.domain,
                    "program": row.program_name,
                    "template": {
                        "prefix": row.template.prefix,
                        "motif": row.template.motif,
                        "suffix": row.template.suffix,
                    },
                }
                for row in solved
            ],
            "syntax_bigram_overlap": len(syntax_overlap),
            "training_candidate_executions": training_candidate_executions,
            "solved_trace_executions": solved_trace_executions,
        },
        "learned_library": {
            "template_count": len(library.signatures),
            "templates": [
                {
                    "prefix": signature[0],
                    "motif": signature[1],
                    "suffix": signature[2],
                }
                for signature in library.signatures
            ],
            "cross_domain_support": [
                {
                    "signature": {
                        "prefix": signature[0],
                        "motif": signature[1],
                        "suffix": signature[2],
                    },
                    "domains": domains,
                }
                for signature, domains in library.support
            ],
        },
        "heldout_grid": {
            "task_count": len(cold_results),
            "cold_candidate_count": len(target_programs),
            "guided_candidate_count": len(restricted),
            "all_guided_exact": all_guided_exact,
            "same_solutions_as_cold": same_solutions,
            "results": [
                {
                    "task": guided.task_name,
                    "program": guided.chosen_program,
                    "train_exact": guided.train_exact,
                    "test_accuracy": guided.test_accuracy,
                    "cold_candidates": cold.candidate_count,
                    "guided_candidates": guided.candidate_count,
                }
                for cold, guided in zip(cold_results, guided_results)
            ],
        },
        "resources": {
            "target_index_probe_executions": index_executions,
            "cold_target_candidate_executions": cold_target_executions,
            "guided_target_verification_executions": guided_target_verification,
            "incremental_guided_total": incremental_guided_total,
            "incremental_reduction": cold_target_executions / incremental_guided_total,
            "full_curriculum_total": full_curriculum_total,
            "full_curriculum_surplus_vs_cold_target": cold_target_executions - full_curriculum_total,
            "full_curriculum_reduction_vs_cold_target": cold_target_executions / full_curriculum_total,
        },
        "passed": (
            len(library.signatures) == 3
            and len(syntax_overlap) == 0
            and len(restricted) < len(target_programs)
            and all_guided_exact
            and same_solutions
            and incremental_guided_total < cold_target_executions
            and full_curriculum_total < cold_target_executions
        ),
        "claim_boundary": (
            "DreamCoder, AbstractBeam, ReGAL, abstraction learning, "
            "neural algorithmic reasoning, and trace-based synthesis "
            "are prior art. BTQ-001 is an unverified novelty candidate "
            "for source-agnostic cross-DSL trace-quotient library "
            "learning. This finite prototype is not raw-stream learning, "
            "a public-benchmark result, or evidence of human-level "
            "general intelligence."
        ),
    }
    return result


def main() -> None:
    print(json.dumps(run_experiment(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
