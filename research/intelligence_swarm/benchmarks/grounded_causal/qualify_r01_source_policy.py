#!/usr/bin/env python3
"""Fail-closed qualification gate between R0.1 and R0.2.

This does not modify SILG or introduce a new model. It decides whether the
preserved official recurrent R0.1 bundle demonstrates enough source-policy
competence and reproducibility evidence to make downstream representation and
transfer comparisons meaningful.
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


def _positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _valid_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _command_int_option(command: Any, option: str) -> int | None:
    if not isinstance(command, list):
        return None
    try:
        index = command.index(option)
    except ValueError:
        return None
    if index + 1 >= len(command):
        return None
    try:
        value = int(command[index + 1])
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _official_frame_boundary(run: dict[str, Any], requested_frames: int) -> tuple[int | None, int | None]:
    """Return the first learner-update boundary at/above the requested budget.

    SILG stops only after a complete learner batch. For the pinned recurrent
    command, one update consumes ``batch_size * unroll_length`` frames. Thus a
    non-divisible requested budget legitimately produces a small, deterministic
    overshoot; accepting arbitrary ``>=`` values would hide accidental extra
    training, so the exact first boundary is required.
    """
    command = run.get("command")
    batch_size = _command_int_option(command, "--batch_size")
    unroll_length = _command_int_option(command, "--unroll_length")
    if batch_size is None or unroll_length is None or requested_frames <= 0:
        return None, None
    update_frames = batch_size * unroll_length
    expected_checkpoint_frames = ((requested_frames + update_frames - 1) // update_frames) * update_frames
    return expected_checkpoint_frames, update_frames


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

    model_audit = training.get("model_audit", {})
    if not isinstance(model_audit, dict) or model_audit.get("completed") is not True:
        failures.append("missing_model_audit")
    else:
        for field in ("parameters", "trainable_parameters", "state_dict_bytes", "cpu_forward_latency_ms_per_step"):
            if not _positive_number(model_audit.get(field)):
                failures.append(f"invalid_model_audit_{field}")
        if not _valid_sha256(model_audit.get("state_dict_sha256")):
            failures.append("invalid_model_audit_state_dict_sha256")

    runs = training.get("runs", [])
    if not isinstance(runs, list):
        runs = []
        failures.append("invalid_training_runs")
    run_seeds = [int(run.get("seed", -1)) for run in runs if isinstance(run, dict)]
    if tuple(run_seeds) != EXPECTED_SEEDS:
        failures.append("training_run_seed_topology_mismatch")
    if len(set(run_seeds)) != len(run_seeds):
        failures.append("duplicate_training_seed")

    run_by_seed = {int(run.get("seed", -1)): run for run in runs if isinstance(run, dict)}
    for seed in EXPECTED_SEEDS:
        run = run_by_seed.get(seed)
        if run is None:
            failures.append(f"missing_training_seed_{seed}")
            continue
        if not bool(run.get("completed")):
            failures.append(f"training_incomplete_seed_{seed}")
        if not _positive_number(run.get("wall_seconds")):
            failures.append(f"missing_training_wall_time_seed_{seed}")

        resource = run.get("resource", {})
        if not isinstance(resource, dict) or not _positive_number(resource.get("peak_rss_kib")):
            failures.append(f"missing_peak_rss_seed_{seed}")
        if isinstance(resource, dict) and resource.get("exit_status") not in (None, 0):
            failures.append(f"nonzero_resource_exit_status_seed_{seed}")

        if not _valid_sha256(run.get("log_sha256")):
            failures.append(f"invalid_training_log_sha256_seed_{seed}")

        checkpoint = run.get("checkpoint", {})
        if not isinstance(checkpoint, dict):
            checkpoint = {}
        actual_frames = int(checkpoint.get("frames_in_checkpoint", -1))
        expected_frames, update_frames = _official_frame_boundary(run, requested_frames)
        if expected_frames is None or update_frames is None:
            failures.append(f"missing_frame_update_contract_seed_{seed}")
        elif actual_frames != expected_frames:
            failures.append(f"checkpoint_frame_boundary_mismatch_seed_{seed}")
        for field in ("official_checkpoint_bytes", "model_state_bytes"):
            if not _positive_number(checkpoint.get(field)):
                failures.append(f"missing_checkpoint_{field}_seed_{seed}")
        for field in ("official_checkpoint_sha256", "model_state_sha256"):
            if not _valid_sha256(checkpoint.get(field)):
                failures.append(f"invalid_checkpoint_{field}_seed_{seed}")

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

    structural_exact = {
        "source_pin_mismatch",
        "training_not_successful",
        "training_seed_mismatch",
        "invalid_requested_frame_budget",
        "invalid_training_runs",
        "training_run_seed_topology_mismatch",
        "duplicate_training_seed",
        "matched_evaluation_not_successful",
        "evaluation_seed_mismatch",
        "matched_control_set_mismatch",
        "initial_instance_mismatch",
        "answer_leakage_not_explicitly_false",
    }
    structural_prefixes = (
        "missing_",
        "invalid_",
        "training_incomplete_",
        "checkpoint_frame_boundary_",
        "nonzero_resource_",
    )
    if any(failure in structural_exact or failure.startswith(structural_prefixes) for failure in failures):
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
            "resource_and_checksum_audit_required": True,
            "frame_budget_semantics": "first complete official learner-update boundary at or above requested frames",
        },
        "next_run_contract": None if qualified else {
            "iteration_complete": False,
            "required_diagnosis": [
                "compare official command/defaults and deterministic harness patch",
                "inspect action distribution, valid-action use, entropy and episode termination",
                "inspect recurrent reset/detach, frame counting, optimizer and checkpoint restore",
                "repair only the missing or invalid reproducibility evidence when the policy itself qualifies",
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
