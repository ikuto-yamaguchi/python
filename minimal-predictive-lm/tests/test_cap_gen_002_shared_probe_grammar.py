from minimal_predictive_lm.cap_gen_002_shared_probe_grammar import (
    exact_probe_bundle,
    is_monotone_submodular,
    make_greedy_counterexample,
    make_observational_pruning_counterexample,
    make_two_distinction_fixture,
    myopic_marginal_greedy,
    observational_probe_groups,
    run_theory_gate,
    separation_coverage,
    shared_executable_bits,
)


def test_shared_code_and_pair_coverage_are_monotone_submodular():
    grammar = make_two_distinction_fixture()
    names = tuple(probe.name for probe in grammar.probes)

    assert is_monotone_submodular(
        names,
        lambda selected: shared_executable_bits(grammar, selected),
    )
    assert is_monotone_submodular(
        names,
        lambda selected: len(separation_coverage(grammar, selected)),
    )


def test_isolated_accounting_reverses_the_true_shared_optimum():
    grammar = make_two_distinction_fixture()
    shared = exact_probe_bundle(grammar, accounting="shared")
    isolated = exact_probe_bundle(grammar, accounting="isolated")

    assert shared.probes == ("shared-probe-a", "shared-probe-b")
    assert shared.executable_bits == 12
    assert isolated.probes == ("direct-probe-a", "direct-probe-b")
    assert isolated.isolated_bits == 14
    # Under the true union code, the isolated-accounting choice is still larger.
    assert isolated.executable_bits == 14


def test_one_step_marginal_greedy_has_a_parameterized_bad_family():
    grammar = make_greedy_counterexample(6)
    exact = exact_probe_bundle(grammar, accounting="shared")
    greedy = myopic_marginal_greedy(grammar)

    assert all(name.startswith("shared-") for name in exact.probes)
    assert all(name.startswith("direct-") for name in greedy.probes)
    assert exact.executable_bits == 42
    assert greedy.executable_bits == 210
    assert greedy.executable_bits / exact.executable_bits == 5.0


def test_bad_greedy_ratio_increases_with_problem_size():
    ratios = []
    for n in (2, 3, 4, 5, 6):
        grammar = make_greedy_counterexample(n)
        exact = exact_probe_bundle(grammar, accounting="shared")
        greedy = myopic_marginal_greedy(grammar)
        ratios.append(greedy.executable_bits / exact.executable_bits)

    assert ratios == sorted(ratios)
    assert ratios[-1] >= 5.0


def test_observational_probe_pruning_is_not_safe_for_unseen_histories():
    counterexample = make_observational_pruning_counterexample()
    groups = observational_probe_groups(
        counterexample.current_histories,
        counterexample.probes,
        counterexample.responses,
    )

    assert groups == (("probe-left", "probe-right"),)
    assert counterexample.current_signatures_equal()
    assert counterexample.unseen_signatures_differ()


def test_public_api_has_no_task_benchmark_subject_or_axis_identifier():
    names = set(exact_probe_bundle.__code__.co_varnames)
    assert "task_id" not in names
    assert "benchmark" not in names
    assert "subject" not in names
    assert "axis" not in names


def test_end_to_end_shared_probe_theory_gate_passes_with_bounded_claims():
    result = run_theory_gate()

    assert result["passed"] is True
    assert result["two_distinction_fixture"]["shared_optimum_bits"] == 12
    assert result["two_distinction_fixture"]["isolated_optimum_bits"] == 14
    assert result["greedy_counterexample"]["ratio"] == 5.0
    assert result["prospective_pruning_counterexample"]["unseen_signatures_differ"] is True
    assert "prior art" in result["claim_boundary"]
    assert "unverified novelty candidate" in result["claim_boundary"]
