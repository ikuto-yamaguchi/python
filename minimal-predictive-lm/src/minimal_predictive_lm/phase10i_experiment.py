from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
from typing import Sequence

from .benchmark_harness import (
    PredictionRecord,
    ResourceUsage,
    RunPolicy,
    RunReport,
    compare_reports,
    model_request,
    score_report,
)
from .public_benchmarks import load_bigbench_arithmetic_subset


SMOLLM2_MODEL_ID = "HuggingFaceTB/SmolLM2-135M-Instruct"


def _run_with_metadata(
    manifest,
    policy: RunPolicy,
    *,
    model_id: str,
    command: Sequence[str],
    timeout_seconds: float,
) -> tuple[RunReport, dict[str, object]]:
    request = model_request(manifest, policy)
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.perf_counter_ns()
    completed = subprocess.run(
        list(command),
        input=json.dumps(request, ensure_ascii=False),
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    wall_ns = time.perf_counter_ns() - started
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    if completed.returncode != 0:
        raise RuntimeError(
            f"model command failed with {completed.returncode}: {completed.stderr[-4000:]}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"model command returned invalid JSON: {completed.stdout[-2000:]}"
        ) from exc

    raw_predictions = payload.get("predictions")
    if not isinstance(raw_predictions, list):
        raise ValueError("model response must contain a predictions list")
    predictions = tuple(
        PredictionRecord(
            str(item["id"]),
            str(item.get("text", ""))[: policy.max_output_chars],
            int(item.get("operations", 0)),
            int(item.get("reads", 0)),
            int(item.get("writes", 0)),
        )
        for item in raw_predictions
    )
    expected_ids = tuple(example.example_id for example in manifest.examples)
    observed_ids = tuple(item.example_id for item in predictions)
    if observed_ids != expected_ids:
        raise ValueError("prediction ids or order differ from the benchmark manifest")

    cpu_seconds = (
        after.ru_utime
        + after.ru_stime
        - before.ru_utime
        - before.ru_stime
    )
    energy = payload.get("energy_joules")
    resources = ResourceUsage(
        model_bytes=int(payload.get("model_bytes", 0)),
        peak_rss_bytes=int(payload.get("peak_rss_bytes", 0)),
        wall_ns=wall_ns,
        cpu_ns=max(0, int(cpu_seconds * 1_000_000_000)),
        operations=sum(item.operations for item in predictions),
        reads=sum(item.reads for item in predictions),
        writes=sum(item.writes for item in predictions),
        energy_joules=None if energy is None else float(energy),
    )
    report = RunReport(
        model_id,
        manifest.name,
        manifest.sha256,
        manifest.public,
        policy,
        predictions,
        resources,
        "fresh_subprocess",
    )
    metadata = payload.get("metadata")
    return report, dict(metadata) if isinstance(metadata, dict) else {}


def run() -> dict[str, object]:
    manifest = load_bigbench_arithmetic_subset(examples_per_task=10)
    policy = RunPolicy(
        max_output_chars=64,
        stop_sequences=("\n\n",),
        tools_allowed=(),
        temperature=0.0,
        seed=0,
    )

    mpm_report, mpm_metadata = _run_with_metadata(
        manifest,
        policy,
        model_id="mpm-phase10h-bigbench-arithmetic",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase10h_worker"),
        timeout_seconds=180.0,
    )
    smol_report, smol_metadata = _run_with_metadata(
        manifest,
        policy,
        model_id=SMOLLM2_MODEL_ID,
        command=(sys.executable, "-m", "minimal_predictive_lm.phase10i_smollm_worker"),
        timeout_seconds=2700.0,
    )

    mpm_score = score_report(manifest, mpm_report)
    smol_score = score_report(manifest, smol_report)
    comparison = compare_reports(manifest, mpm_report, smol_report)

    # This benchmark is intentionally narrow. Even a valid Pareto result here is
    # not evidence of broad language-model parity.
    general_llm_parity_allowed = False

    return {
        "benchmark": {
            "name": manifest.name,
            "split": manifest.split,
            "source": manifest.source,
            "license": manifest.license_id,
            "manifest_sha256": manifest.sha256,
            "examples": len(manifest.examples),
            "public": manifest.public,
        },
        "policy": asdict(policy),
        "mpm": {
            "score": asdict(mpm_score),
            "resources": asdict(mpm_report.resources),
            "metadata": mpm_metadata,
        },
        "smollm2": {
            "model_id": SMOLLM2_MODEL_ID,
            "score": asdict(smol_score),
            "resources": asdict(smol_report.resources),
            "metadata": smol_metadata,
        },
        "matched_comparison": {
            "fairness_violations": list(comparison.fairness_violations),
            "narrow_benchmark_parity_allowed": comparison.parity_claim_allowed,
            "narrow_benchmark_pareto_allowed": comparison.pareto_claim_allowed,
            "strictly_better_resources": list(comparison.strictly_better_resources),
            "general_llm_parity_allowed": general_llm_parity_allowed,
            "accuracy_delta_mpm_minus_smollm2": (
                mpm_score.overall_accuracy - smol_score.overall_accuracy
            ),
            "model_bytes_ratio_smollm2_over_mpm": (
                smol_report.resources.model_bytes / mpm_report.resources.model_bytes
            ),
            "peak_rss_ratio_smollm2_over_mpm": (
                smol_report.resources.peak_rss_bytes
                / mpm_report.resources.peak_rss_bytes
            ),
            "wall_time_ratio_smollm2_over_mpm": (
                smol_report.resources.wall_ns / mpm_report.resources.wall_ns
            ),
        },
        "stage_c": {
            "readiness_points_before": 9,
            "readiness_points_after": 9,
            "mathematics_level": 3,
            "reason": (
                "one narrow direct-arithmetic benchmark cannot establish broad "
                "mathematics or language-model level 4 while GSM8K remains 0%"
            ),
        },
        "limitations": [
            "the comparison covers direct binary arithmetic rather than broad language intelligence",
            "MPM received ten independent operator-grounding interactions; SmolLM2 used its pretrained instruction interface",
            "SmolLM2 runtime parameter bytes are measured after float32 loading, not compressed on-disk checkpoint bytes",
            "MPM model bytes count the induced executable program while peak RSS includes the Python runtime for both systems",
            "operation counts are unavailable for SmolLM2 and are excluded from the Pareto gate",
            "energy is not measured",
            "the 0% GSM8K result remains the relevant evidence for multi-step word-problem reasoning",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    benchmark = payload["benchmark"]
    mpm = payload["mpm"]
    smol = payload["smollm2"]
    comparison = payload["matched_comparison"]
    lines = [
        "# Phase 10i results: matched SmolLM2 comparison",
        "",
        "MPM and SmolLM2-135M-Instruct receive the same pinned public benchmark,",
        "prompt strings, output limit, no-tool policy, deterministic decoding policy,",
        "scorer, and fresh-process resource instrumentation.",
        "",
        "## Benchmark",
        "",
        f"- name / examples: **{benchmark['name']} / {benchmark['examples']}**",
        f"- manifest SHA-256: **{benchmark['manifest_sha256']}**",
        f"- public / license: **{benchmark['public']} / {benchmark['license']}**",
        "",
        "## Results",
        "",
        "| system | accuracy | coverage | model bytes | peak RSS | wall time |",
        "|---|---:|---:|---:|---:|---:|",
        (
            f"| MPM | {mpm['score']['overall_accuracy']:.3%} | "
            f"{mpm['score']['coverage']:.3%} | {mpm['resources']['model_bytes']:,} | "
            f"{mpm['resources']['peak_rss_bytes']:,} | "
            f"{mpm['resources']['wall_ns'] / 1e6:.3f} ms |"
        ),
        (
            f"| SmolLM2-135M-Instruct | {smol['score']['overall_accuracy']:.3%} | "
            f"{smol['score']['coverage']:.3%} | {smol['resources']['model_bytes']:,} | "
            f"{smol['resources']['peak_rss_bytes']:,} | "
            f"{smol['resources']['wall_ns'] / 1e6:.3f} ms |"
        ),
        "",
        "## Fairness and claim gates",
        "",
        f"- fairness violations: **{comparison['fairness_violations']}**",
        f"- narrow benchmark parity allowed: **{comparison['narrow_benchmark_parity_allowed']}**",
        f"- narrow benchmark Pareto allowed: **{comparison['narrow_benchmark_pareto_allowed']}**",
        f"- general LLM parity allowed: **{comparison['general_llm_parity_allowed']}**",
        f"- accuracy delta, MPM − SmolLM2: **{comparison['accuracy_delta_mpm_minus_smollm2']:.3%}**",
        f"- model-byte ratio, SmolLM2 / MPM: **{comparison['model_bytes_ratio_smollm2_over_mpm']:,.2f}x**",
        f"- peak-RSS ratio: **{comparison['peak_rss_ratio_smollm2_over_mpm']:.2f}x**",
        f"- wall-time ratio: **{comparison['wall_time_ratio_smollm2_over_mpm']:.2f}x**",
        "",
        "This result is valid only for the pinned direct-arithmetic subset. The",
        "system remains at 0% on GSM8K, so no broad mathematics or language-model",
        "parity claim is permitted.",
        "",
        "## Model metadata",
        "",
        f"- SmolLM2 metadata: `{json.dumps(smol['metadata'], ensure_ascii=False, sort_keys=True)}`",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase10i.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase10i.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
