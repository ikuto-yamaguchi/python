#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import audit_statistics_recomputation_binding as subject
import evaluation_contract


def _bundle() -> tuple[list[dict], list[dict]]:
    data: list[dict] = []
    predictions: list[dict] = []
    methods = sorted(evaluation_contract.REQUIRED_METHODS)
    for seed in sorted(evaluation_contract.CANONICAL_SEEDS):
        train_id = f"train-{seed}-a"
        data.append(
            {
                "instance_id": train_id,
                "domain": "messenger",
                "seed": seed,
                "split": "train",
                "condition": "in_distribution",
                "utterance": f"training instruction {seed}",
                "state_before": [seed, -1],
                "gold_action": 0,
                "gold_state_after": [seed, 0],
                "valid_action_mask": [True, True],
            }
        )

        ids = [f"test-{seed}-a", f"test-{seed}-b"]
        for offset, iid in enumerate(ids):
            row = {
                "instance_id": iid,
                "domain": "messenger",
                "seed": seed,
                "split": "test",
                "condition": "in_distribution",
                "utterance": f"evaluation instruction {seed} {offset}",
                "state_before": [offset],
                "gold_action": offset,
                "gold_state_after": [offset + 1],
                "valid_action_mask": [True, True],
            }
            data.append(row)
        by_id = {row["instance_id"]: row for row in data if row["seed"] == seed}
        for method in methods:
            for offset, iid in enumerate(ids):
                donor = ids[1 - offset]
                pred = {
                    "instance_id": iid,
                    "method": method,
                    "instance_fingerprint": evaluation_contract.instance_fingerprint(by_id[iid]),
                    "pred_action": offset,
                    "pred_state_after": [offset + 1],
                }
                if method in evaluation_contract.SHUFFLE_METHODS:
                    pred["control_source_instance_id"] = donor
                    pred["control_source_fingerprint"] = evaluation_contract.instance_fingerprint(by_id[donor])
                if method == "target_label_shuffle":
                    pred["pred_action"] = by_id[donor]["gold_action"]
                elif method == "outcome_shuffle":
                    pred["pred_state_after"] = by_id[donor]["gold_state_after"]
                predictions.append(pred)
    return data, predictions


def test_exact_recomputation_passes() -> None:
    data, predictions = _bundle()
    score = evaluation_contract.score(data, predictions)
    assert score["valid"], score["errors"]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "statistics.json").write_text(json.dumps({"valid": True, "scores": score}), encoding="utf-8")
        result = subject.audit(data, predictions, {"statistics_path": "statistics.json"}, root)
        assert result["valid"], result["errors"]
        assert result["saved_score_sha256"] == result["recomputed_score_sha256"]


def test_fabricated_but_well_formed_statistics_fail() -> None:
    data, predictions = _bundle()
    score = evaluation_contract.score(data, predictions)
    score["summary"]["correct"]["action"] = 0.123456
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "statistics.json").write_text(json.dumps({"valid": True, "scores": score}), encoding="utf-8")
        result = subject.audit(data, predictions, {"statistics_path": "statistics.json"}, root)
        assert not result["valid"]
        assert result["classification"] == "initial_reproduction_failure"
        assert any("do not exactly match" in error for error in result["errors"])


def test_nonfinite_saved_statistics_fail_closed() -> None:
    data, predictions = _bundle()
    score = evaluation_contract.score(data, predictions)
    score["summary"]["correct"]["action"] = float("nan")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "statistics.json").write_text(json.dumps({"valid": True, "scores": score}), encoding="utf-8")
        result = subject.audit(data, predictions, {"statistics_path": "statistics.json"}, root)
        assert not result["valid"]
        assert any("non-canonical or non-finite" in error for error in result["errors"])


if __name__ == "__main__":
    test_exact_recomputation_passes()
    test_fabricated_but_well_formed_statistics_fail()
    test_nonfinite_saved_statistics_fail_closed()
    print("statistics recomputation binding tests passed")
