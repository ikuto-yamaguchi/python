from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

from .benchmark_harness import BenchmarkExample, RunPolicy, answer_is_correct, run_command_adapter, score_report
from .generic_temporal_state import GenericTemporalMachine
from .phase13a_experiment import build_phase13a_manifest
from .phase15a_experiment import axis_scores
from .phase15a_public_benchmarks import load_phase15a_public_transfer_suite
from .wordnet_ontology import download_pinned_wordnet


def cross_domain_temporal_examples() -> tuple[BenchmarkExample, ...]:
    return (
        BenchmarkExample(
            "time_direct_week",
            "temporal",
            (
                "Today is July 14, 2024. What is the date one week from today in MM/DD/YYYY?\n"
                "Options:\n(A) 07/21/2024\n(B) 07/07/2024\n(C) 08/14/2024"
            ),
            "(A)",
            "exact",
        ),
        BenchmarkExample(
            "time_tomorrow_anchor",
            "temporal",
            (
                "Tomorrow is 03/01/2024. What is the date yesterday in MM/DD/YYYY?\n"
                "Options:\n(A) 02/28/2024\n(B) 02/29/2024\n(C) 03/01/2024"
            ),
            "(A)",
            "exact",
        ),
        BenchmarkExample(
            "time_uk_locale",
            "temporal",
            (
                "In the UK, people put the day before the month. Therefore, today is 31/12/2020 to them. "
                "What is the date tomorrow in MM/DD/YYYY?\n"
                "Options:\n(A) 12/31/2020\n(B) 01/01/2021\n(C) 01/31/2021"
            ),
            "(B)",
            "exact",
        ),
        BenchmarkExample(
            "time_elapsed",
            "temporal",
            (
                "Mira deployed on Jan 10, 2020. 30 days have passed since then. "
                "What is the date today in MM/DD/YYYY?\n"
                "Options:\n(A) 02/08/2020\n(B) 02/09/2020\n(C) 02/10/2020"
            ),
            "(B)",
            "exact",
        ),
        BenchmarkExample(
            "time_recurrence",
            "temporal",
            (
                "Mira audits on the 5th of each month starting from the November of 2021. "
                "It is her 4th visit today. What is the date today in MM/DD/YYYY?\n"
                "Options:\n(A) 01/05/2022\n(B) 02/05/2022\n(C) 03/05/2022"
            ),
            "(B)",
            "exact",
        ),
        BenchmarkExample(
            "time_anniversary",
            "temporal",
            (
                "Mira and Sol married on Mar 3, 2010. It is their 12-year anniversary today. "
                "What is the date a month ago in MM/DD/YYYY?\n"
                "Options:\n(A) 02/03/2022\n(B) 03/03/2021\n(C) 02/03/2021"
            ),
            "(A)",
            "exact",
        ),
    )


def cross_domain_score(machine: GenericTemporalMachine) -> dict[str, object]:
    rows = cross_domain_temporal_examples()
    correct = 0
    predictions: dict[str, str] = {}
    reasons: dict[str, str] = {}
    for row in rows:
        prediction = machine.predict(row.prompt)
        text = prediction.output or "__ABSTAIN__"
        predictions[row.example_id] = text
        reasons[row.example_id] = prediction.anchor_reason
        correct += int(answer_is_correct(row, text))
    return {
        "examples": len(rows),
        "correct": correct,
        "accuracy": correct / len(rows),
        "predictions": predictions,
        "anchor_reasons": reasons,
    }


def date_diagnostics(manifest, machine: GenericTemporalMachine) -> dict[str, object]:
    failures: list[dict[str, str]] = []
    reason_counts: dict[str, int] = {}
    correct = answered = 0
    for row in manifest.examples:
        if row.axis != "date_understanding":
            continue
        prediction = machine.predict(row.prompt)
        reason_counts[prediction.anchor_reason] = reason_counts.get(prediction.anchor_reason, 0) + 1
        text = prediction.output or "__ABSTAIN__"
        answered += int(prediction.output is not None)
        is_correct = answer_is_correct(row, text)
        correct += int(is_correct)
        if not is_correct:
            failures.append(
                {
                    "id": row.example_id,
                    "target": row.target,
                    "prediction": text,
                    "anchor_reason": prediction.anchor_reason,
                    "prompt": row.prompt,
                }
            )
    return {
        "examples": 40,
        "answered": answered,
        "correct": correct,
        "reason_counts": reason_counts,
        "failures": failures,
    }


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
        model_id="mpm-phase15c-shared-state-runtime",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase15c_worker"),
        timeout_seconds=300.0,
    )
    after = run_command_adapter(
        unseen,
        policy,
        model_id="mpm-phase15d-temporal-state-runtime",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase15d_worker"),
        timeout_seconds=300.0,
    )
    original_after = run_command_adapter(
        original,
        policy,
        model_id="mpm-phase15d-original-public-regression",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase15d_worker"),
        timeout_seconds=300.0,
    )

    before_score = score_report(unseen, before)
    after_score = score_report(unseen, after)
    original_score = score_report(original, original_after)
    before_predictions = {row.example_id: row.text for row in before.predictions}
    after_predictions = {row.example_id: row.text for row in after.predictions}
    after_axes = axis_scores(unseen, after_predictions)
    machine = GenericTemporalMachine()
    heldout = cross_domain_score(machine)
    diagnostics = date_diagnostics(unseen, machine)

    return {
        "adaptation_protocol": {
            "public_date_surface_formats_inspected": True,
            "strict_zero_shot_claim": False,
            "benchmark_examples_used_as_training_rows": 0,
            "benchmark_targets_used_as_training_rows": 0,
            "human_designed_temporal_compiler": 1,
            "benchmark_task_name_branches": machine.benchmark_task_name_branches,
            "ambiguous_subday_anchor_forces_abstention": True,
        },
        "temporal_machine": {
            "description_bits": machine.description_bits,
            "description_bytes": (machine.description_bits + 7) // 8,
            "state": machine.render()["state"],
            "events": machine.render()["events"],
            "query": machine.render()["query"],
            "cross_domain_heldout": heldout,
            "public_date_diagnostics": diagnostics,
        },
        "suite": {
            "name": unseen.name,
            "manifest_sha256": unseen.sha256,
            "examples": len(unseen.examples),
            "axes": len(after_axes),
            "wordnet_sha256": source_sha256,
        },
        "before": {
            "score": asdict(before_score),
            "axis_scores": axis_scores(unseen, before_predictions),
            "resources": asdict(before.resources),
        },
        "after": {
            "score": asdict(after_score),
            "axis_scores": after_axes,
            "resources": asdict(after.resources),
        },
        "original_public_regression": {
            "manifest_sha256": original.sha256,
            "score": asdict(original_score),
            "resources": asdict(original_after.resources),
        },
        "delta": {
            "correct": after_score.correct - before_score.correct,
            "answered": after_score.answered - before_score.answered,
            "accuracy_points": 100 * (
                after_score.overall_accuracy - before_score.overall_accuracy
            ),
            "coverage_points": 100 * (after_score.coverage - before_score.coverage),
        },
        "gates": {
            "cross_domain_temporal_transfer_passed": heldout["accuracy"] == 1.0,
            "date_axis_has_zero_wrong_answers": after_axes["date_understanding"]["wrong"] == 0,
            "date_axis_at_least_39_correct": after_axes["date_understanding"]["correct"] >= 39,
            "all_answered_predictions_correct": after_score.answered == after_score.correct,
            "original_public_200_of_200_retained": original_score.correct == 200,
            "benchmark_task_name_specialization_used": False,
            "benchmark_surface_adaptation_used": True,
            "general_temporal_claim_allowed": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "the temporal surface compiler was human-designed after inspecting public date formats",
            "holiday and special-calendar anchors are limited to explicitly implemented generic rules",
            "the compiler treats sub-day future statements without a time-of-day as unidentifiable",
            "natural-language temporal reference resolution remains rule-bounded rather than induced",
            "no matched open-model comparison is included",
            "free-form dialogue, coding, long context, multimodal perception, and autonomous grammar induction remain untested",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    protocol = payload["adaptation_protocol"]
    machine = payload["temporal_machine"]
    before = payload["before"]
    after = payload["after"]
    regression = payload["original_public_regression"]
    lines = [
        "# Phase 15d results: temporal state runtime",
        "",
        "Raw date statements compile into a `today` state, one calendar transition,",
        "and a multiple-choice projection. Missing time-of-day information can leave a",
        "sub-day anchor unidentifiable, in which case the model abstains.",
        "",
        "## Adaptation disclosure",
        "",
        f"- public date formats inspected: **{protocol['public_date_surface_formats_inspected']}**",
        f"- strict zero-shot claim: **{protocol['strict_zero_shot_claim']}**",
        f"- human-designed temporal compilers: **{protocol['human_designed_temporal_compiler']}**",
        f"- benchmark task-name branches: **{protocol['benchmark_task_name_branches']}**",
        "",
        "## Temporal runtime",
        "",
        f"- payload: **{machine['description_bytes']} bytes**",
        f"- state / events: **{machine['state']} / {machine['events']}**",
        f"- cross-domain held-out: **{machine['cross_domain_heldout']['correct']}/{machine['cross_domain_heldout']['examples']}**",
        "",
        "## Public accuracy before and after",
        "",
        "| axis | Phase 15c | Phase 15d | answered | wrong |",
        "|---|---:|---:|---:|---:|",
    ]
    for axis, row in after["axis_scores"].items():
        lines.append(
            f"| {axis.replace('_', ' ')} | {100 * before['axis_scores'][axis]['accuracy']:.1f}% | {100 * row['accuracy']:.1f}% | {row['answered']} | {row['wrong']} |"
        )
    lines.extend(
        [
            "",
            f"Overall: **{100 * before['score']['overall_accuracy']:.1f}% → {100 * after['score']['overall_accuracy']:.1f}%**",
            f"Answered/correct: **{after['score']['answered']} / {after['score']['correct']}**",
            f"Original public regression: **{regression['score']['correct']}/{regression['score']['examples']}**",
            f"Date failures saved: **{len(machine['public_date_diagnostics']['failures'])}**",
            "",
            "## Claim boundary",
            "",
            "This is a benchmark-informed temporal compiler, not open-ended language",
            "understanding or autonomous discovery of calendar semantics.",
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
    (output_dir / "phase15d.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "phase15d.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
