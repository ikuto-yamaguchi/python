#!/usr/bin/env python3
"""Regression tests for Unicode-normalized utterance overlap in evaluation_contract.py."""
from __future__ import annotations

from copy import deepcopy

from evaluation_contract import validate_dataset


def rows(train_text: str, test_text: str) -> list[dict]:
    result = []
    for seed in (1, 7, 19):
        for split, utterance in (("train", train_text), ("test", test_text)):
            result.append(
                {
                    "instance_id": f"{seed}-{split}",
                    "domain": "rtfm_s1",
                    "seed": seed,
                    "split": split,
                    "condition": "in_distribution",
                    "utterance": utterance,
                    "state_before": {"x": seed},
                    "gold_action": 0,
                    "gold_state_after": {"x": seed + 1},
                    "model_input_fields": ["utterance", "state_before"],
                    "model_input": {"utterance": utterance, "state_before": {"x": seed}},
                }
            )
    return result


def assert_failure(train_text: str, test_text: str) -> None:
    result = validate_dataset(rows(train_text, test_text))
    assert not result["valid"], result
    assert result["classification"] if "classification" in result else True
    assert any("Unicode-normalized utterance leakage" in error for error in result["errors"]), result
    assert result["unicode_utterance_overlap_required"] is True


def test_clean_distinct_utterances_pass() -> None:
    result = validate_dataset(rows("take red", "take blue"))
    assert result["valid"], result
    assert result["utterance_overlap"]["test"]["count"] == 0


def test_fullwidth_alias_fails() -> None:
    assert_failure("ＴＡＫＥ　ＲＥＤ", "take red")


def test_combining_character_alias_fails() -> None:
    assert_failure("café", "cafe\u0301")


def test_zero_width_alias_fails() -> None:
    assert_failure("open door", "open\u200bdoor")


def test_overlap_report_keeps_instance_provenance() -> None:
    result = validate_dataset(rows("ＴＡＫＥ　ＲＥＤ", "take red"))
    example = result["utterance_overlap"]["test"]["examples"][0]
    assert example["normalized"] == "takered"
    assert len(example["train_instance_ids"]) == 3
    assert len(example["eval_instance_ids"]) == 3


if __name__ == "__main__":
    test_clean_distinct_utterances_pass()
    test_fullwidth_alias_fails()
    test_combining_character_alias_fails()
    test_zero_width_alias_fails()
    test_overlap_report_keeps_instance_provenance()
    print("ok")
