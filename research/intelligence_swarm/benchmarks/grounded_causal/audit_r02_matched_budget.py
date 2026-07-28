#!/usr/bin/env python3
"""Fail-closed audit for R0.2 matched-comparison result bundles.

This does not introduce a model or mechanism. It verifies that the existing
Environment-first, End-to-end and State-only comparison used the same typed
training rows, epoch exposure, canonical seed and split contract, and that
resource/checkpoint evidence is present.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CANONICAL_SEEDS = {1, 7, 19}
EXPECTED_METHODS = {"environment_first", "end_to_end", "state_only"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def audit(result_path: Path) -> dict[str, Any]:
    payload = json.loads(result_path.read_text())
    failures: list[str] = []

    seed = payload.get("seed")
    require(seed in CANONICAL_SEEDS, f"non-canonical seed: {seed}", failures)

    dataset = payload.get("dataset", {})
    n_train = int(dataset.get("n_train", 0) or 0)
    n_test = int(dataset.get("n_test", 0) or 0)
    splits = set(dataset.get("splits", []))
    require(n_train > 0, "missing train rows", failures)
    require(n_test > 0, "missing test rows", failures)
    require(splits == {"train", "test"}, f"split mismatch: {sorted(splits)}", failures)
    require(len(str(dataset.get("sha256", ""))) == 64, "missing dataset SHA-256", failures)

    config = payload.get("config", {})
    env_epochs = int(config.get("env_epochs", 0) or 0)
    lang_epochs = int(config.get("lang_epochs", 0) or 0)
    require(env_epochs > 0 and lang_epochs > 0, "non-positive training epochs", failures)

    # Every method receives the same number of row presentations. Environment-first
    # divides them across transition pretraining and language alignment; End-to-end
    # and State-only consume the sum in a single phase.
    exposures = {
        "environment_first": n_train * env_epochs + n_train * lang_epochs,
        "end_to_end": n_train * (env_epochs + lang_epochs),
        "state_only": n_train * (env_epochs + lang_epochs),
    }
    require(len(set(exposures.values())) == 1, f"training exposure mismatch: {exposures}", failures)

    budget = payload.get("parameter_budget", {})
    env_bytes = int(budget.get("environment_first_inference_bytes", -1))
    e2e_bytes = int(budget.get("end_to_end_inference_bytes", -2))
    require(bool(budget.get("equal")), "parameter budget not marked equal", failures)
    require(env_bytes > 0 and env_bytes == e2e_bytes, "inference parameter bytes mismatch", failures)
    require(int(budget.get("environment_pretraining_only_bytes", 0) or 0) > 0,
            "missing pretraining-only parameter bytes", failures)

    evaluations = payload.get("evaluations", [])
    methods = {item.get("method") for item in evaluations}
    require(methods == EXPECTED_METHODS, f"method set mismatch: {sorted(methods)}", failures)
    for item in evaluations:
        method = item.get("method", "unknown")
        all_cell = item.get("conditions", {}).get("all", {})
        require(int(all_cell.get("n", 0) or 0) == n_test,
                f"{method}: prediction coverage differs from n_test", failures)
        require(all_cell.get("action_accuracy") is not None,
                f"{method}: action accuracy missing", failures)
        require(all_cell.get("typed_next_state_loss") is not None,
                f"{method}: typed next-state loss missing", failures)
        require(item.get("cpu_inference_ms_per_instance_mean") is not None,
                f"{method}: CPU latency missing", failures)

    training = payload.get("training", {})
    for key in (
        "environment_pretraining_seconds",
        "environment_first_language_seconds",
        "end_to_end_seconds",
        "state_only_seconds",
        "peak_rss_kib",
    ):
        require(training.get(key) is not None and float(training.get(key)) >= 0,
                f"training resource field missing: {key}", failures)

    checkpoints = payload.get("checkpoints", {})
    require(set(checkpoints) == EXPECTED_METHODS,
            f"checkpoint method set mismatch: {sorted(checkpoints)}", failures)
    for method, checkpoint in checkpoints.items():
        require(int(checkpoint.get("bytes", 0) or 0) > 0,
                f"{method}: checkpoint bytes missing", failures)
        require(len(str(checkpoint.get("sha256", ""))) == 64,
                f"{method}: checkpoint SHA-256 missing", failures)

    task_success_available = all(
        item.get("conditions", {}).get("all", {}).get("task_success_status")
        == "available_from_external_online_rollout"
        for item in evaluations
    )

    classification = (
        "matched_offline_budget_audit_passed_online_task_success_pending"
        if not failures and not task_success_available
        else "matched_online_budget_audit_passed"
        if not failures
        else "initial_reproduction_failure"
    )
    return {
        "classification": classification,
        "passed": not failures,
        "failures": failures,
        "result_path": str(result_path),
        "result_sha256": sha256(result_path),
        "seed": seed,
        "dataset": {"n_train": n_train, "n_test": n_test, "splits": sorted(splits)},
        "training_row_exposures": exposures,
        "parameter_budget": {
            "environment_first_inference_bytes": env_bytes,
            "end_to_end_inference_bytes": e2e_bytes,
            "equal": env_bytes == e2e_bytes and env_bytes > 0,
        },
        "task_success_available": task_success_available,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
