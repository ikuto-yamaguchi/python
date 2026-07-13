from pathlib import Path
import json

import pytest

from minimal_predictive_lm.phase19a_general_learning_reality_gate import (
    CorpusFile,
    stable_rank,
)
from minimal_predictive_lm.phase19b_domain_holdout_transfer_gate import (
    evaluate_transfer,
    run_gate,
)


def row(path: str, domain: str, text: str) -> CorpusFile:
    return CorpusFile(path, domain, text.encode(), stable_rank(path))


def shared_rows():
    train = []
    heldout = []
    for domain, suffix in (
        ("code", ".py"),
        ("prose", ".md"),
        ("structured", ".json"),
    ):
        for index in range(12):
            text = (
                f"common alpha beta domain_{domain} item_{index % 3} "
                "value value value\n"
            ) * 20
            target = heldout if index % 5 == 0 else train
            target.append(row(f"{domain}/f{index}{suffix}", domain, text))
    return tuple(train), tuple(heldout)


def test_target_domain_is_never_in_source():
    train, heldout = shared_rows()
    result = evaluate_transfer(train, heldout, "prose")
    assert result["checks"]["target_domain_excluded_from_source"]
    assert set(result["source_domains"]) == {"code", "structured"}
    assert all("/f" in path for path in result["target_paths"])


def test_transfer_is_deterministic():
    train, heldout = shared_rows()
    assert evaluate_transfer(train, heldout, "code") == evaluate_transfer(
        train, heldout, "code"
    )


def test_unknown_domain_rejected():
    train, heldout = shared_rows()
    with pytest.raises(ValueError):
        evaluate_transfer(train, heldout, "image")


def test_empty_target_is_rejected():
    train, heldout = shared_rows()
    without_code = tuple(row for row in heldout if row.domain != "code")
    with pytest.raises(ValueError):
        evaluate_transfer(train, without_code, "code")


def test_gate_uses_only_generic_corpus_fields(tmp_path: Path):
    for index in range(15):
        (tmp_path / f"c{index}.py").write_text(
            ("shared token python value\n" * 40) + str(index), encoding="utf-8"
        )
        (tmp_path / f"p{index}.md").write_text(
            ("shared token prose value\n" * 40) + str(index), encoding="utf-8"
        )
        (tmp_path / f"s{index}.json").write_text(
            json.dumps({"shared": ["token", "value"] * 40, "i": index}),
            encoding="utf-8",
        )
    result = run_gate(tmp_path)
    assert result["checks"]["no_task_labels"]
    assert result["checks"]["all_target_domains_fully_excluded"]
