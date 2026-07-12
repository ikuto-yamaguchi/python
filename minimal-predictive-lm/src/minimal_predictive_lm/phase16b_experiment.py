from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

from .aggregate_routing import phase12_prompt_eligibility, routing_guard_description_bits
from .benchmark_harness import RunPolicy, run_command_adapter, score_report
from .phase13a_experiment import build_phase13a_manifest
from .phase15a_experiment import axis_scores
from .phase15a_public_benchmarks import load_phase15a_public_transfer_suite
from .phase16a_public_benchmarks import load_phase16a_public_transfer_suite
from .wordnet_ontology import download_pinned_wordnet


def routing_probe_results() -> dict[str, object]:
    probes = {
        "key_value_state": "state_count=40 delta=12",
        "compact_arithmetic": "What is 3011 times 31?",
        "isolated_product_number": (
            "A long report discusses an expert of Bayer 04 Leverkusen and concludes that "
            "the argument should be reviewed carefully."
        ),
        "multiline_formal_text": (
            "Every reviewer of Product 7 is careful.\n"
            "Is the argument deductively valid or invalid?"
        ),
        "single_version_number": "The release name is Model 8.",
    }
    return {
        name: asdict(phase12_prompt_eligibility(prompt))
        for name, prompt in probes.items()
    }


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
        model_id="mpm-phase15d-before-routing-guard",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase15d_worker"),
        timeout_seconds=300.0,
    )
    after = run_command_adapter(
        third,
        policy,
        model_id="mpm-phase16b-guarded-aggregate",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16b_worker"),
        timeout_seconds=300.0,
    )
    original_after = run_command_adapter(
        original,
        policy,
        model_id="mpm-phase16b-original-regression",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16b_worker"),
        timeout_seconds=300.0,
    )
    second_after = run_command_adapter(
        second,
        policy,
        model_id="mpm-phase16b-second-regression",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16b_worker"),
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
    probes = routing_probe_results()

    return {
        "routing_guard": {
            "description_bits": routing_guard_description_bits(),
            "description_bytes": (routing_guard_description_bits() + 7) // 8,
            "probes": probes,
            "positive_probes_accepted": (
                probes["key_value_state"]["eligible"]
                and probes["compact_arithmetic"]["eligible"]
            ),
            "negative_probes_rejected": all(
                not probes[name]["eligible"]
                for name in (
                    "isolated_product_number",
                    "multiline_formal_text",
                    "single_version_number",
                )
            ),
        },
        "suite": {
            "name": third.name,
            "manifest_sha256": third.sha256,
            "examples": len(third.examples),
            "axes": len(after_axes),
            "wordnet_sha256": source_sha256,
            "benchmark_examples_used_for_training": 0,
            "benchmark_targets_used_for_training": 0,
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
                after_score.answered - after_score.correct
                - (before_score.answered - before_score.correct)
            ),
            "coverage_points": 100 * (after_score.coverage - before_score.coverage),
        },
        "gates": {
            "false_positive_eliminated": (
                before_score.answered - before_score.correct == 1
                and after_score.answered == 0
            ),
            "positive_routing_retained": (
                probes["key_value_state"]["eligible"]
                and probes["compact_arithmetic"]["eligible"]
            ),
            "sparse_number_prose_rejected": all(
                not probes[name]["eligible"]
                for name in (
                    "isolated_product_number",
                    "multiline_formal_text",
                    "single_version_number",
                )
            ),
            "original_public_200_of_200_retained": original_score.correct == 200,
            "second_public_raw_198_of_200_retained": second_score.correct == 198,
            "new_capability_added": False,
            "benchmark_task_name_specialization_used": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "the 160-character and two-number thresholds are human-selected generic routing constraints",
            "the guard improves calibration but adds no reasoning capability",
            "compact prose containing two incidental numbers can still enter the Phase 12 learner",
            "long legitimate arithmetic problems are deliberately left to later structured parsers",
            "the third public slice remains unsolved after the guard",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    guard = payload["routing_guard"]
    before = payload["before"]
    after = payload["after"]
    regressions = payload["regressions"]
    lines = [
        "# Phase 16b results: sparse-number routing guard",
        "",
        "A long formal-logic prompt containing the club name `Bayer 04 Leverkusen`",
        "was incorrectly routed to a compact Phase 12 numeric program and produced `8`.",
        "The guard admits explicit key/value records and compact prompts with at least two",
        "numeric arguments, while rejecting multiline or long sparse-number prose.",
        "",
        "## Guard",
        "",
        f"- payload: **{guard['description_bytes']} bytes**",
        f"- positive probes accepted: **{guard['positive_probes_accepted']}**",
        f"- sparse-number negative probes rejected: **{guard['negative_probes_rejected']}**",
        "",
        "## Third public slice before and after",
        "",
        "| axis | before answered/wrong | after answered/wrong |",
        "|---|---:|---:|",
    ]
    for axis, row in after["axis_scores"].items():
        prior = before["axis_scores"][axis]
        lines.append(
            f"| {axis.replace('_', ' ')} | {prior['answered']}/{prior['wrong']} | {row['answered']}/{row['wrong']} |"
        )
    lines.extend(
        [
            "",
            f"Overall answered/correct: **{before['score']['answered']}/{before['score']['correct']} → {after['score']['answered']}/{after['score']['correct']}**",
            f"Original public regression: **{regressions['original_public']['score']['correct']}/{regressions['original_public']['score']['examples']}**",
            f"Second public raw regression: **{regressions['second_public']['score']['correct']}/{regressions['second_public']['score']['examples']}**",
            "",
            "## Claim boundary",
            "",
            "This phase removes one false positive and improves abstention calibration.",
            "It does not add a new capability or support any general-intelligence claim.",
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
    (output_dir / "phase16b.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "phase16b.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
