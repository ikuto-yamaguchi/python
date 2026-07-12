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
    answer_is_correct,
    compare_reports,
    model_request,
    score_report,
)
from .phase12a_experiment import (
    _axis_scores,
    build_mixed_manifest,
    calibration_interactions,
)


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
    payload = json.loads(completed.stdout)
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
    if tuple(item.example_id for item in predictions) != expected_ids:
        raise ValueError("prediction ids or order differ from benchmark manifest")
    cpu_seconds = (
        after.ru_utime
        + after.ru_stime
        - before.ru_utime
        - before.ru_stime
    )
    resources = ResourceUsage(
        model_bytes=int(payload.get("model_bytes", 0)),
        peak_rss_bytes=int(payload.get("peak_rss_bytes", 0)),
        wall_ns=wall_ns,
        cpu_ns=max(0, int(cpu_seconds * 1_000_000_000)),
        operations=sum(item.operations for item in predictions),
        reads=sum(item.reads for item in predictions),
        writes=sum(item.writes for item in predictions),
        energy_joules=None,
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


def _axis_delta(candidate_axes, baseline_axes) -> dict[str, dict[str, float]]:
    return {
        axis: {
            "mpm_accuracy": float(candidate_axes[axis]["accuracy"]),
            "smollm2_accuracy": float(baseline_axes[axis]["accuracy"]),
            "delta": float(candidate_axes[axis]["accuracy"])
            - float(baseline_axes[axis]["accuracy"]),
        }
        for axis in sorted(candidate_axes)
    }


def run() -> dict[str, object]:
    manifest, public_manifest, public_count = build_mixed_manifest()
    policy = RunPolicy(
        max_output_chars=96,
        stop_sequences=("\n\n",),
        tools_allowed=(),
        temperature=0.0,
        seed=0,
    )
    mpm_report, mpm_metadata = _run_with_metadata(
        manifest,
        policy,
        model_id="mpm-phase12a-mixed-task-model",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase12a_worker"),
        timeout_seconds=300.0,
    )
    smol_report, smol_metadata = _run_with_metadata(
        manifest,
        policy,
        model_id=SMOLLM2_MODEL_ID,
        command=(sys.executable, "-m", "minimal_predictive_lm.phase12b_smollm_worker"),
        timeout_seconds=2700.0,
    )
    mpm_score = score_report(manifest, mpm_report)
    smol_score = score_report(manifest, smol_report)
    mpm_axes = _axis_scores(manifest, mpm_report)
    smol_axes = _axis_scores(manifest, smol_report)
    base = compare_reports(manifest, mpm_report, smol_report)

    # The suite is intentionally non-public, and MPM receives structured state
    # transition evidence for four calibration examples while SmolLM2 sees the
    # same prompt-output demonstrations. Therefore this run is exploratory only.
    fairness_violations = sorted(
        set(base.fairness_violations)
        | {
            "mixed_suite_not_fully_public",
            "calibration_observability_mismatch_on_state_transition",
        }
    )
    runtime_ratios = {
        "model_bytes_smollm2_over_mpm": (
            smol_report.resources.model_bytes / mpm_report.resources.model_bytes
        ),
        "peak_rss_smollm2_over_mpm": (
            smol_report.resources.peak_rss_bytes
            / mpm_report.resources.peak_rss_bytes
        ),
        "wall_time_smollm2_over_mpm": (
            smol_report.resources.wall_ns / mpm_report.resources.wall_ns
        ),
    }
    return {
        "suite": {
            "name": manifest.name,
            "manifest_sha256": manifest.sha256,
            "examples": len(manifest.examples),
            "axes": len(mpm_axes),
            "public_examples": public_count,
            "public_axes": 1,
            "fully_public": manifest.public,
            "public_arithmetic_source_sha256": public_manifest.sha256,
        },
        "calibration": {
            "examples": len(calibration_interactions()),
            "prompt_output_examples_matched": int(
                smol_metadata.get("same_prompt_output_calibration_examples", 0)
            )
            == len(calibration_interactions()),
            "mpm_structured_state_evidence": True,
            "smollm2_structured_state_evidence": bool(
                smol_metadata.get("state_transition_evidence_visible", False)
            ),
        },
        "mpm": {
            "score": asdict(mpm_score),
            "axis_scores": mpm_axes,
            "resources": asdict(mpm_report.resources),
            "metadata": mpm_metadata,
        },
        "smollm2": {
            "score": asdict(smol_score),
            "axis_scores": smol_axes,
            "resources": asdict(smol_report.resources),
            "metadata": smol_metadata,
        },
        "exploratory_comparison": {
            "axis_deltas": _axis_delta(mpm_axes, smol_axes),
            "overall_accuracy_delta_mpm_minus_smollm2": (
                mpm_score.overall_accuracy - smol_score.overall_accuracy
            ),
            "runtime_ratios": runtime_ratios,
            "fairness_violations": fairness_violations,
            "exploratory_result_available": True,
            "strict_parity_claim_allowed": False,
            "runtime_pareto_claim_allowed": False,
            "public_multi_domain_parity_allowed": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "six of seven axes are deterministic synthetic micro-tasks",
            "MPM sees structured state-transition evidence for state calibration while SmolLM2 sees prompt-output demonstrations",
            "SmolLM2 rereads all forty demonstrations for every query while MPM compiles them once",
            "shared-prefix KV-cache reuse is not implemented for the SmolLM2 reference runner",
            "model parameter bytes are measured after float32 loading",
            "training, induction, and pretraining costs are not in one lifetime ledger",
            "energy is not measured",
            "the run cannot authorize public multi-domain or general LLM parity",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    suite = payload["suite"]
    mpm = payload["mpm"]
    smol = payload["smollm2"]
    comparison = payload["exploratory_comparison"]
    lines = [
        "# Phase 12b results: exploratory mixed-suite SmolLM2 comparison",
        "",
        "The same 70 prompts, output policy, scorer, and forty prompt-output",
        "demonstrations are used for MPM and SmolLM2-135M-Instruct. The result is",
        "exploratory because the suite is not fully public and state calibration",
        "observability is not structurally identical.",
        "",
        "## Overall",
        "",
        "| system | accuracy | coverage | model bytes | peak RSS | wall time |",
        "|---|---:|---:|---:|---:|---:|",
        (
            f"| MPM | {mpm['score']['overall_accuracy']:.1%} | "
            f"{mpm['score']['coverage']:.1%} | {mpm['resources']['model_bytes']} | "
            f"{mpm['resources']['peak_rss_bytes']} | "
            f"{mpm['resources']['wall_ns'] / 1_000_000:.3f} ms |"
        ),
        (
            f"| SmolLM2 | {smol['score']['overall_accuracy']:.1%} | "
            f"{smol['score']['coverage']:.1%} | {smol['resources']['model_bytes']} | "
            f"{smol['resources']['peak_rss_bytes']} | "
            f"{smol['resources']['wall_ns'] / 1_000_000:.3f} ms |"
        ),
        "",
        "## Accuracy by axis",
        "",
        "| axis | MPM | SmolLM2 | delta |",
        "|---|---:|---:|---:|",
    ]
    for axis, row in comparison["axis_deltas"].items():
        lines.append(
            f"| {axis} | {row['mpm_accuracy']:.1%} | "
            f"{row['smollm2_accuracy']:.1%} | {row['delta']:+.1%} |"
        )
    lines.extend(
        [
            "",
            "## Claim gate",
            "",
            f"- fairness violations: **{comparison['fairness_violations']}**",
            "- strict parity claim allowed: **False**",
            "- runtime Pareto claim allowed: **False**",
            "- public multi-domain parity allowed: **False**",
            "- general LLM parity allowed: **False**",
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
    (output / "phase12b.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output / "phase12b.md").write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
