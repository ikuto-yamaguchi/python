from minimal_predictive_lm.cap_gen_004_behavioral_trace_quotient import run_experiment
from minimal_predictive_lm.cap_gen_004_btq_core import SynthesisTask, build_trace_index, evaluate_search, guided_programs, induce_cross_domain_library, solve_task
from minimal_predictive_lm.cap_gen_004_btq_grid_domain import grid_probe_inputs, grid_programs
from minimal_predictive_lm.cap_gen_004_btq_sequence_domains import list_programs, string_programs, training_tasks


def test_heldout_grid_transfer_is_exact_and_reduces_search() -> None:
    result = run_experiment()
    assert result["passed"] is True
    assert result["learned_library"]["template_count"] == 3
    assert result["heldout_grid"]["task_count"] == 6
    assert result["heldout_grid"]["cold_candidate_count"] == 70
    assert result["heldout_grid"]["guided_candidate_count"] == 22
    assert result["heldout_grid"]["all_guided_exact"] is True
    assert result["heldout_grid"]["same_solutions_as_cold"] is True
    assert all(row["test_accuracy"] == 1.0 for row in result["heldout_grid"]["results"])
    assert result["resources"]["incremental_guided_total"] == 536
    assert result["resources"]["cold_target_candidate_executions"] == 1260
    assert result["resources"]["full_curriculum_total"] == 923
    assert result["resources"]["full_curriculum_surplus_vs_cold_target"] == 337


def test_unseen_control_skeleton_is_not_falsely_claimed() -> None:
    programs_by_domain = {"string": string_programs(), "list": list_programs()}
    solved = tuple(solve_task(programs_by_domain[task.domain], task) for task in training_tasks())
    library = induce_cross_domain_library(solved)
    target_programs = grid_programs()
    index, _ = build_trace_index(target_programs, grid_probe_inputs())
    guided = guided_programs(index, library)
    transpose_program = next(program for program in target_programs if program.name == "transpose")
    input_grid = ((1, 2, 3), (4, 5, 6))
    expected = transpose_program.run(input_grid)[0]
    task = SynthesisTask("unseen_transpose", "grid", ((input_grid, expected),))
    result = evaluate_search(guided, task)
    assert result.train_exact is False
    assert result.chosen_program is None
