#!/usr/bin/env python3
"""Recompute R0.2 offline policy metrics with the live SILG action semantics.

The original matched comparison reports an unmasked argmax diagnostic.  Live
RTFM evaluation masks actions using the observation's ``valid`` field before
selection.  This evaluator loads the already-trained checkpoints and computes
valid-action-masked action accuracy on the same immutable test instances, while
retaining the unmasked value only as an explicitly labelled diagnostic.

This adds no architecture or training mechanism.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any

import torch
from torch import nn

from evaluate_r02_online_silg import load_method
from gaddy_klein_typed_baseline import CANONICAL_SEEDS, load_rows, validate_rows
from r02_typed_comparison import CONDITIONS, batch_mask, make_loader, sha256, validate_seed

METHODS = ("environment_first", "end_to_end", "state_only")


def _per_row_transition_loss(state_predictions, batch, specs) -> torch.Tensor:
    losses = torch.zeros(batch["action"].shape[0], dtype=torch.float32)
    for spec in specs:
        pred = state_predictions[spec.name]
        gold = batch["after"][spec.name]
        if spec.kind == "categorical":
            loss = nn.functional.cross_entropy(
                pred.flatten(0, 1), gold.long().flatten(), reduction="none"
            ).reshape(batch["action"].shape[0], -1).mean(1)
        elif spec.kind == "binary":
            loss = nn.functional.binary_cross_entropy_with_logits(
                pred, gold.float(), reduction="none"
            ).reshape(batch["action"].shape[0], -1).mean(1)
        else:
            loss = nn.functional.mse_loss(
                pred, gold.float(), reduction="none"
            ).reshape(batch["action"].shape[0], -1).mean(1)
        losses += loss
    return losses / max(1, len(specs))


def _masked_predictions(action_logits: torch.Tensor, batch: dict[str, Any]) -> tuple[torch.Tensor, torch.Tensor]:
    if "valid" not in batch["before"]:
        raise RuntimeError("typed R0.2 state lacks the official SILG valid-action field")
    valid = batch["before"]["valid"].reshape(batch["action"].shape[0], -1).bool()
    logits = action_logits.reshape(batch["action"].shape[0], -1)
    if logits.shape != valid.shape:
        raise RuntimeError(f"action schema mismatch: logits={tuple(logits.shape)} valid={tuple(valid.shape)}")
    if not bool(valid.any(dim=1).all()):
        bad = (~valid.any(dim=1)).nonzero(as_tuple=False).reshape(-1).tolist()
        raise RuntimeError(f"instances expose no valid action: rows={bad}")
    gold = batch["action"].long().reshape(-1)
    if not bool(valid.gather(1, gold.unsqueeze(1)).all()):
        bad = (~valid.gather(1, gold.unsqueeze(1)).reshape(-1)).nonzero(as_tuple=False).reshape(-1).tolist()
        raise RuntimeError(f"gold action is invalid under the exported SILG mask: rows={bad}")
    masked = logits.masked_fill(~valid, float("-inf")).argmax(dim=-1)
    unmasked = logits.argmax(dim=-1)
    return masked, unmasked


def evaluate_method(method: str, checkpoint: Path, rows, specs) -> dict[str, Any]:
    config, forward, parameters, parameter_bytes = load_method(method, checkpoint, specs)
    loader = make_loader(rows, specs, config, shuffle=False)
    totals = {
        condition: {"n": 0, "masked_correct": 0, "unmasked_correct": 0, "transition_loss_sum": 0.0}
        for condition in CONDITIONS
    }
    latencies: list[float] = []
    with torch.inference_mode():
        for batch in loader:
            started = time.perf_counter_ns()
            action_logits = forward(batch["before"], batch["text"])
            latencies.append((time.perf_counter_ns() - started) / 1e6 / max(1, batch["action"].shape[0]))
            masked, unmasked = _masked_predictions(action_logits, batch)

            # Checkpoint loading through load_method returns only action logits, so
            # next-state loss remains sourced from the immutable matched-comparison
            # result.  This file is the authoritative action-policy metric artifact.
            for condition in CONDITIONS:
                select = batch_mask(batch, condition)
                n = int(select.sum())
                if not n:
                    continue
                totals[condition]["n"] += n
                totals[condition]["masked_correct"] += int((masked[select] == batch["action"][select]).sum())
                totals[condition]["unmasked_correct"] += int((unmasked[select] == batch["action"][select]).sum())

    conditions = {}
    for condition, values in totals.items():
        n = values["n"]
        conditions[condition] = {
            "n": n,
            "policy_action_accuracy_valid_masked": None if not n else values["masked_correct"] / n,
            "diagnostic_action_accuracy_unmasked": None if not n else values["unmasked_correct"] / n,
        }
    return {
        "method": method,
        "checkpoint": {"path": str(checkpoint), "bytes": checkpoint.stat().st_size, "sha256": sha256(checkpoint)},
        "parameters": parameters,
        "parameter_bytes": parameter_bytes,
        "conditions": conditions,
        "cpu_inference_ms_per_instance_mean": statistics.fmean(latencies) if latencies else None,
        "cpu_inference_ms_per_instance_median": statistics.median(latencies) if latencies else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True, help="comparison JSON path used as checkpoint stem")
    parser.add_argument("--seed", type=int, choices=CANONICAL_SEEDS, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    rows = load_rows(args.data)
    specs = validate_rows(rows)
    validate_seed(rows, args.seed)
    test = [row for row in rows if row["split"] == "test"]
    if not test:
        raise ValueError("test rows are required")

    stem = args.comparison.with_suffix("")
    checkpoints = {method: Path(f"{stem}.{method}.pt") for method in METHODS}
    missing = [str(path) for path in checkpoints.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing R0.2 checkpoints: {missing}")

    evaluations = [evaluate_method(method, checkpoints[method], test, specs) for method in METHODS]
    payload = {
        "status": "offline_policy_metrics_complete",
        "classification": "R0.2 matched offline policy metric; task success requires online rollout",
        "metric_semantics": {
            "authoritative_action_accuracy": "argmax after applying the exported current-state SILG valid-action mask",
            "unmasked_accuracy": "diagnostic only; not the deployed policy decision rule",
        },
        "seed": args.seed,
        "dataset": {"path": str(args.data), "sha256": sha256(args.data), "n_test": len(test)},
        "evaluations": evaluations,
        "limitations": [
            "this artifact does not substitute action accuracy for online task success",
            "next-state prediction remains in the matched comparison artifact",
            "entity and language-form transfer are inapplicable for RTFM S1",
            "no novelty, intelligence-principle, or capability-progress claim follows from this metric",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
