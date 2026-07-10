from __future__ import annotations

from typing import Dict, Sequence

import numpy as np


def binary_gate_metrics(y_true: Sequence[int], ok_prob: Sequence[float], ok_index: int, threshold: float) -> Dict[str, float]:
    y = np.asarray(y_true, dtype=np.int64)
    probability = np.asarray(ok_prob, dtype=np.float64)
    true_ok = y == ok_index
    pred_ok = probability >= threshold
    ok_count = int(true_ok.sum())
    ng_count = int((~true_ok).sum())
    false_ok = int((pred_ok & ~true_ok).sum())
    false_ng = int((~pred_ok & true_ok).sum())
    correct = int((pred_ok == true_ok).sum())
    return {
        "threshold": float(threshold),
        "binary_accuracy": correct / max(1, len(y)),
        "false_ok": float(false_ok),
        "false_ng": float(false_ng),
        "false_ok_rate": false_ok / max(1, ng_count),
        "false_ng_rate": false_ng / max(1, ok_count),
        "ok_count": float(ok_count),
        "ng_count": float(ng_count),
    }


def calibrate_ok_threshold(
    y_true: Sequence[int],
    ok_prob: Sequence[float],
    ok_index: int,
    target_false_ok_rate: float = 0.0,
) -> Dict[str, float]:
    probabilities = np.asarray(ok_prob, dtype=np.float64)
    if probabilities.size == 0:
        return binary_gate_metrics([], [], ok_index, 0.5)
    unique = np.unique(probabilities)
    candidates = np.unique(np.concatenate(([0.0], unique, np.nextafter(unique, np.inf), [1.0 + 1e-7])))
    evaluated = [binary_gate_metrics(y_true, probabilities, ok_index, float(threshold)) for threshold in candidates]
    feasible = [item for item in evaluated if item["false_ok_rate"] <= target_false_ok_rate + 1e-12]
    pool = feasible or evaluated
    best = min(
        pool,
        key=lambda item: (
            item["false_ok_rate"],
            item["false_ng_rate"],
            -item["binary_accuracy"],
            item["threshold"],
        ),
    )
    best["target_false_ok_rate"] = float(target_false_ok_rate)
    best["target_satisfied"] = float(best["false_ok_rate"] <= target_false_ok_rate + 1e-12)
    return best
