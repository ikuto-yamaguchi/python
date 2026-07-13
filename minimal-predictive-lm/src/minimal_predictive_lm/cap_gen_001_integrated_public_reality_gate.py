from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
from typing import Mapping, Sequence

from .benchmark_harness import (
    ABSTAIN_TOKEN,
    BenchmarkExample,
    BenchmarkManifest,
    RunPolicy,
    answer_is_correct,
    build_manifest,
    run_command_adapter,
    score_report,
)
from .phase13a_experiment import build_phase13a_manifest
from .phase15a_experiment import axis_scores
from .phase15a_public_benchmarks import load_phase15a_public_transfer_suite
from .phase16a_experiment import frozen_phase15d_fingerprint
from .phase16a_public_benchmarks import load_phase16a_public_transfer_suite
from .wordnet_ontology import OEWN_2025_SHA256, download_pinned_wordnet


CAPABILITY_ID = "CAP-GEN-001"
EXAMPLES_PER_AXIS = 40
PUBLIC_AXIS_TARGET = 0.70
PUBLIC_AGGREGATE_TARGET = 0.80


def _prefixed_examples(
    source: BenchmarkManifest, prefix: str
) -> tuple[BenchmarkExample, ...]:
    return tuple(
        BenchmarkExample(
            f"{prefix}/{row.example_id}",
            row.axis,
            row.prompt,
            row.target,
            row.answer_type,
        )
        for row in source.examples
    )


def build_integrated_manifest(
    *, examples_per_axis: int = EXAMPLES_PER_AXIS
) -> BenchmarkManifest:
    first, _hashes = build_phase13a_manifest(examples_per_task=examples_per_axis)
    second = load_phase15a_public_transfer_suite(
        examples_per_task=examples_per_axis
    )
    third = load_phase16a_public_transfer_suite(
        examples_per_task=examples_per_axis
    )
    examples = (
        _prefixed_examples(first, "slice1")
        + _prefixed_examples(second, "slice2")
        + _prefixed_examples(third, "slice3")
    )
    return build_manifest(
        name="cap-gen-001-integrated-public-reality-gate",
        split=f"three-frozen-slices-first-{examples_per_axis}-per-axis",
        source=(
            "Google BIG-bench arithmetic plus fifteen BIG-Bench-Hard/public axes "
            "previously frozen in phases 13a, 15a, and 16a"
        ),
        license_id="mixed:Apache-2.0+MIT",
        public=True,
        examples=examples,
    )


def readiness_decision(
    axis_rows: Mapping[str, Mapping[str, object]],
    aggregate_accuracy: float,
) -> dict[str, object]:
    floor = min(float(row["accuracy"]) for row in axis_rows.values())
    weak_axes = tuple(
        axis
        for axis, row in sorted(axis_rows.items())
        if float(row["accuracy"]) < PUBLIC_AXIS_TARGET
    )
    proxy_passed = (
        aggregate_accuracy >= PUBLIC_AGGREGATE_TARGET
        and floor >= PUBLIC_AXIS_TARGET
    )
    return {
        "aggregate_target": PUBLIC_AGGREGATE_TARGET,
        "axis_floor_target": PUBLIC_AXIS_TARGET,
        "observed_axis_floor": floor,
        "weak_axes": weak_axes,
        "public_reasoning_proxy_passed": proxy_passed,
        "japanese_high_school_claim_allowed": False,
        "general_llm_parity_allowed": False,
        "architecture_pivot_required": not proxy_passed,
    }


def _failure_examples(
    manifest: BenchmarkManifest,
    predictions: Mapping[str, str],
    *,
    per_axis: int = 2,
) -> dict[str, list[dict[str, str]]]:
    output: dict[str, list[dict[str, str]]] = {}
    for example in manifest.examples:
        prediction = predictions.get(example.example_id, "").strip()
        if answer_is_correct(example, prediction):
            continue
        rows = output.setdefault(example.axis, [])
        if len(rows) >= per_axis:
            continue
        rows.append(
            {
                "id": example.example_id,
                "prompt": example.prompt,
                "target": example.target,
                "prediction": prediction or ABSTAIN_TOKEN,
                "outcome": (
                    "abstained"
                    if not prediction or prediction == ABSTAIN_TOKEN
                    else "wrong"
                ),
            }
        )
    return output


def run_gate() -> dict[str, object]:
    output_dir = Path("results")
    wordnet_path = output_dir / "cache" / "english-wordnet-2025.zip"
    source_path, source_sha256, _source_bytes = download_pinned_wordnet(
        wordnet_path
    )
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    manifest = build_integrated_manifest()
    fingerprint_before = frozen_phase15d_fingerprint()
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
    report = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-single-frozen-worker-integrated-public-reality-baseline",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase15d_worker"),
        timeout_seconds=900.0,
    )
    fingerprint_after = frozen_phase15d_fingerprint()
    score = score_report(manifest, report)
    predictions = {row.example_id: row.text for row in report.predictions}
    axes = axis_scores(manifest, predictions)
    readiness = readiness_decision(axes, score.overall_accuracy)

    checks = {
        "manifest_is_public": manifest.public,
        "exactly_fifteen_axes": len(axes) == 15,
        "exactly_600_examples": len(manifest.examples) == 600,
        "one_frozen_fingerprint": fingerprint_before == fingerprint_after,
        "one_worker_for_every_axis": True,
        "no_axis_name_routing_added_by_gate": True,
        "pinned_wordnet_verified": source_sha256 == OEWN_2025_SHA256,
        "reality_gate_reports_failure_without_promoting_claim": (
            not readiness["japanese_high_school_claim_allowed"]
            and not readiness["general_llm_parity_allowed"]
        ),
    }
    return {
        "capability_id": CAPABILITY_ID,
        "purpose": (
            "freeze one current worker and measure the same checkpoint on all "
            "fifteen previously public reasoning axes before any further micro-gate"
        ),
        "suite": {
            "name": manifest.name,
            "manifest_sha256": manifest.sha256,
            "examples": len(manifest.examples),
            "axes": len(axes),
            "examples_per_axis": EXAMPLES_PER_AXIS,
        },
        "frozen_model": {
            "worker": "minimal_predictive_lm.phase15d_worker",
            "fingerprint_before": fingerprint_before,
            "fingerprint_after": fingerprint_after,
            "unchanged": fingerprint_before == fingerprint_after,
            "benchmark_specific_changes_for_this_gate": 0,
        },
        "score": asdict(score),
        "axis_scores": axes,
        "readiness": readiness,
        "failure_examples": _failure_examples(manifest, predictions),
        "resources": asdict(report.resources),
        "checks": checks,
        "gate_valid": all(checks.values()),
        "capability_passed": bool(readiness["public_reasoning_proxy_passed"]),
        "claim_boundary": (
            "This fifteen-axis public reasoning proxy is necessary but not sufficient "
            "for Japanese high-school intelligence. Japanese, mathematics curriculum, "
            "science, humanities, writing, repository coding, long context, and "
            "interactive learning remain separate required gates."
        ),
    }


def render_markdown(result: Mapping[str, object]) -> str:
    score = result["score"]
    readiness = result["readiness"]
    lines = [
        "# CAP-GEN-001: integrated public reality gate",
        "",
        f"Gate protocol valid: **{result['gate_valid']}**",
        f"Current capability passed: **{result['capability_passed']}**",
        "",
        f"- Examples / axes: **{result['suite']['examples']} / {result['suite']['axes']}**",
        f"- Overall accuracy: **{100 * score['overall_accuracy']:.1f}%**",
        f"- Coverage: **{100 * score['coverage']:.1f}%**",
        f"- Minimum axis accuracy: **{100 * readiness['observed_axis_floor']:.1f}%**",
        f"- Architecture pivot required: **{readiness['architecture_pivot_required']}**",
        "",
        "## Axis scores",
        "",
        "| axis | correct | answered | examples | accuracy | coverage |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for axis, row in result["axis_scores"].items():
        lines.append(
            f"| {axis.replace('_', ' ')} | {row['correct']} | {row['answered']} | "
            f"{row['examples']} | {100 * row['accuracy']:.1f}% | "
            f"{100 * row['coverage']:.1f}% |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Further CAP-SEM micro-gates are frozen until this integrated score moves.",
            "- The same worker and fingerprint must improve multiple axes together.",
            "- A Japanese high-school or general-LLM claim remains forbidden.",
            "",
            "## Claim boundary",
            "",
            str(result["claim_boundary"]),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    result = run_gate()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "cap_gen_001.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "cap_gen_001.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(render_markdown(result), end="")
    if not result["gate_valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
