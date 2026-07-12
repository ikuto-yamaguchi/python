from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

from .benchmark_harness import RunPolicy, run_command_adapter, score_report
from .generic_proposition_machine import GenericPropositionMachine
from .phase13a_experiment import build_phase13a_manifest
from .phase15a_experiment import axis_scores
from .phase15a_public_benchmarks import load_phase15a_public_transfer_suite
from .phase16a_experiment import failure_examples
from .phase16a_public_benchmarks import load_phase16a_public_transfer_suite
from .wordnet_ontology import download_pinned_wordnet


def run() -> dict[str, object]:
    output_dir = Path("results")
    source_path, source_sha256, _source_bytes = download_pinned_wordnet(
        output_dir / "cache" / "english-wordnet-2025.zip"
    )
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    third = load_phase16a_public_transfer_suite(examples_per_task=40)
    original, _source_hashes = build_phase13a_manifest()
    second = load_phase15a_public_transfer_suite(examples_per_task=40)
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
        third,
        policy,
        model_id="mpm-phase16b-before-proposition-runtime",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16b_worker"),
        timeout_seconds=300.0,
    )
    after = run_command_adapter(
        third,
        policy,
        model_id="mpm-phase16c-shared-proposition-runtime",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16c_worker"),
        timeout_seconds=300.0,
    )
    original_after = run_command_adapter(
        original,
        policy,
        model_id="mpm-phase16c-original-regression",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16c_worker"),
        timeout_seconds=300.0,
    )
    second_after = run_command_adapter(
        second,
        policy,
        model_id="mpm-phase16c-second-regression",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16c_worker"),
        timeout_seconds=300.0,
    )

    before_score = score_report(third, before)
    after_score = score_report(third, after)
    original_score = score_report(original, original_after)
    second_score = score_report(second, second_after)
    before_predictions = {row.example_id: row.text for row in before.predictions}
    after_predictions = {row.example_id: row.text for row in after.predictions}
    before_axes = axis_scores(third, before_predictions)
    after_axes = axis_scores(third, after_predictions)
    runtime = GenericPropositionMachine()

    return {
        "runtime": {
            "name": "shared-parity-and-monadic-proposition-machine",
            "description_bits": runtime.description_bits,
            "description_bytes": (runtime.description_bits + 7) // 8,
            "human_designed_surface_compilers": runtime.human_designed_surface_compilers,
            "benchmark_task_name_branches": runtime.benchmark_task_name_branches,
            "shared_mechanisms": [
                "signed parity constraint propagation",
                "Boolean expression algebra",
                "finite-model entailment for equality-free monadic logic",
                "contradiction-aware abstention",
            ],
            "independent_unit_tests": 6,
        },
        "adaptation_protocol": {
            "public_benchmark_format_inspected": True,
            "public_targets_available_during_post_hoc_audit": True,
            "benchmark_examples_used_for_parameter_training": 0,
            "benchmark_targets_embedded_in_model": 0,
            "benchmark_item_dictionary_entries": 0,
            "task_name_dispatch_branches": 0,
            "strict_zero_shot_claim_allowed": False,
            "classification": "benchmark-informed post-hoc capability adaptation",
        },
        "suite": {
            "name": third.name,
            "manifest_sha256": third.sha256,
            "examples": len(third.examples),
            "axes": len(after_axes),
            "wordnet_sha256": source_sha256,
        },
        "before": {
            "score": asdict(before_score),
            "axis_scores": before_axes,
            "resources": asdict(before.resources),
        },
        "after": {
            "score": asdict(after_score),
            "axis_scores": after_axes,
            "resources": asdict(after.resources),
            "failure_examples": failure_examples(third, after_predictions),
        },
        "regressions": {
            "original_public": {
                "manifest_sha256": original.sha256,
                "score": asdict(original_score),
                "resources": asdict(original_after.resources),
            },
            "second_public": {
                "manifest_sha256": second.sha256,
                "score": asdict(second_score),
                "resources": asdict(second_after.resources),
            },
        },
        "delta": {
            "answered": after_score.answered - before_score.answered,
            "correct": after_score.correct - before_score.correct,
            "wrong": (
                after_score.answered
                - after_score.correct
                - (before_score.answered - before_score.correct)
            ),
            "coverage_points": 100 * (after_score.coverage - before_score.coverage),
            "accuracy_points": 100
            * (after_score.overall_accuracy - before_score.overall_accuracy),
            "model_bytes": after.resources.model_bytes - before.resources.model_bytes,
        },
        "gates": {
            "independent_runtime_tests_declared": True,
            "task_name_specialization_absent": runtime.benchmark_task_name_branches == 0,
            "original_public_200_of_200_retained": original_score.correct == 200,
            "second_public_raw_198_of_200_retained": second_score.correct == 198,
            "belief_propagation_opened": after_axes["belief_propagation"]["correct"] > 0,
            "formal_validity_opened": after_axes["formal_validity"]["correct"] > 0,
            "third_slice_full_parity_allowed": after_score.correct == len(third.examples),
            "strict_zero_shot_claim_allowed": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "the two surface compilers were designed after inspecting public task formats",
            "finite-model search is bounded to at most fourteen predicate atoms per parsed argument",
            "the formal-language compiler covers a controlled fragment and abstains outside it",
            "reference resolution, adjective ordering, and causal judgement are not targeted",
            "the third slice is only a five-task public benchmark sample",
            "free-form dialogue, real-repository coding, long context, multimodal perception, and autonomous parser induction remain untested",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    runtime = payload["runtime"]
    before = payload["before"]
    after = payload["after"]
    regressions = payload["regressions"]
    delta = payload["delta"]
    lines = [
        "# Phase 16c results: shared proposition runtime",
        "",
        "A signed parity graph and a finite-model monadic proposition engine are",
        "shared across quoted truth propagation and controlled formal validity.",
        "The public formats were inspected, so this is post-hoc adaptation rather than",
        "strict zero-shot transfer.",
        "",
        "## Runtime",
        "",
        f"- payload: **{runtime['description_bytes']} bytes**",
        f"- human-designed surface compilers: **{runtime['human_designed_surface_compilers']}**",
        f"- benchmark task-name branches: **{runtime['benchmark_task_name_branches']}**",
        "",
        "## Third public slice",
        "",
        "| axis | before correct/answered | after correct/answered | after wrong |",
        "|---|---:|---:|---:|",
    ]
    for axis, row in after["axis_scores"].items():
        prior = before["axis_scores"][axis]
        lines.append(
            f"| {axis.replace('_', ' ')} | {prior['correct']}/{prior['answered']} | "
            f"{row['correct']}/{row['answered']} | {row['wrong']} |"
        )
    lines.extend(
        [
            "",
            f"Overall correct/answered: **{before['score']['correct']}/{before['score']['answered']} → {after['score']['correct']}/{after['score']['answered']}**",
            f"Accuracy / coverage gain: **{delta['accuracy_points']:.1f} / {delta['coverage_points']:.1f} percentage points**",
            f"Model payload delta: **{delta['model_bytes']} bytes**",
            f"Original public regression: **{regressions['original_public']['score']['correct']}/{regressions['original_public']['score']['examples']}**",
            f"Second public raw regression: **{regressions['second_public']['score']['correct']}/{regressions['second_public']['score']['examples']}**",
            "",
            "## Claim boundary",
            "",
            "This phase may support only the measured proposition capabilities. It does",
            "not establish strict zero-shot transfer, complete third-slice parity, or",
            "general-LLM parity.",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "phase16c.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "phase16c.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
