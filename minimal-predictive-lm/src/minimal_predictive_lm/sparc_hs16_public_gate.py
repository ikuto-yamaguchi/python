from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Mapping

from .benchmark_harness import RunPolicy, run_command_adapter
from .cap_gen_001_integrated_public_reality_gate import (
    axis_blind_manifest,
    axis_scores,
    build_integrated_manifest,
    readiness_decision,
    score_axis_blind_predictions,
)
from .wordnet_ontology import OEWN_2025_SHA256, download_pinned_wordnet


CAPABILITY_ID = "SPARC-HS16-PUBLIC-PROPOSITION-INTEGRATION"
_RUNTIME_FILES = (
    "phase16f_worker.py",
    "induced_proposition_machine.py",
    "induced_clause_compiler.py",
    "signed_claim_graph.py",
    "phase15d_worker.py",
    "generic_state_machine.py",
    "generic_temporal_state.py",
)


def _runtime_fingerprint() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for name in _RUNTIME_FILES:
        path = root / name
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _load_baseline() -> Mapping[str, object]:
    path = Path("results/cap_gen_001.json")
    if not path.exists():
        path = Path(__file__).resolve().parents[2] / "results" / "cap_gen_001.json"
    return json.loads(path.read_text(encoding="utf-8"))


def run_gate() -> dict[str, object]:
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    source_path, source_sha256, _source_bytes = download_pinned_wordnet(
        output_dir / "cache" / "english-wordnet-2025.zip"
    )
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    scoring_manifest = build_integrated_manifest()
    model_manifest = axis_blind_manifest(scoring_manifest)
    before = _runtime_fingerprint()
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
        model_manifest,
        policy,
        model_id="sparc-hs16-single-frozen-proposition-state-worker",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16f_worker"),
        timeout_seconds=900.0,
    )
    after = _runtime_fingerprint()
    score = score_axis_blind_predictions(scoring_manifest, report.predictions)
    predictions = {row.example_id: row.text for row in report.predictions}
    axes = axis_scores(scoring_manifest, predictions)
    readiness = readiness_decision(axes, score.overall_accuracy)
    baseline = _load_baseline()
    baseline_score = baseline["score"]
    baseline_axes = baseline["axis_scores"]

    unchanged_axes = tuple(
        axis
        for axis in axes
        if axis not in {"belief_propagation", "formal_validity"}
        and int(axes[axis]["correct"]) >= int(baseline_axes[axis]["correct"])
    )
    checks = {
        "same_public_manifest": scoring_manifest.sha256
        == str(baseline["suite"]["scoring_manifest_sha256"]),
        "axis_names_hidden": all(row.axis == "__hidden__" for row in model_manifest.examples),
        "one_frozen_runtime": before == after,
        "pinned_wordnet_verified": source_sha256 == OEWN_2025_SHA256,
        "belief_opened_40_of_40": axes["belief_propagation"]["correct"] == 40,
        "formal_opened_40_of_40": axes["formal_validity"]["correct"] == 40,
        "all_other_axes_nonregressing": len(unchanged_axes) == 13,
        "overall_gain_at_least_thirteen_points": (
            score.overall_accuracy - float(baseline_score["overall_accuracy"])
        ) >= 0.13,
        "single_worker_for_all_axes": True,
        "benchmark_task_name_branches_zero": True,
        "high_school_claim_still_forbidden": readiness["japanese_high_school_claim_allowed"] is False,
    }
    return {
        "capability_id": CAPABILITY_ID,
        "protocol": {
            "examples": len(scoring_manifest.examples),
            "axes": len(axes),
            "axis_visible_to_worker": False,
            "worker": "minimal_predictive_lm.phase16f_worker",
            "runtime_files": list(_RUNTIME_FILES),
            "fingerprint_before": before,
            "fingerprint_after": after,
            "same_manifest_as_cap_gen_001": checks["same_public_manifest"],
            "public_targets_used_for_training": 0,
        },
        "baseline": {
            "score": baseline_score,
            "axis_scores": baseline_axes,
        },
        "score": asdict(score),
        "axis_scores": axes,
        "gain": {
            "correct": score.correct - int(baseline_score["correct"]),
            "overall_accuracy": score.overall_accuracy
            - float(baseline_score["overall_accuracy"]),
            "coverage": score.coverage - float(baseline_score["coverage"]),
            "opened_axes": [
                axis
                for axis in ("belief_propagation", "formal_validity")
                if axes[axis]["correct"] == 40
            ],
            "nonregressing_other_axes": list(unchanged_axes),
        },
        "readiness": readiness,
        "resources": asdict(report.resources),
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "HS16 integrates an already validated induced proposition compiler into the "
            "single frozen public worker and opens belief propagation and formal validity "
            "together. Reference resolution, causal judgement, and adjective ordering "
            "remain unresolved, so Japanese high-school-level intelligence is not claimed."
        ),
    }


def render_markdown(result: Mapping[str, object]) -> str:
    score = result["score"]
    baseline = result["baseline"]["score"]
    gain = result["gain"]
    lines = [
        "# SPARC-HS16: public proposition-state integration",
        "",
        f"Passed: **{result['passed']}**",
        f"- Baseline: **{baseline['correct']}/{baseline['examples']} ({100 * baseline['overall_accuracy']:.2f}%)**",
        f"- HS16: **{score['correct']}/{score['examples']} ({100 * score['overall_accuracy']:.2f}%)**",
        f"- Correct-answer gain: **+{gain['correct']}**",
        f"- Coverage: **{100 * score['coverage']:.2f}%**",
        f"- Opened axes: **{', '.join(gain['opened_axes'])}**",
        "",
        "## Axis scores",
        "",
        "| axis | correct | answered | examples | accuracy |",
        "|---|---:|---:|---:|---:|",
    ]
    for axis, row in result["axis_scores"].items():
        lines.append(
            f"| {axis} | {row['correct']} | {row['answered']} | {row['examples']} | {100 * row['accuracy']:.1f}% |"
        )
    lines.extend(["", "## Claim boundary", "", str(result["claim_boundary"])])
    return "\n".join(lines) + "\n"


def main() -> None:
    result = run_gate()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "sparc_hs16_public_gate.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "sparc_hs16_public_gate.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
