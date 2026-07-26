#!/usr/bin/env python3
"""Fail-closed qualification gate between R0.1 and R0.2.

This does not modify SILG or introduce a new model. It decides whether the
preserved official recurrent R0.1 bundle demonstrates enough source-policy
competence to make downstream representation/transfer comparisons meaningful.
A failed gate emits an actionable next-run contract instead of treating a
single failed experiment as a completed research iteration.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_SEEDS = (1, 7, 19)
EXPECTED_METHODS = {
    "correct",
    "random",
    "language_blind",
    "state_only",
    "language_shuffle",
}
EXPECTED_SILG = "2af07578e1264029a240fcfb78d4ac0aea16f5de"
EXPECTED_RTFM = "58f17955595b5a127c96d045d896fcbcc7d4b570"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def classify_failures(training: dict[str, Any], matched: dict[str, Any]) -> tuple[list[str], str, dict[str, Any]]:
    failures: list[str] = []

    pins = training.get("source_pins", {})
    if pins.get("silg") != EXPECTED_SILG or pins.get("rtfm") != EXPECTED_RTFM:
        failures.append("source_pin_mismatch")

    if training.get("status") != "success":
        failures.append("training_not_successful")

    declared_seeds = tuple(int(x) for x in training.get("seeds", []))
    if declared_seeds != EXPECTED_SEEDS:
        failures.append("training_seed_mismatch")

    requested_frames = int(training.get("frames_per_seed", -1))
    if requested_frames <= 0:
        failures.append("invalid_requested_frame_budget")

    runs = training.get("runs", [])
    run_by_seed = {int(run.get("seed", -1)): run for run in runs if isinstance(run, dict)}
    for seed in EXPECTED_SEEDS:
        run = run_by_seed.get(seed)
        if run is None:
            failures.append(f"missing_training_seed_{seed}")
            continue
        if not bool(run.get("completed")):
            failures.append(f"training_incomplete_seed_{seed}")
        checkpoint = run.get("checkpoint", {})
        actual_frames = int(checkpoint.get("frames_in_checkpoint", -1)) if isinstance(checkpoint, dict) else -1
        if requested_frames > 0 and actual_frames < requested_frames:
            failures.append(f"frame_budget_not_reached_seed_{seed}")

    if matched.get("status") != "success":
        failures.append("matched_evaluation_not_successful")
    if tuple(int(x) for x in matched.get("seeds", [])) != EXPECTED_SEEDS:
        failures.append("evaluation_seed_mismatch")
    if set(matched.get("methods", [])) != EXPECTED_METHODS:
        failures.append("matched_control_set_mismatch")
    if not bool(matched.get("all_initial_streams_match")):
        failures.append("initial_instance_mismatch")
    if matched.get("answer_leakage") is not False:
        failures.append("answer_leakage_not_explicitly_false")

    aggregate = matched.get("aggregate", {})
    missing_methods = sorted(EXPECTED_METHODS - set(aggregate)) if isinstance(aggregate, dict) else sorted(EXPECTED_METHODS)
    failures.extend(f"missing_aggregate_{method}" for method in missing_methods)

    metrics: dict[str, Any] = {}
    if not missing_methods and isinstance(aggregate, dict):
        correct_win = float(aggregate["correct"].get("win_rate", 0.0))
        random_win = float(aggregate["random"].get("win_rate", 0.0))
        correct_return = float(aggregate["correct"].get("return_mean", 0.0))
        random_return = float(aggregate["random"].get("return_mean", 0.0))
        metrics = {
            "correct_win_rate": correct_win,
            "random_win_rate": random_win,
            "correct_minus_random_win_rate": correct_win - random_win,
            "correct_return_mean": correct_return,
            "random_return_mean": random_return,
            "correct_minus_random_return": correct_return - random_return,
            "control_win_rates": {
                method: float(aggregate[method].get("win_rate", 0.0))
                for method in sorted(EXPECTED_METHODS - {"correct"})
            },
        }
        if correct_win <= 0.0:
            failures.append("zero_source_policy_success")
        if correct_win <= random_win:
            failures.append("correct_not_above_random_win_rate")
        if correct_return <= random_return:
            failures.append("correct_not_above_random_return")

    structural = {
        "source_pin_mismatch",
        "training_not_successful",
        "training_seed_mismatch",
        "invalid_requested_frame_budget",
        "matched_evaluation_not_successful",
        "evaluation_seed_mismatch",
        "matched_control_set_mismatch",
        "initial_instance_mismatch",
        "answer_leakage_not_explicitly_false",
    }
    if any(failure in structural or failure.startswith(("missing_", "training_incomplete_", "frame_budget_")) for failure in failures):
        classification = "implementation_or_artifact_failure"
    elif any(failure.startswith("correct_not_above_") or failure == "zero_source_policy_success" for failure in failures):
        classification = "optimization_or_policy_competence_failure"
    else:
        classification = "qualified"
    return failures, classification, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training", type=Path, required=True)
    parser.add_argument("--matched", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    training = load_json(args.training)
    matched = load_json(args.matched)
    failures, classification, metrics = classify_failures(training, matched)
    qualified = not failures

    payload = {
        "status": "qualified" if qualified else "rejected",
        "qualified_for_r02": qualified,
        "classification": classification,
        "failures": failures,
        "metrics": metrics,
        "fixed_constraints": {
            "source_pins": {"silg": EXPECTED_SILG, "rtfm": EXPECTED_RTFM},
            "seeds": list(EXPECTED_SEEDS),
            "same_instance_controls": sorted(EXPECTED_METHODS),
            "architecture_change_allowed": False,
        },
        "next_run_contract": None if qualified else {
            "iteration_complete": False,
            "required_diagnosis": [
                "compare official command/defaults and deterministic harness patch",
                "inspect action distribution, valid-action use, entropy and episode termination",
                "inspect recurrent reset/detach, frame counting, optimizer and checkpoint restore",
            ],
            "allowed_change": "one diagnosed cause only; keep model family, frames, seeds, split and instances fixed",
            "required_retest": "repeat matched correct/random/language-blind/state-only/language-shuffle evaluation",
            "stop_rule": "do not close the iteration until qualified, a cause is falsified by a matched rerun, or the preregistered screening budget is exhausted",
        },
        "capability_progress_claimed": False,
        "new_intelligence_principle_claimed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not qualified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
