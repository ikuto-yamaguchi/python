from __future__ import annotations

import csv

from minimal_predictive_lm.jmmlu_exam_baseline import load_jmmlu
from minimal_predictive_lm.university_exam_mastery_contract import (
    DomainResult,
    REQUIRED_DOMAINS,
    UniversityExamMasteryContract,
)


def test_missing_domains_can_never_complete() -> None:
    report = UniversityExamMasteryContract.evaluate({})
    assert report["completion_allowed"] is False
    assert report["highschool_level_passed"] is False
    assert all(value is False for value in report["checks"].values())


def test_every_domain_requires_literal_perfection_and_clean_holdout() -> None:
    perfect = {
        domain.domain_id: DomainResult(
            correct=10,
            total=10,
            independently_held_out=True,
            exact_scoring=True,
        )
        for domain in REQUIRED_DOMAINS
    }
    assert UniversityExamMasteryContract.evaluate(perfect)["completion_allowed"] is True

    first = REQUIRED_DOMAINS[0].domain_id
    imperfect = dict(perfect)
    imperfect[first] = DomainResult(9, 10, True, True)
    assert UniversityExamMasteryContract.evaluate(imperfect)["completion_allowed"] is False

    contaminated = dict(perfect)
    contaminated[first] = DomainResult(10, 10, False, True)
    assert UniversityExamMasteryContract.evaluate(contaminated)["completion_allowed"] is False


def test_jmmlu_loader_hides_subject_from_prompt(tmp_path) -> None:
    directory = tmp_path / "JMMLU" / "test"
    directory.mkdir(parents=True)
    path = directory / "high_school_mathematics.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["question", "A", "B", "C", "D", "answer"])
        writer.writeheader()
        writer.writerow(
            {
                "question": "2+2は？",
                "A": "3",
                "B": "4",
                "C": "5",
                "D": "6",
                "answer": "B",
            }
        )
    # The production loader rejects incomplete subject coverage. Add enough tiny
    # files to exercise that guard without weakening it.
    for index in range(49):
        other = directory / f"subject_{index:02d}.csv"
        other.write_text(path.read_text(encoding="utf-8-sig"), encoding="utf-8-sig")

    rows = load_jmmlu(tmp_path)
    example = rows["high_school_mathematics"][0]
    assert example.answer_index == 1
    assert "high_school_mathematics" not in example.raw_question
    assert "(1)4" in example.raw_question
