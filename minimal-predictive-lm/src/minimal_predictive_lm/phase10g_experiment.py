from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

from .benchmark_harness import RunPolicy, run_command_adapter, score_report
from .public_benchmarks import (
    GSM8K_TEST_GIT_BLOB_SHA1,
    GSM8K_TEST_URL,
    load_gsm8k_test,
)


def run() -> dict[str, object]:
    manifest = load_gsm8k_test()
    policy = RunPolicy(
        max_output_chars=128,
        stop_sequences=("\n\n",),
        tools_allowed=(),
        temperature=0.0,
        seed=0,
    )
    report = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase10g-gsm8k",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase10f_worker"),
        timeout_seconds=180.0,
    )
    score = score_report(manifest, report)
    return {
        "benchmark": {
            "name": manifest.name,
            "split": manifest.split,
            "source": GSM8K_TEST_URL,
            "source_git_blob_sha1": GSM8K_TEST_GIT_BLOB_SHA1,
            "manifest_sha256": manifest.sha256,
            "license": manifest.license_id,
            "examples": len(manifest.examples),
            "public": manifest.public,
        },
        "mpm": {
            "score": asdict(score),
            "resources": asdict(report.resources),
            "policy": asdict(report.policy),
            "execution_mode": report.execution_mode,
        },
        "stage_c": {
            "readiness_points_before": 8,
            "readiness_points_after": 9,
            "mathematics_level_before": 2,
            "mathematics_level_after": 3,
            "matched_open_model_executed": False,
            "parity_claim_allowed": False,
            "pareto_claim_allowed": False,
            "reason": (
                "a public raw-input benchmark was executed with resource measurement, "
                "but no matched open-model baseline has been run"
            ),
        },
        "limitations": [
            "the current MPM math system only induces five one-step binary arithmetic programs",
            "GSM8K requires multi-step linguistic and arithmetic reasoning",
            "the system is evaluated zero-shot without benchmark-specific training",
            "no calculator or external tool is allowed in this run",
            "energy is not measured",
            "public evidence maturity increases even if task accuracy is low; this is not a capability claim",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    benchmark = payload["benchmark"]
    mpm = payload["mpm"]
    score = mpm["score"]
    resources = mpm["resources"]
    stage = payload["stage_c"]
    lines = [
        "# Phase 10g results: public GSM8K baseline",
        "",
        "The official GSM8K test split is downloaded from the OpenAI repository,",
        "verified against a pinned Git blob SHA, and passed to the model without",
        "targets or benchmark-specific tools.",
        "",
        "## Benchmark",
        "",
        f"- examples: **{benchmark['examples']:,}**",
        f"- public: **{benchmark['public']}**",
        f"- license: **{benchmark['license']}**",
        f"- source Git blob: **{benchmark['source_git_blob_sha1']}**",
        f"- manifest SHA-256: **{benchmark['manifest_sha256']}**",
        "",
        "## MPM result",
        "",
        f"- correct / answered / total: **{score['correct']} / {score['answered']} / {score['examples']}**",
        f"- overall accuracy: **{score['overall_accuracy']:.3%}**",
        f"- selective accuracy: **{score['selective_accuracy']:.3%}**",
        f"- coverage: **{score['coverage']:.3%}**",
        f"- model program bytes: **{resources['model_bytes']:,}**",
        f"- peak RSS: **{resources['peak_rss_bytes']:,} bytes**",
        f"- wall time: **{resources['wall_ns'] / 1e6:.3f} ms**",
        f"- CPU time: **{resources['cpu_ns'] / 1e6:.3f} ms**",
        f"- feature reads / operations: **{resources['reads']:,} / {resources['operations']:,}**",
        "",
        "## Stage-C evidence",
        "",
        f"- readiness points: **{stage['readiness_points_before']} → {stage['readiness_points_after']} / 24**",
        f"- mathematics level: **{stage['mathematics_level_before']} → {stage['mathematics_level_after']}**",
        f"- matched open model executed: **{stage['matched_open_model_executed']}**",
        f"- parity claim allowed: **{stage['parity_claim_allowed']}**",
        "",
        "Level 3 records public evidence maturity, not high performance. A poor",
        "score is retained as the baseline that the next multi-step representation",
        "must improve.",
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
    (output / "phase10g.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase10g.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
