from minimal_predictive_lm.cap_gen_004_btq_core import induce_cross_domain_library, solve_task, source_ngram_overlap
from minimal_predictive_lm.cap_gen_004_btq_sequence_domains import list_programs, string_programs, training_tasks


def _solved():
    programs = {"string": string_programs(), "list": list_programs()}
    return tuple(solve_task(programs[task.domain], task) for task in training_tasks())


def test_library_is_supported_by_two_source_incompatible_domains() -> None:
    solved = _solved()
    library = induce_cross_domain_library(solved)
    assert len(library.signatures) == 3
    assert all(domains == ("list", "string") for _, domains in library.support)
    assert source_ngram_overlap(solved, n=2) == ()


def test_one_domain_is_not_enough_for_cross_domain_promotion() -> None:
    solved = tuple(row for row in _solved() if row.domain == "string")
    library = induce_cross_domain_library(solved)
    assert library.signatures == ()
