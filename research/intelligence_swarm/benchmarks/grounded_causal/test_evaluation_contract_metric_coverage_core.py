#!/usr/bin/env python3
"""Focused regressions for fail-closed optional inverse-metric coverage."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("evaluation_contract.py")
spec = importlib.util.spec_from_file_location("evaluation_contract", MODULE_PATH)
assert spec and spec.loader
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)

METHODS = sorted(contract.REQUIRED_METHODS)
SEEDS = sorted(contract.CANONICAL_SEEDS)


def make_dataset(*, inverse: str = "all") -> list[dict]:
    rows: list[dict] = []
    for seed in SEEDS:
        rows.append({
            "instance_id": f"train-{seed}",
            "domain": "toy",
            "seed": seed,
            "split": "train",
            "condition": "in_distribution",
            "utterance": f"train command {seed}",
            "state_before": {"position": seed},
            "gold_action": 0,
            "gold_state_after": {"position": seed + 1},
        })
        for index in range(2):
            row = {
                "instance_id": f"test-{seed}-{index}",
                "domain": "toy",
                "seed": seed,
                "split": "test",
                "condition": "in_distribution",
                "utterance": f"evaluation command {seed} {index}",
                "state_before": {"position": seed * 10 + index},
                "gold_action": index,
                "gold_state_after": {"position": seed * 10 + index + 1},
            }
            if inverse == "all" or (inverse == "partial" and not (seed == SEEDS[-1] and index == 1)):
                row["gold_inverse"] = f"inverse-{seed}-{index}"
            rows.append(row)
    return rows


def make_predictions(data: list[dict], *, include_inverse: bool = True) -> list[dict]:
    eval_rows = [row for row in data if row["split"] == "test"]
    by_cell: dict[tuple, list[dict]] = {}
    for row in eval_rows:
        key = (row["seed"], row["domain"], row["split"], row["condition"])
        by_cell.setdefault(key, []).append(row)

    predictions: list[dict] = []
    for method in METHODS:
        for row in eval_rows:
            pred = {
                "instance_id": row["instance_id"],
                "method": method,
                "instance_fingerprint": contract.instance_fingerprint(contract.adapt_row(row)),
                "pred_action": row["gold_action"],
                "pred_state_after": copy.deepcopy(row["gold_state_after"]),
            }
            if include_inverse:
                pred["pred_inverse"] = row.get("gold_inverse", "prediction-only")
            if method in contract.SHUFFLE_METHODS:
                key = (row["seed"], row["domain"], row["split"], row["condition"])
                peers = by_cell[key]
                donor = peers[1] if peers[0]["instance_id"] == row["instance_id"] else peers[0]
                pred["control_source_instance_id"] = donor["instance_id"]
                pred["control_source_fingerprint"] = contract.instance_fingerprint(contract.adapt_row(donor))
                # Keep this optional-metric fixture valid under the later shuffle-value
                # binding contract. The shuffle control's reportable prediction must
                # come from the declared donor, not from the target row.
                if method == "target_label_shuffle":
                    pred["pred_action"] = donor["gold_action"]
                elif method == "outcome_shuffle":
                    pred["pred_state_after"] = copy.deepcopy(donor["gold_state_after"])
            predictions.append(pred)
    return predictions


def assert_no_inverse_statistics(result: dict) -> None:
    assert all("inverse" not in cell for cell in result["cells"]), result
    assert all("inverse" not in summary for summary in result["summary"].values()), result
    assert all("inverse" not in gaps for gaps in result["paired_gaps_vs_correct"].values()), result


def test_complete_inverse_coverage() -> None:
    data = make_dataset(inverse="all")
    result = contract.score(data, make_predictions(data, include_inverse=True))
    assert result["valid"], result
    assert result["inverse_metric_complete"] is True
    assert result["gold_inverse_coverage"] == {"expected": 6, "present": 6}

    cells_by_method: dict[str, list[dict]] = {}
    for cell in result["cells"]:
        cells_by_method.setdefault(cell["method"], []).append(cell)

    # Complete optional-metric coverage remains mandatory for every method, but
    # the later shuffle-scope contract intentionally reports only the field that
    # is causally bound to each shuffle donor.
    for method in METHODS:
        method_cells = cells_by_method[method]
        if method in contract.SHUFFLE_METHODS:
            assert all("inverse" not in cell for cell in method_cells), result
        else:
            assert all(cell.get("inverse") == 1.0 for cell in method_cells), result


def test_selective_prediction_omission_fails_closed() -> None:
    data = make_dataset(inverse="all")
    predictions = make_predictions(data, include_inverse=True)
    victim = next(row for row in predictions if row["method"] == "state_only")
    victim.pop("pred_inverse")
    result = contract.score(data, predictions)
    assert not result["valid"], result
    assert result["classification"] == "initial_reproduction_failure"
    assert any("state_only" in error and "incomplete pred_inverse coverage" in error for error in result["errors"])
    assert result["inverse_metric_complete"] is False
    assert_no_inverse_statistics(result)


def test_partial_gold_inverse_fails_closed() -> None:
    data = make_dataset(inverse="partial")
    result = contract.score(data, make_predictions(data, include_inverse=True))
    assert not result["valid"], result
    assert any("gold_inverse must cover all evaluation instances or none" in error for error in result["errors"])
    assert result["inverse_metric_complete"] is False
    assert_no_inverse_statistics(result)


def test_prediction_only_inverse_fails_closed() -> None:
    data = make_dataset(inverse="none")
    result = contract.score(data, make_predictions(data, include_inverse=True))
    assert not result["valid"], result
    assert any("pred_inverse supplied without any evaluation gold_inverse" in error for error in result["errors"])
    assert result["inverse_metric_complete"] is False
    assert_no_inverse_statistics(result)


def test_inverse_absent_everywhere_is_valid() -> None:
    data = make_dataset(inverse="none")
    result = contract.score(data, make_predictions(data, include_inverse=False))
    assert result["valid"], result
    assert result["inverse_metric_complete"] is False
    assert result["gold_inverse_coverage"] == {"expected": 6, "present": 0}
    assert_no_inverse_statistics(result)


def main() -> None:
    tests = [
        test_complete_inverse_coverage,
        test_selective_prediction_omission_fails_closed,
        test_partial_gold_inverse_fails_closed,
        test_prediction_only_inverse_fails_closed,
        test_inverse_absent_everywhere_is_valid,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)} core optional metric coverage regressions")


if __name__ == "__main__":
    main()
