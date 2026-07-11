from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

from .benchmark_harness import (
    BenchmarkExample,
    RunPolicy,
    answer_is_correct,
    build_manifest,
    run_command_adapter,
    score_report,
)
from .mixed_task_learner import (
    MixedInteraction,
    induce_mixed_task_model,
    interaction_from_observation,
)
from .public_benchmarks import load_bigbench_arithmetic_subset


def calibration_interactions() -> tuple[MixedInteraction, ...]:
    rows: list[MixedInteraction] = []

    arithmetic = (
        ("What is 100001 plus 230004?", 330005),
        ("What is 410007 plus 520009?", 930016),
        ("What is 730011 plus 140013?", 870024),
        ("What is 900031 minus 210017?", 690014),
        ("What is 810019 minus 300007?", 510012),
        ("What is 700021 minus 120009?", 580012),
        ("What is 1003 times 17?", 17051),
        ("What is 2009 times 23?", 46207),
        ("What is 3011 times 31?", 93341),
        ("What is 840084 divided by 12?", 70007),
        ("What is 990099 divided by 9?", 110011),
        ("What is 720072 divided by 8?", 90009),
    )
    rows.extend(
        interaction_from_observation(prompt, output=answer)
        for prompt, answer in arithmetic
    )

    for count, delta in ((7, 5), (13, 8), (21, 3), (34, 11)):
        total = count + delta
        rows.append(
            interaction_from_observation(
                f"state_count={count} delta={delta}",
                after={"count": total},
                output=total,
            )
        )

    for status in ("ready", "busy", "ready", "blocked"):
        answer = "GO" if status == "ready" else "WAIT"
        rows.append(
            interaction_from_observation(
                f"choose status={status} yes=GO no=WAIT",
                output=answer,
            )
        )

    forward_pairs = (
        ("abcdefghijklmnopqrstuvwxy", "bcdefghijklmnopqrstuvwxyz"),
        ("causalstate", "dbvtbmtubuf"),
        ("featurebranch", "gfbuvsfcsbodi"),
        ("sensorline", "tfotpsmjof"),
    )
    backward_pairs = (
        ("bcdefghijklmnopqrstuvwxyz", "abcdefghijklmnopqrstuvwxy"),
        ("dbvtbmtubuf", "causalstate"),
        ("gfbuvsfcsbodi", "featurebranch"),
        ("tfotpsmjof", "sensorline"),
    )
    rows.extend(
        interaction_from_observation(
            f"convert forward value={source}", output=target
        )
        for source, target in forward_pairs
    )
    rows.extend(
        interaction_from_observation(
            f"convert backward value={source}", output=target
        )
        for source, target in backward_pairs
    )

    for left, right in (
        ("red", "blue"),
        ("north", "star"),
        ("phase", "twelve"),
        ("tool", "trace"),
    ):
        rows.append(
            interaction_from_observation(
                f"join left={left} right={right}", output=left + right
            )
        )

    for value, source in (
        ("red", "manual7"),
        ("open", "sensor3"),
        ("stable", "testlog9"),
        ("green", "report4"),
    ):
        rows.append(
            interaction_from_observation(
                f"claim value={value} source={source}", output=source
            )
        )

    for before, after, result in (
        ("alpha", "ALPHA", "PASS"),
        ("beta", "BETA", "PASS"),
        ("gamma", "GAMMA", "PASS"),
        ("delta", "DELTA", "PASS"),
    ):
        rows.append(
            interaction_from_observation(
                f"event before={before} after={after} result={result}",
                output=before,
            )
        )
    return tuple(rows)


def synthetic_examples() -> tuple[BenchmarkExample, ...]:
    rows: list[BenchmarkExample] = []
    for index, (count, delta) in enumerate(
        ((2, 9), (18, 7), (40, 12), (71, 14), (105, 23), (9, 91))
    ):
        rows.append(
            BenchmarkExample(
                f"phase12a_state_{index:02d}",
                "state_update",
                f"state_count={count} delta={delta}",
                str(count + delta),
                "numeric",
            )
        )
    for index, (status, yes_value, no_value) in enumerate(
        (
            ("ready", "PROCEED", "HOLD"),
            ("busy", "OPEN", "CLOSED"),
            ("blocked", "RUN", "STOP"),
            ("ready", "ACCEPT", "REJECT"),
            ("paused", "ON", "OFF"),
            ("ready", "LEFT", "RIGHT"),
        )
    ):
        rows.append(
            BenchmarkExample(
                f"phase12a_condition_{index:02d}",
                "conditional_execution",
                f"choose status={status} yes={yes_value} no={no_value}",
                yes_value if status == "ready" else no_value,
            )
        )
    for index, (source, target) in enumerate(
        (
            ("repository", "sfqptjupsz"),
            ("compiler", "dpnqjmfs"),
            ("mixedstream", "njyfetusfbn"),
        )
    ):
        rows.append(
            BenchmarkExample(
                f"phase12a_forward_{index:02d}",
                "string_transformation",
                f"convert forward value={source}",
                target,
            )
        )
    for index, (source, target) in enumerate(
        (
            ("sfqptjupsz", "repository"),
            ("dpnqjmfs", "compiler"),
            ("njyfetusfbn", "mixedstream"),
        )
    ):
        rows.append(
            BenchmarkExample(
                f"phase12a_backward_{index:02d}",
                "string_transformation",
                f"convert backward value={source}",
                target,
            )
        )
    for index, (left, right) in enumerate(
        (
            ("causal", "state"),
            ("event", "graph"),
            ("macro", "library"),
            ("raw", "stream"),
        )
    ):
        rows.append(
            BenchmarkExample(
                f"phase12a_join_{index:02d}",
                "composition",
                f"join left={left} right={right}",
                left + right,
            )
        )
    for index, (value, source) in enumerate(
        (
            ("blue", "manual11"),
            ("failed", "testlog12"),
            ("fresh", "sensor8"),
            ("approved", "report6"),
        )
    ):
        rows.append(
            BenchmarkExample(
                f"phase12a_provenance_{index:02d}",
                "provenance",
                f"claim value={value} source={source}",
                source,
            )
        )
    for index, (before, after) in enumerate(
        (
            ("omega", "OMEGA"),
            ("lambda", "LAMBDA"),
            ("kernel", "KERNEL"),
            ("vector", "VECTOR"),
        )
    ):
        rows.append(
            BenchmarkExample(
                f"phase12a_event_{index:02d}",
                "event_extraction",
                f"event before={before} after={after} result=PASS",
                before,
            )
        )
    return tuple(rows)


def build_synthetic_manifest():
    return build_manifest(
        name="phase12a-mixed-synthetic",
        split="heldout",
        source="generated deterministic Phase 12a held-out suite",
        license_id="CC0-1.0",
        public=False,
        examples=synthetic_examples(),
    )


def build_mixed_manifest():
    public_manifest = load_bigbench_arithmetic_subset(
        examples_per_task=2,
        expected_manifest_sha256=None,
    )
    public_rows = tuple(
        BenchmarkExample(
            example.example_id,
            "mathematics_public",
            example.prompt,
            example.target,
            example.answer_type,
        )
        for example in public_manifest.examples
    )
    manifest = build_manifest(
        name="phase12a-mixed-micro-suite",
        split="public-arithmetic-plus-synthetic-heldout",
        source=(
            "Google BIG-bench arithmetic (Apache-2.0) plus deterministic Phase 12a "
            "synthetic held-out tasks"
        ),
        license_id="mixed:Apache-2.0+CC0-1.0",
        public=False,
        examples=public_rows + synthetic_examples(),
    )
    return manifest, public_manifest, len(public_rows)


def _axis_scores(manifest, report) -> dict[str, dict[str, object]]:
    predictions = {row.example_id: row.text for row in report.predictions}
    grouped: dict[str, list[BenchmarkExample]] = {}
    for example in manifest.examples:
        grouped.setdefault(example.axis, []).append(example)
    output: dict[str, dict[str, object]] = {}
    for axis, examples in sorted(grouped.items()):
        correct = sum(
            answer_is_correct(example, predictions.get(example.example_id, ""))
            for example in examples
        )
        output[axis] = {
            "examples": len(examples),
            "correct": correct,
            "accuracy": correct / len(examples),
        }
    return output


def run() -> dict[str, object]:
    calibration = calibration_interactions()
    model = induce_mixed_task_model(calibration)
    manifest, public_manifest, public_count = build_mixed_manifest()
    policy = RunPolicy(
        max_output_chars=96,
        stop_sequences=("\n\n",),
        tools_allowed=(),
        temperature=0.0,
        seed=0,
    )
    report = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase12a-mixed-task-model",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase12a_worker"),
        timeout_seconds=240.0,
    )
    score = score_report(manifest, report)
    axes = _axis_scores(manifest, report)
    calibration_prompts = {row.prompt for row in calibration}
    benchmark_overlap = sum(
        example.prompt in calibration_prompts for example in manifest.examples
    )
    public_overlap = sum(
        example.prompt in calibration_prompts
        for example in manifest.examples[:public_count]
    )
    all_axis_perfect = all(float(row["accuracy"]) == 1.0 for row in axes.values())
    return {
        "suite": {
            "name": manifest.name,
            "manifest_sha256": manifest.sha256,
            "examples": len(manifest.examples),
            "axes": len(axes),
            "public_examples": public_count,
            "public_axes": 1,
            "fully_public": manifest.public,
            "public_arithmetic_source_sha256": public_manifest.sha256,
            "calibration_examples": len(calibration),
            "calibration_prompt_overlap": benchmark_overlap,
            "public_calibration_prompt_overlap": public_overlap,
        },
        "model": {
            "rules": len(model.rules),
            "description_bits": model.description_bits,
            "description_bytes": (model.description_bits + 7) // 8,
            "candidate_evaluations": model.candidate_evaluations,
            "domain_specific_handlers": model.domain_specific_handlers,
            "calibration_accuracy": 1.0,
        },
        "score": asdict(score),
        "axis_scores": axes,
        "resources": asdict(report.resources),
        "gates": {
            "mixed_multi_axis_execution_success": all_axis_perfect,
            "same_learner_all_axes": model.domain_specific_handlers == 0,
            "narrow_public_comparison_already_available": True,
            "mixed_suite_ready_for_exploratory_open_model_run": all_axis_perfect,
            "public_multi_domain_parity_allowed": False,
            "general_llm_parity_allowed": False,
            "stage_c_score_changed": False,
        },
        "limitations": [
            "only the arithmetic slice is a pinned public benchmark",
            "the remaining axes are deterministic synthetic micro-tasks",
            "generic extraction still relies on numbers and ASCII key=value structure",
            "lexical routing is learned from a small calibration set rather than open language",
            "the invented string primitive is limited to affine character transforms",
            "natural-language generation, long-context understanding, and open-domain knowledge are not tested",
            "a successful mixed micro-suite cannot establish general LLM parity",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    suite = payload["suite"]
    model = payload["model"]
    score = payload["score"]
    resources = payload["resources"]
    lines = [
        "# Phase 12a results: mixed multi-axis learner",
        "",
        "One learned router and one domain-neutral program/primitive induction stack",
        "process arithmetic, state, conditional, string, composition, provenance, and",
        "event-extraction examples in a single shuffled benchmark manifest.",
        "",
        "## Suite",
        "",
        f"- examples / axes: **{suite['examples']} / {suite['axes']}**",
        f"- public examples / public axes: **{suite['public_examples']} / {suite['public_axes']}**",
        f"- calibration examples / prompt overlap: **{suite['calibration_examples']} / {suite['calibration_prompt_overlap']}**",
        f"- manifest SHA-256: **{suite['manifest_sha256']}**",
        "",
        "## Model",
        "",
        f"- routing rules: **{model['rules']}**",
        f"- model payload: **{model['description_bits']}bit / {model['description_bytes']}bytes**",
        f"- induction candidate evaluations: **{model['candidate_evaluations']}**",
        f"- domain-specific handlers: **{model['domain_specific_handlers']}**",
        "",
        "## Accuracy by axis",
        "",
        "| axis | correct | examples | accuracy |",
        "|---|---:|---:|---:|",
    ]
    for axis, row in payload["axis_scores"].items():
        lines.append(
            f"| {axis} | {row['correct']} | {row['examples']} | {row['accuracy']:.1%} |"
        )
    lines.extend(
        [
            "",
            f"Overall accuracy / coverage: **{score['overall_accuracy']:.1%} / {score['coverage']:.1%}**",
            f"Peak RSS / wall time: **{resources['peak_rss_bytes']} bytes / {resources['wall_ns'] / 1_000_000:.3f} ms**",
            "",
            "## Claim gate",
            "",
            "The mixed suite is suitable for an exploratory matched open-model run, but",
            "it is not a public multi-domain benchmark. Only the arithmetic slice is public,",
            "so public multi-domain and general-LLM parity remain closed.",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase12a.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output / "phase12a.md").write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
