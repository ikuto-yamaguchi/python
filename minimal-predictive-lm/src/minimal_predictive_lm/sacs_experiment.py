from __future__ import annotations

import json
import resource
import time
from pathlib import Path

import numpy as np

from .sacs_core import (
    FullHistoryAttentionMemory,
    SelectiveAssociativeState,
    SingleVectorRecurrentMemory,
)


def _normalize_rows(values: np.ndarray) -> np.ndarray:
    return values / (np.linalg.norm(values, axis=1, keepdims=True) + 1e-12)


def _cosine(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(left @ right / denominator) if denominator else 0.0


def _evaluate(memory, keys: np.ndarray, values: np.ndarray) -> dict[str, float]:
    cosines: list[float] = []
    nearest_correct = 0
    for index, key in enumerate(keys):
        prediction = memory.read(key)
        cosines.append(_cosine(prediction, values[index]))
        similarities = values @ prediction
        nearest_correct += int(int(np.argmax(similarities)) == index)
    return {
        "mean_cosine": float(np.mean(cosines)),
        "nearest_value_accuracy": nearest_correct / len(keys),
    }


def run_experiment(output: str | Path | None = None) -> dict[str, object]:
    start = time.perf_counter()
    generator = np.random.default_rng(20260716)
    associations = 256
    key_dim = 64
    value_dim = 32
    keys = _normalize_rows(generator.standard_normal((associations, key_dim)).astype(np.float32))
    values = _normalize_rows(generator.standard_normal((associations, value_dim)).astype(np.float32))

    sacs = SelectiveAssociativeState(
        key_dim=key_dim,
        value_dim=value_dim,
        blocks=32,
        top_k=1,
        decays=[1.0] * 32,
        seed=7,
    )
    # Two online passes test whether delta correction repairs interference while
    # keeping the state fixed. No backpropagation or history replay is required
    # at inference time; this is an isolated memory-operator ablation.
    losses: list[float] = []
    for _epoch in range(2):
        for key, value in zip(keys, values):
            losses.append(sacs.update(key, value, learning_rate=1.0))

    full = FullHistoryAttentionMemory(key_dim, value_dim)
    recurrent = SingleVectorRecurrentMemory(value_dim, decay=0.99)
    for key, value in zip(keys, values):
        full.write(key, value)
        recurrent.write(key, value)

    sacs_metrics = _evaluate(sacs, keys, values)
    attention_metrics = _evaluate(full, keys, values)
    recurrent_metrics = _evaluate(recurrent, keys, values)
    sacs_report = sacs.report()

    projected_contexts = (256, 1024, 8192, 65536)
    attention_scaling = {
        str(length): {
            "cache_bytes": length * 4 * (key_dim + value_dim),
            "read_multiply_adds": 2 * length * key_dim,
        }
        for length in projected_contexts
    }
    sacs_scaling = {
        str(length): {
            "state_bytes": sacs_report.total_bytes,
            "read_multiply_adds": sacs_report.read_multiply_adds,
        }
        for length in projected_contexts
    }

    result: dict[str, object] = {
        "capability_id": "SACS-001-FIXED-MEMORY",
        "purpose": "attention-free fixed-memory associative recall operator",
        "associations": associations,
        "key_dim": key_dim,
        "value_dim": value_dim,
        "full_history_attention": {
            **attention_metrics,
            "observed_cache_bytes": full.total_bytes,
            "observed_read_multiply_adds": full.read_multiply_adds,
            "scaling": attention_scaling,
        },
        "single_vector_recurrence": {
            **recurrent_metrics,
            "state_bytes": recurrent.total_bytes,
        },
        "sacs": {
            **sacs_metrics,
            "mean_online_mse": float(np.mean(losses)),
            "final_online_mse": float(np.mean(losses[-associations:])),
            "report": sacs_report.__dict__,
            "scaling": sacs_scaling,
        },
        "fixed_state_independent_of_history": True,
        "kv_cache_used": False,
        "softmax_attention_used": False,
        "gradient_training_used": False,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "SACS-001 validates only the fixed-memory associative operator. It is not a language model and does not "
            "establish high-school-level intelligence. The next milestone must train the operator inside a Japanese "
            "generative recurrent model and compare capability per byte and per operation."
        ),
    }
    result["passed"] = bool(
        sacs_metrics["mean_cosine"] >= 0.78
        and sacs_metrics["nearest_value_accuracy"] >= 0.70
        and sacs_report.total_bytes < attention_scaling["8192"]["cache_bytes"]
        and sacs_report.read_multiply_adds < attention_scaling["8192"]["read_multiply_adds"]
        and recurrent_metrics["nearest_value_accuracy"] < sacs_metrics["nearest_value_accuracy"]
        and result["peak_process_kib"] <= 250_000
    )
    if output is not None:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    print(json.dumps(run_experiment("results/sacs_001_fixed_memory.json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
