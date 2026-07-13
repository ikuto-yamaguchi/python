from minimal_predictive_lm.phase18d1_dataset_to_program_meta_learner import NoProgramError, synthesize_program
from minimal_predictive_lm.phase18d2_data_driven_library_growth import (
    evaluate_library_program,
    induce_macro_library,
    load_library_stream,
    no_singleton_macro_control,
    run,
    synthesize_with_library,
)


def _groups():
    tasks = load_library_stream()
    source = tuple(task for task in tasks if task["group"] == "library_training")
    post = tuple(task for task in tasks if task["group"] == "post_library")
    return source, post


def test_repeated_programs_create_expected_macros():
    source, _ = _groups()
    macros, learned = induce_macro_library(source)
    assert set(learned) == {task["id"] for task in source}
    assert {macro.template.render() for macro in macros} == {
        "ADD(@0,@0,@1)",
        "OR(@0,NOT(@1))",
        "REVERSE_STRING(UPPER(@0))",
    }
    assert all(macro.compression_gain > 0 for macro in macros)


def test_post_library_tasks_are_learned_without_source_changes():
    source, post = _groups()
    macros, _ = induce_macro_library(source)
    for task in post:
        program = synthesize_with_library(task, macros)
        assert "M" in program.expression.surface
        assert evaluate_library_program(program, task["test"]) == (len(task["test"]), len(task["test"]))


def test_learned_macro_opens_programs_outside_base_budget():
    source, post = _groups()
    macros, _ = induce_macro_library(source)
    opened = 0
    for task in post:
        try:
            synthesize_program(task)
        except NoProgramError:
            library_program = synthesize_with_library(task, macros)
            correct, total = evaluate_library_program(library_program, task["test"])
            assert correct == total
            opened += 1
    assert opened >= 4


def test_exact_macro_reuse_reduces_search():
    source, post = _groups()
    macros, _ = induce_macro_library(source)
    exact = next(task for task in post if task["id"] == "post-exact-affine")
    base = synthesize_program(exact)
    library = synthesize_with_library(exact, macros)
    assert library.expression.search_cost < base.minimum_cost
    assert library.programs_evaluated < base.programs_evaluated


def test_single_observations_do_not_become_primitives():
    source, _ = _groups()
    assert no_singleton_macro_control(source)


def test_all_phase18d2_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["library"]["macro_count"] == 3
    assert payload["evaluation"]["post_library_correct"] == payload["evaluation"]["post_library_total"]
    assert payload["evaluation"]["base_failures_opened_by_library"] >= 4
    assert payload["campaign"]["source_changes_per_macro"] == 0
    assert payload["claim_boundary"]["arbitrary_primitive_invention"] is False
    assert payload["claim_boundary"]["high_school_intelligence"] is False
