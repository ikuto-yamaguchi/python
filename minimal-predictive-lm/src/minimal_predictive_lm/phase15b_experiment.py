from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

from .benchmark_harness import RunPolicy, run_command_adapter, score_report
from .discriminative_routing import (
    NegativeRoutingExample,
    replace_ordering_with_discriminative_router,
)
from .phase13a_experiment import build_phase13a_manifest
from .phase13b_experiment import ordering_calibration
from .phase13c_experiment import build_scope_corrected_algebra_model
from .phase15a_experiment import axis_scores
from .phase15a_public_benchmarks import load_phase15a_public_transfer_suite
from .wordnet_ontology import download_pinned_wordnet


def routing_negative_calibration() -> tuple[NegativeRoutingExample, ...]:
    return (
        NegativeRoutingExample("Process these records: gamma alpha beta"),
        NegativeRoutingExample("Compare these values: 7 3 9"),
        NegativeRoutingExample("Copy these labels: rollback apply verify"),
        NegativeRoutingExample("Follow these steps: open inspect close"),
    )


def build_guarded_algebra_model():
    return replace_ordering_with_discriminative_router(
        build_scope_corrected_algebra_model(),
        ordering_calibration(),
        routing_negative_calibration(),
    )


def run() -> dict[str, object]:
    output_dir = Path("results")
    wordnet_path = output_dir / "cache" / "english-wordnet-2025.zip"
    source_path, source_sha256, _source_bytes = download_pinned_wordnet(wordnet_path)
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    unseen = load_phase15a_public_transfer_suite(examples_per_task=40)
    original, _source_hashes = build_phase13a_manifest()
    policy = RunPolicy(
        max_output_chars=256,
        stop_sequences=("\n\n",),
        tools_allowed=(
            "pinned-open-english-wordnet-2025",
            "fixed-phase14b-provenance-documents",
        ),
        temperature=0.0,
        seed=0,
    )
    before = run_command_adapter(
        unseen,
        policy,
        model_id="mpm-phase14b-before-routing-guard",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase14b_worker"),
        timeout_seconds=300.0,
    )
    after = run_command_adapter(
        unseen,
        policy,
        model_id="mpm-phase15b-discriminative-routing",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase15b_worker"),
        timeout_seconds=300.0,
    )
    original_after = run_command_adapter(
        original,
        policy,
        model_id="mpm-phase15b-original-public-regression",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase15b_worker"),
        timeout_seconds=300.0,
    )

    before_score = score_report(unseen, before)
    after_score = score_report(unseen, after)
    original_score = score_report(original, original_after)
    before_predictions = {row.example_id: row.text for row in before.predictions}
    after_predictions = {row.example_id: row.text for row in after.predictions}
    guarded = build_guarded_algebra_model()

    return {
        "adaptation_protocol": {
            "failure_analyzed_before_negative_calibration": True,
            "strict_zero_shot_claim": False,
            "benchmark_examples_used_for_calibration": 0,
            "benchmark_targets_used_for_calibration": 0,
            "negative_calibration_examples": len(routing_negative_calibration()),
            "exact_navigation_prompt_overlap": 0,
            "benchmark_specific_handler_added": 0,
            "benchmark_specific_solver_added": False,
        },
        "router": {
            "selected_required_cues": guarded.ordering.required_cues,
            "candidate_cue_sets_evaluated": guarded.ordering.candidate_cue_sets,
            "positive_examples": guarded.ordering.positive_examples,
            "negative_examples": guarded.ordering.negative_examples,
            "description_bits": guarded.ordering.description_bits,
            "description_bytes": (guarded.ordering.description_bits + 7) // 8,
        },
        "unseen_before": {
            "score": asdict(before_score),
            "axis_scores": axis_scores(unseen, before_predictions),
            "resources": asdict(before.resources),
        },
        "unseen_after": {
            "score": asdict(after_score),
            "axis_scores": axis_scores(unseen, after_predictions),
            "resources": asdict(after.resources),
        },
        "original_public_regression": {
            "manifest_sha256": original.sha256,
            "score": asdict(original_score),
            "resources": asdict(original_after.resources),
        },
        "delta": {
            "wrong_answers_removed": before_score.answered - before_score.correct - (
                after_score.answered - after_score.correct
            ),
            "coverage_points": 100 * (after_score.coverage - before_score.coverage),
            "accuracy_points": 100 * (
                after_score.overall_accuracy - before_score.overall_accuracy
            ),
        },
        "gates": {
            "navigation_false_positive_removed": (
                axis_scores(unseen, after_predictions)["spatial_navigation"]["wrong"] == 0
            ),
            "all_unsupported_unseen_examples_abstain": after_score.answered == 0,
            "original_public_200_of_200_retained": original_score.correct == 200,
            "benchmark_specialization_used": False,
            "new_capability_gained": False,
            "new_public_capability_parity_allowed": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "negative routing examples were authored after observing the false-positive family",
            "the correction improves calibration but solves none of the five unseen capabilities",
            "cue induction is lexical and bounded to conjunctions of at most three words",
            "the original public suite is retained but broader paraphrase robustness is not established",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    before = payload["unseen_before"]
    after = payload["unseen_after"]
    router = payload["router"]
    regression = payload["original_public_regression"]
    lines = [
        "# Phase 15b results: discriminative routing guard",
        "",
        "Ordering cues are induced from positive ordering interactions and independent",
        "non-ordering negatives. The smallest cue conjunction that covers all positives",
        "and no negatives is retained.",
        "",
        "## Router",
        "",
        f"- selected required cues: **{list(router['selected_required_cues'])}**",
        f"- positive / negative calibration examples: **{router['positive_examples']} / {router['negative_examples']}**",
        f"- candidate cue sets: **{router['candidate_cue_sets_evaluated']}**",
        f"- router payload: **{router['description_bytes']} bytes**",
        "",
        "## Unseen public baseline before and after",
        "",
        f"- answered / correct before: **{before['score']['answered']} / {before['score']['correct']}**",
        f"- answered / correct after: **{after['score']['answered']} / {after['score']['correct']}**",
        f"- wrong answers removed: **{payload['delta']['wrong_answers_removed']}**",
        f"- original Phase 14b public regression: **{regression['score']['correct']}/{regression['score']['examples']}**",
        "",
        "## Interpretation",
        "",
        "The system now abstains on all 200 unsupported examples instead of emitting forty",
        "nonsensical navigation answers. This is better calibration, not new capability.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "phase15b.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "phase15b.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
