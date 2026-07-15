from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

from .cic_artifact import CICArtifact, artifact_accuracy
from .cic_training import (
    choose_epochs,
    compile_candidates,
    load_mawps,
    stable_outer_split,
    train_raw_model,
)


def run_experiment(dataset: str | Path, output: str | Path | None = None) -> dict[str, object]:
    start = time.perf_counter()
    examples = load_mawps(dataset)
    raw_train, raw_test = stable_outer_split(examples)
    train_rows, expansions = compile_candidates(raw_train)
    selected_epochs, validation_scores = choose_epochs(train_rows)
    model = train_raw_model(train_rows, epochs=selected_epochs)
    full = CICArtifact.from_raw(
        model,
        quantization_limit=127,
        metadata={"variant": "full", "selected_epochs": selected_epochs},
    )
    compact = CICArtifact.from_raw(
        model,
        top_weights=512,
        quantization_limit=7,
        metadata={"variant": "compact", "selected_epochs": selected_epochs},
    )
    full_correct, total, full_work = artifact_accuracy(full, raw_test)
    compact_correct, _total, compact_work = artifact_accuracy(compact, raw_test)
    elapsed = time.perf_counter() - start
    result: dict[str, object] = {
        "capability_id": "CIC-001-MAWPS-CORRECTED",
        "neural_network_used": False,
        "gradient_training_used": False,
        "dataset": {
            "integer_label_rows": len(examples),
            "raw_train_rows": len(raw_train),
            "synthesizable_train_rows": len(train_rows),
            "untouched_raw_test_rows": len(raw_test),
            "fractional_rows_skipped_without_truncation": True,
            "split_before_answer_driven_synthesis": True,
            "split": "sha256(question) mod 10000 < 2000",
        },
        "selection": {
            "selected_epochs": selected_epochs,
            "inner_validation_accuracy_by_epoch": validation_scores,
            "test_used_for_selection": False,
        },
        "full": {
            "correct": full_correct,
            "total": total,
            "accuracy": full_correct / total if total else 0.0,
            "artifact_bytes": len(full.to_bytes()),
            "mechanisms": len(full.mechanisms),
            "mean_checked_mechanisms": full_work,
        },
        "compact": {
            "correct": compact_correct,
            "total": total,
            "accuracy": compact_correct / total if total else 0.0,
            "artifact_bytes": len(compact.to_bytes()),
            "mechanisms": len(compact.mechanisms),
            "weights_per_mechanism_limit": 512,
            "quantization_levels": 15,
            "mean_checked_mechanisms": compact_work,
        },
        "resources": {
            "training_synthesis_expansions": expansions,
            "elapsed_seconds": elapsed,
            "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "claim_boundary": (
            "This corrected result evaluates every raw holdout row after splitting before "
            "answer-driven synthesis. CIC remains arithmetic-only, not general dialogue, "
            "not Japanese high-school-level intelligence, and not evidence of globally "
            "minimal compute or memory."
        ),
    }
    # Do not reuse the invalidated accuracy thresholds from CIC-001. This run is
    # for obtaining an unbiased replacement measurement first.
    result["passed"] = False
    if output is not None:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        full.save(output_path.with_suffix(".full.cic"))
        compact.save(output_path.with_suffix(".compact.cic"))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the corrected CIC public MAWPS experiment")
    parser.add_argument("dataset")
    parser.add_argument("--output", default="results/cic_001_corrected_mawps.json")
    args = parser.parse_args()
    print(json.dumps(run_experiment(args.dataset, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
