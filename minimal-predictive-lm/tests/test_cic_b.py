import json
from pathlib import Path

from minimal_predictive_lm.cic_artifact import CICArtifact, artifact_accuracy
from minimal_predictive_lm.cic_training import MathExample, load_mawps, stable_outer_split


def test_fractional_mawps_labels_are_not_truncated(tmp_path: Path) -> None:
    dataset = tmp_path / "mawps.json"
    dataset.write_text(
        json.dumps(
            [
                {"question": "half", "answer": "0.5"},
                {"question": "whole", "answer": "2"},
            ]
        ),
        encoding="utf-8",
    )
    rows = load_mawps(dataset)
    assert rows == [MathExample("whole", 2)]


def test_raw_holdout_is_split_before_synthesis_and_kept_in_denominator() -> None:
    rows = [MathExample(f"question-{index}", index) for index in range(20)]
    train, test = stable_outer_split(rows, test_threshold=5000)
    assert sorted(train + test, key=lambda row: row.question) == sorted(
        rows, key=lambda row: row.question
    )

    empty_artifact = CICArtifact(dimensions=8, mechanisms={}, metadata={})
    correct, total, work = artifact_accuracy(empty_artifact, test)
    assert correct == 0
    assert total == len(test)
    assert work == 0.0
