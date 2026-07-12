from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys

from .benchmark_harness import ABSTAIN_TOKEN, RunPolicy, answer_is_correct, run_command_adapter, score_report
from .mixed_task_learner import induce_mixed_task_model
from .phase12a_experiment import calibration_interactions
from .phase13b_experiment import build_algebra_model
from .phase13c_experiment import build_scope_corrected_algebra_model
from .phase13d_experiment import build_public_quantifier
from .phase14b_experiment import build_phase14b_graph
from .phase15a_public_benchmarks import PHASE15A_TASKS, load_phase15a_public_transfer_suite
from .wordnet_ontology import OEWN_2025_SHA256, download_pinned_wordnet


def frozen_model_fingerprint() -> str:
    phase12 = induce_mixed_task_model(calibration_interactions())
    algebra = build_scope_corrected_algebra_model()
    quantifier = build_public_quantifier()
    graph = build_phase14b_graph()
    payload = {
        "phase12": phase12.render(),
        "algebra": algebra.render(),
        "quantifier": quantifier.render(),
        "document_graph": graph.render(),
        "wordnet_sha256": OEWN_2025_SHA256,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def axis_scores(manifest, predictions: dict[str, str]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[object]] = {}
    for example in manifest.examples:
        grouped.setdefault(example.axis, []).append(example)
    output: dict[str, dict[str, object]] = {}
    for axis, rows in sorted(grouped.items()):
        answered = sum(
            bool(predictions.get(row.example_id, "").strip())
            and predictions.get(row.example_id, "").strip() != ABSTAIN_TOKEN
            for row in rows
        )
        correct = sum(
            answer_is_correct(row, predictions.get(row.example_id, "")) for row in rows
        )
        output[axis] = {
            "examples": len(rows),
            "answered": answered,
            "correct": correct,
            "wrong": answered - correct,
            "abstained": len(rows) - answered,
            "accuracy": correct / len(rows),
            "coverage": answered / len(rows),
            "selective_accuracy": correct / answered if answered else 0.0,
        }
    return output


def failure_examples(manifest, predictions: dict[str, str], *, per_axis: int = 3) -> dict[str, list[dict[str, str]]]:
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


def capability_gap_inventory() -> dict[str, str]:
    return {
        "date_understanding": "temporal reference grounding, calendar arithmetic, and option selection",
        "logical_ordering": "relation normalization, transitive order closure, and ordinal query resolution",
        "state_permutation_tracking": "mutable bijection state and sequential swap execution",
        "spatial_navigation": "heading-aware vector state and rotation composition",
        "stack_completion": "typed pushdown stack state and reverse closing emission",
    }


def run() -> dict[str, object]:
    output_dir = Path("results")
    wordnet_path = output_dir / "cache" / "english-wordnet-2025.zip"
    source_path, source_sha256, _source_bytes = download_pinned_wordnet(wordnet_path)
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    manifest = load_phase15a_public_transfer_suite(examples_per_task=40)
    fingerprint_before = frozen_model_fingerprint()
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
        model_id="mpm-phase14b-frozen-before-phase15-adaptation",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase14b_worker"),
        timeout_seconds=300.0,
    )
    fingerprint_after = frozen_model_fingerprint()
    score = score_report(manifest, report)
    predictions = {row.example_id: row.text for row in report.predictions}
    axes = axis_scores(manifest, predictions)

    return {
        "suite": {
            "name": manifest.name,
            "manifest_sha256": manifest.sha256,
            "source": manifest.source,
            "license_id": manifest.license_id,
            "public": manifest.public,
            "examples": len(manifest.examples),
            "axes": len(axes),
            "tasks": list(PHASE15A_TASKS),
            "task_blob_sha1": {
                task: config["blob_sha1"] for task, config in PHASE15A_TASKS.items()
            },
            "examples_per_axis": {
                axis: int(row["examples"]) for axis, row in axes.items()
            },
            "benchmark_examples_used_for_training": 0,
            "benchmark_targets_used_for_training": 0,
        },
        "frozen_model": {
            "fingerprint_before": fingerprint_before,
            "fingerprint_after": fingerprint_after,
            "unchanged": fingerprint_before == fingerprint_after,
            "wordnet_sha256": source_sha256,
            "benchmark_specific_handlers_added": 0,
            "benchmark_specific_primitives_added": 0,
            "benchmark_specific_documents_added": 0,
            "benchmark_examples_used_for_calibration": 0,
        },
        "score": asdict(score),
        "axis_scores": axes,
        "failure_examples": failure_examples(manifest, predictions),
        "capability_gap_inventory": capability_gap_inventory(),
        "resources": asdict(report.resources),
        "gates": {
            "frozen_public_baseline_valid": (
                manifest.public
                and fingerprint_before == fingerprint_after
                and source_sha256 == OEWN_2025_SHA256
            ),
            "benchmark_specialization_used": False,
            "phase14b_public_score_changed": False,
            "new_public_capability_parity_allowed": False,
            "runtime_pareto_allowed": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "the five new axes are another benchmark slice rather than a complete measure of general intelligence",
            "the frozen worker still receives structured benchmark records although it ignores axis names in execution",
            "only the first forty examples of each public task are used",
            "no matched open-model comparison is included",
            "low accuracy identifies missing mechanisms but does not by itself prove which representation is optimal",
            "free-form dialogue, coding, long context, multimodal perception, and autonomous evidence search remain untested",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    model = payload["frozen_model"]
    score = payload["score"]
    lines = [
        "# Phase 15a results: frozen unseen public capability baseline",
        "",
        "The Phase 14b system is frozen before five previously unused public tasks are",
        "evaluated. No benchmark example, target, document, handler, or primitive is added.",
        "",
        "## Anti-specialization checks",
        "",
        f"- public examples / axes: **{payload['suite']['examples']} / {payload['suite']['axes']}**",
        f"- model fingerprint unchanged: **{model['unchanged']}**",
        f"- benchmark training examples / targets: **{payload['suite']['benchmark_examples_used_for_training']} / {payload['suite']['benchmark_targets_used_for_training']}**",
        f"- benchmark handlers / primitives / documents added: **{model['benchmark_specific_handlers_added']} / {model['benchmark_specific_primitives_added']} / {model['benchmark_specific_documents_added']}**",
        "",
        "## Frozen public accuracy",
        "",
        "| axis | correct | answered | abstained | examples | accuracy |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for axis, row in payload["axis_scores"].items():
        lines.append(
            f"| {axis.replace('_', ' ')} | {row['correct']} | {row['answered']} | {row['abstained']} | {row['examples']} | {100 * row['accuracy']:.1f}% |"
        )
    lines.extend(
        [
            "",
            f"Overall accuracy / coverage: **{100 * score['overall_accuracy']:.1f}% / {100 * score['coverage']:.1f}%**",
            f"Answered/correct: **{score['answered']} / {score['correct']}**",
            "",
            "## Capability gaps",
            "",
        ]
    )
    for axis, description in payload["capability_gap_inventory"].items():
        lines.append(f"- **{axis}**: {description}")
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "This is a frozen failure boundary. It does not authorize adaptation claims,",
            "open-model parity, runtime Pareto, or general-LLM parity.",
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
    (output_dir / "phase15a.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "phase15a.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
