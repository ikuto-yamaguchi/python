from fractions import Fraction

from minimal_predictive_lm.phase18b7_shared_linear_constraint_graph import (
    ConstraintGraph,
    LinearConstraint,
    NonIdentifiableConstraintError,
    compile_inequalities,
    compile_linear_system,
    compile_unit_rate,
    evaluate,
    negative_controls,
    permutation_invariance,
    rename_invariance,
    run,
    solve,
    verify,
)


def test_four_task_families_share_one_exact_core():
    accuracy, coverage, verified = evaluate()
    assert (accuracy, coverage, verified) == (1.0, 1.0, 1.0)


def test_exact_fractional_system():
    solution = solve(compile_linear_system(((2, 1, 1), (1, -3, 7))))
    assert dict(solution.values) == {"x": Fraction(10, 7), "y": Fraction(-13, 7)}
    assert verify(compile_linear_system(((2, 1, 1), (1, -3, 7))), solution)


def test_negative_coefficient_flips_inequality():
    solution = solve(compile_inequalities(((-3, "LE", 6), (4, "LT", 20))))
    assert solution.interval.lower == Fraction(-2)
    assert solution.interval.lower_closed
    assert solution.interval.upper == Fraction(5)
    assert not solution.interval.upper_closed


def test_word_problem_compiler_has_no_solver_specific_path():
    solution = solve(compile_unit_rate(17, 900, 500, 11300))
    assert dict(solution.values) == {"x": Fraction(7), "y": Fraction(10)}


def test_order_and_variable_names_are_semantically_irrelevant():
    assert permutation_invariance()
    assert rename_invariance()


def test_unsupported_or_nonidentifiable_cases_abstain():
    assert all(negative_controls().values())
    graph = ConstraintGraph.build(("x", "y"), (LinearConstraint.make({"x": 1, "y": 1}, "EQ", 2, "one"),))
    try:
        solve(graph)
    except NonIdentifiableConstraintError:
        pass
    else:
        raise AssertionError("underdetermined system must abstain")


def test_all_phase18b7_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["new_mathematical_capability"] is False
    assert payload["claim_boundary"]["high_school_intelligence"] is False
