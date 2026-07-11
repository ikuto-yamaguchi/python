from __future__ import annotations

from dataclasses import asdict, replace
from fractions import Fraction
import json
from pathlib import Path
import sys

from .benchmark_harness import (
    BenchmarkExample,
    RunPolicy,
    build_manifest,
    compare_reports,
    model_request,
    run_command_adapter,
    score_report,
)
from .phase10b_experiment import NEAR_HELDOUT, SHIFTED


def _target_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def smoke_manifest():
    traces = tuple(NEAR_HELDOUT) + tuple(SHIFTED)
    return build_manifest(
        name="phase10f-math-smoke",
        split="heldout",
        source="generated://phase10f-smoke",
        license_id="internal-synthetic",
        public=False,
        examples=(
            BenchmarkExample(
                f"math_{index:03d}",
                "mathematics",
                trace.raw,
                _target_text(trace.answer),
                "numeric",
            )
            for index, trace in enumerate(traces)
        ),
    )


def run() -> dict[str, object]:
    manifest = smoke_manifest()
    policy = RunPolicy(
        max_output_chars=64,
        stop_sequences=("\n\n",),
        tools_allowed=(),
        temperature=0.0,
        seed=0,
    )
    report = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase10f-math",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase10f_worker"),
    )
    score = score_report(manifest, report)

    request = model_request(manifest, policy)
    target_leakage = any("target" in item for item in request["examples"])

    non_public_gate = compare_reports(manifest, report, report)
    mismatched_baseline = replace(
        report,
        model_id="unexecuted-open-model-placeholder",
        policy=replace(policy, max_output_chars=65),
    )
    mismatch_gate = compare_reports(manifest, report, mismatched_baseline)

    return {
        "harness": {
            "manifest_name": manifest.name,
            "manifest_sha256": manifest.sha256,
            "examples": len(manifest.examples),
            "model_request_contains_targets": target_leakage,
            "fresh_subprocess": report.execution_mode == "fresh_subprocess",
            "instrumentation_version": report.instrumentation_version,
        },
        "mpm_smoke": {
            "score": asdict(score),
            "resources": asdict(report.resources),
        },
        "anti_overclaim": {
            "non_public_fairness_violations": list(non_public_gate.fairness_violations),
            "non_public_parity_allowed": non_public_gate.parity_claim_allowed,
            "non_public_pareto_allowed": non_public_gate.pareto_claim_allowed,
            "policy_mismatch_violations": list(mismatch_gate.fairness_violations),
            "policy_mismatch_parity_allowed": mismatch_gate.parity_claim_allowed,
        },
        "comparison_readiness": {
            "harness_schema_complete": True,
            "target_free_model_request": not target_leakage,
            "fresh_process_resource_measurement": True,
            "matched_policy_gate": True,
            "public_benchmark_executed": False,
            "open_model_executed": False,
            "first_narrow_comparison_ready": False,
            "stage_c_points_before": 8,
            "stage_c_points_after": 8,
            "remaining_mandatory_evidence_runs": 2,
        },
        "limitations": [
            "the smoke benchmark is synthetic and is used only to validate the harness",
            "no open model is downloaded or executed in Phase 10f",
            "peak RSS includes the Python runtime and imported modules",
            "operation and read counters are model-specific and are not yet cross-model comparable",
            "energy is absent unless an external runner supplies a measured value",
            "a public benchmark and a matched open-model run are still required before comparison claims",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    harness = payload["harness"]
    smoke = payload["mpm_smoke"]
    score = smoke["score"]
    resources = smoke["resources"]
    guard = payload["anti_overclaim"]
    readiness = payload["comparison_readiness"]
    lines = [
        "# Phase 10f results: matched benchmark and resource harness",
        "",
        "The harness sends prompts without targets to fresh model subprocesses,",
        "checks benchmark checksums and run-policy equality, and records quality and",
        "resource usage before allowing any parity or Pareto claim.",
        "",
        "## Harness smoke run",
        "",
        f"- examples: **{harness['examples']}**",
        f"- target leakage: **{harness['model_request_contains_targets']}**",
        f"- fresh subprocess: **{harness['fresh_subprocess']}**",
        f"- overall accuracy: **{score['overall_accuracy']:.1%}**",
        f"- coverage: **{score['coverage']:.1%}**",
        f"- model program bytes: **{resources['model_bytes']:,}**",
        f"- peak RSS bytes: **{resources['peak_rss_bytes']:,}**",
        f"- wall time: **{resources['wall_ns'] / 1e6:.3f} ms**",
        f"- CPU time: **{resources['cpu_ns'] / 1e6:.3f} ms**",
        f"- feature reads / operations: **{resources['reads']:,} / {resources['operations']:,}**",
        "",
        "## Anti-overclaim gates",
        "",
        f"- non-public violations: **{', '.join(guard['non_public_fairness_violations'])}**",
        f"- non-public parity allowed: **{guard['non_public_parity_allowed']}**",
        f"- policy mismatch violations: **{', '.join(guard['policy_mismatch_violations'])}**",
        f"- policy-mismatched parity allowed: **{guard['policy_mismatch_parity_allowed']}**",
        "",
        "## Comparison readiness",
        "",
        f"- public benchmark executed: **{readiness['public_benchmark_executed']}**",
        f"- matched open model executed: **{readiness['open_model_executed']}**",
        f"- first narrow comparison ready: **{readiness['first_narrow_comparison_ready']}**",
        f"- Stage-C score: **{readiness['stage_c_points_before']} → {readiness['stage_c_points_after']} / 24**",
        f"- mandatory evidence runs remaining: **{readiness['remaining_mandatory_evidence_runs']}**",
        "",
        "The infrastructure gate is complete, but no public comparison evidence is",
        "claimed from the synthetic smoke run.",
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
    (output / "phase10f.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase10f.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
