from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

from .benchmark_harness import BenchmarkExample, RunPolicy, answer_is_correct, run_command_adapter, score_report
from .generic_state_machine import GenericStateMachine
from .phase13a_experiment import build_phase13a_manifest
from .phase15a_experiment import axis_scores
from .phase15a_public_benchmarks import load_phase15a_public_transfer_suite
from .wordnet_ontology import download_pinned_wordnet


def cross_domain_state_examples() -> tuple[BenchmarkExample, ...]:
    return (
        BenchmarkExample(
            "state_stack_1",
            "stack",
            "Complete the structure. Input: { [ (",
            ") ] }",
            "exact",
        ),
        BenchmarkExample(
            "state_stack_2",
            "stack",
            "Complete the structure. Input: < { [ ]",
            "} >",
            "exact",
        ),
        BenchmarkExample(
            "state_vector_absolute",
            "vector",
            (
                "If you follow these instructions, do you return to the starting point? "
                "Always face forward. Take 3 steps left. Take 3 steps right.\n"
                "Options:\n- Yes\n- No"
            ),
            "Yes",
            "exact",
        ),
        BenchmarkExample(
            "state_vector_relative",
            "vector",
            (
                "If you follow these instructions, do you return to the starting point? "
                "Take 4 steps. Turn around. Take 4 steps.\n"
                "Options:\n- Yes\n- No"
            ),
            "Yes",
            "exact",
        ),
        BenchmarkExample(
            "state_mapping_api",
            "mapping",
            (
                "Nora, Omar, and Priya maintain three API tokens. At the start of the deployment, "
                "Nora has alpha, Omar has beta, and Priya has gamma.\n"
                "As the deployment proceeds, they exchange tokens. First, Nora and Omar swap tokens. "
                "Then, Omar and Priya swap tokens. Finally, Nora and Priya swap tokens. "
                "At the end of the deployment, Nora has\n"
                "Options:\n(A) alpha\n(B) beta\n(C) gamma"
            ),
            "(A)",
            "exact",
        ),
        BenchmarkExample(
            "state_mapping_services",
            "mapping",
            (
                "Ava, Ben, and Cora own three services. At the start of the incident, "
                "Ava has search, Ben has billing, and Cora has storage.\n"
                "As the incident proceeds, they exchange ownership. First, Ava and Cora swap services. "
                "Then, Ben and Cora swap services. Finally, Ava and Ben swap services. "
                "At the end of the incident, Cora has\n"
                "Options:\n(A) search\n(B) billing\n(C) storage"
            ),
            "(B)",
            "exact",
        ),
        BenchmarkExample(
            "state_order_queue",
            "order",
            (
                "In a queue, there are three jobs: parse, build, and deploy. "
                "The build is to the right of parse. Deploy is to the right of build.\n"
                "Options:\n(A) Parse is the rightmost\n(B) Build is the rightmost\n(C) Deploy is the rightmost"
            ),
            "(C)",
            "exact",
        ),
        BenchmarkExample(
            "state_order_versions",
            "order",
            (
                "There are three releases: alpha, beta, and gamma. "
                "Beta is newer than alpha. Gamma is newer than beta.\n"
                "Options:\n(A) Alpha is the newest\n(B) Beta is the newest\n(C) Gamma is the newest"
            ),
            "(C)",
            "exact",
        ),
    )


def cross_domain_score(machine: GenericStateMachine) -> dict[str, object]:
    rows = cross_domain_state_examples()
    predictions: dict[str, str] = {}
    families: dict[str, int] = {}
    correct = 0
    for row in rows:
        prediction = machine.predict(row.prompt)
        text = prediction.output or "__ABSTAIN__"
        predictions[row.example_id] = text
        if prediction.family is not None:
            families[prediction.family] = families.get(prediction.family, 0) + 1
        correct += int(answer_is_correct(row, text))
    return {
        "examples": len(rows),
        "correct": correct,
        "accuracy": correct / len(rows),
        "families": families,
        "predictions": predictions,
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
        model_id="mpm-phase15b-calibrated-abstention",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase15b_worker"),
        timeout_seconds=300.0,
    )
    after = run_command_adapter(
        unseen,
        policy,
        model_id="mpm-phase15c-shared-state-runtime",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase15c_worker"),
        timeout_seconds=300.0,
    )
    original_after = run_command_adapter(
        original,
        policy,
        model_id="mpm-phase15c-original-public-regression",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase15c_worker"),
        timeout_seconds=300.0,
    )

    before_score = score_report(unseen, before)
    after_score = score_report(unseen, after)
    original_score = score_report(original, original_after)
    before_predictions = {row.example_id: row.text for row in before.predictions}
    after_predictions = {row.example_id: row.text for row in after.predictions}
    after_axes = axis_scores(unseen, after_predictions)
    machine = GenericStateMachine()
    heldout = cross_domain_score(machine)

    return {
        "adaptation_protocol": {
            "public_surface_formats_inspected": True,
            "strict_zero_shot_claim": False,
            "benchmark_examples_used_as_training_rows": 0,
            "benchmark_targets_used_as_training_rows": 0,
            "human_designed_surface_compilers": machine.compiler_count,
            "benchmark_task_name_branches": machine.benchmark_task_name_branches,
            "shared_runtime": True,
            "date_capability_intentionally_not_added": True,
        },
        "state_machine": {
            "description_bits": machine.description_bits,
            "description_bytes": (machine.description_bits + 7) // 8,
            "runtime_operations": machine.render()["runtime_operations"],
            "query_operations": machine.render()["query_operations"],
            "compiler_count": machine.compiler_count,
            "benchmark_task_name_branches": machine.benchmark_task_name_branches,
            "cross_domain_heldout": heldout,
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
            "cross_domain_shared_runtime_passed": heldout["accuracy"] == 1.0,
            "four_state_axes_fully_resolved": all(
                after_axes[axis]["accuracy"] == 1.0
                for axis in (
                    "logical_ordering",
                    "state_permutation_tracking",
                    "spatial_navigation",
                    "stack_completion",
                )
            ),
            "date_axis_remains_abstention": (
                after_axes["date_understanding"]["answered"] == 0
            ),
            "all_answered_predictions_correct": after_score.answered == after_score.correct,
            "original_public_200_of_200_retained": original_score.correct == 200,
            "benchmark_task_name_specialization_used": False,
            "benchmark_surface_adaptation_used": True,
            "general_runtime_claim_allowed": False,
            "new_public_capability_parity_allowed": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "the four raw surface compilers were human-designed after inspecting the public task formats",
            "a shared runtime does not remove the format-specific parsing burden",
            "order constraints are solved by enumerating all permutations and therefore do not scale",
            "the mapping compiler assumes proper-name agents and explicit three-stage swap language",
            "the navigation compiler supports the benchmark's bounded absolute or relative command styles",
            "date understanding is deliberately unsolved and remains an abstention",
            "no matched open-model comparison is included",
            "free-form dialogue, coding, long context, multimodal perception, and autonomous parser induction remain untested",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    protocol = payload["adaptation_protocol"]
    machine = payload["state_machine"]
    before = payload["before"]
    after = payload["after"]
    regression = payload["original_public_regression"]
    lines = [
        "# Phase 15c results: shared event-sourced state runtime",
        "",
        "Four raw formats compile into one initial-state / event-list / query-projection",
        "runtime. The runtime contains stack, vector, mapping, and partial-order state,",
        "while date understanding is intentionally left unsupported.",
        "",
        "## Adaptation disclosure",
        "",
        f"- public surface formats inspected: **{protocol['public_surface_formats_inspected']}**",
        f"- strict zero-shot claim: **{protocol['strict_zero_shot_claim']}**",
        f"- human-designed surface compilers: **{protocol['human_designed_surface_compilers']}**",
        f"- benchmark task-name branches: **{protocol['benchmark_task_name_branches']}**",
        f"- shared runtime: **{protocol['shared_runtime']}**",
        "",
        "## Shared runtime",
        "",
        f"- runtime payload: **{machine['description_bytes']} bytes**",
        f"- runtime operations: **{machine['runtime_operations']}**",
        f"- cross-domain held-out: **{machine['cross_domain_heldout']['correct']}/{machine['cross_domain_heldout']['examples']}**",
        "",
        "## Unseen public accuracy before and after",
        "",
        "| axis | Phase 15b | Phase 15c | answered | wrong |",
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
            "",
            "## Claim boundary",
            "",
            "This is a benchmark-informed surface adaptation with a shared runtime, not",
            "autonomous grammar induction or evidence of a general-purpose reasoning system.",
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
    (output_dir / "phase15c.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "phase15c.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
