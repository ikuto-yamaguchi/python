from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

from .benchmark_harness import RunPolicy, run_command_adapter, score_report
from .public_benchmarks import load_bigbench_arithmetic_subset


def run() -> dict[str, object]:
    manifest = load_bigbench_arithmetic_subset(examples_per_task=10)
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
        model_id="mpm-phase10h-bigbench-arithmetic",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase10h_worker"),
        timeout_seconds=180.0,
    )
    score = score_report(manifest, report)
    return {
        "benchmark": {
            "name": manifest.name,
            "split": manifest.split,
            "source": manifest.source,
            "license": manifest.license_id,
            "manifest_sha256": manifest.sha256,
            "examples": len(manifest.examples),
            "subtasks": 20,
            "examples_per_subtask": 10,
            "public": manifest.public,
        },
        "calibration": {
            "examples": 10,
            "operators": ["plus", "minus", "times", "divided by", "percent of"],
            "benchmark_examples_used": 0,
        },
        "mpm": {
            "score": asdict(score),
            "resources": asdict(report.resources),
            "policy": asdict(report.policy),
            "execution_mode": report.execution_mode,
        },
        "comparison": {
            "matched_open_model_executed": False,
            "parity_claim_allowed": False,
            "pareto_claim_allowed": False,
            "reason": "the public MPM run is complete but the matched open-model subprocess has not yet been executed",
        },
        "stage_c": {
            "readiness_points_before": 9,
            "readiness_points_after": 9,
            "mathematics_level": 3,
        },
        "limitations": [
            "the subset is the first ten examples from each of twenty public arithmetic subtasks",
            "the English operator grounding uses ten independent calibration interactions",
            "the benchmark measures direct binary arithmetic rather than natural-language word-problem reasoning",
            "no matched open model has been executed yet",
            "energy is not measured",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    benchmark = payload["benchmark"]
    calibration = payload["calibration"]
    mpm = payload["mpm"]
    score = mpm["score"]
    resources = mpm["resources"]
    comparison = payload["comparison"]
    lines = [
        "# Phase 10h results: public BIG-bench arithmetic baseline",
        "",
        "Twenty public BIG-bench arithmetic subtasks are sampled deterministically",
        "with ten examples per subtask. English operator words are grounded from ten",
        "separate interactions that do not reuse benchmark examples.",
        "",
        "## Benchmark",
        "",
        f"- examples / subtasks: **{benchmark['examples']} / {benchmark['subtasks']}**",
        f"- examples per subtask: **{benchmark['examples_per_subtask']}**",
        f"- public / license: **{benchmark['public']} / {benchmark['license']}**",
        f"- manifest SHA-256: **{benchmark['manifest_sha256']}**",
        "",
        "## Calibration",
        "",
        f"- independent interactions: **{calibration['examples']}**",
        f"- benchmark examples used: **{calibration['benchmark_examples_used']}**",
        "",
        "## MPM result",
        "",
        f"- correct / answered / total: **{score['correct']} / {score['answered']} / {score['examples']}**",
        f"- overall accuracy: **{score['overall_accuracy']:.3%}**",
        f"- coverage: **{score['coverage']:.3%}**",
        f"- model program bytes: **{resources['model_bytes']:,}**",
        f"- peak RSS: **{resources['peak_rss_bytes']:,} bytes**",
        f"- wall time: **{resources['wall_ns'] / 1e6:.3f} ms**",
        f"- feature reads / operations: **{resources['reads']:,} / {resources['operations']:,}**",
        "",
        "## Comparison status",
        "",
        f"- matched open model executed: **{comparison['matched_open_model_executed']}**",
        f"- parity claim allowed: **{comparison['parity_claim_allowed']}**",
        "",
        "This isolates the narrow public domain in which a compiled concept program",
        "may be competitive. It does not repair the 0% GSM8K result.",
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
    (output / "phase10h.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase10h.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
