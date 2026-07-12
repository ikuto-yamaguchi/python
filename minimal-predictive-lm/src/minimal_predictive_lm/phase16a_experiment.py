from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys

from .benchmark_harness import ABSTAIN_TOKEN, RunPolicy, answer_is_correct, run_command_adapter, score_report
from .generic_state_machine import GenericStateMachine
from .generic_temporal_state import GenericTemporalMachine
from .mixed_task_learner import induce_mixed_task_model
from .phase12a_experiment import calibration_interactions
from .phase13a_experiment import build_phase13a_manifest
from .phase13d_experiment import build_public_quantifier
from .phase14b_experiment import build_phase14b_graph
from .phase15a_experiment import axis_scores
from .phase15a_public_benchmarks import load_phase15a_public_transfer_suite
from .phase15b_experiment import build_guarded_algebra_model
from .phase16a_public_benchmarks import PHASE16A_TASKS, load_phase16a_public_transfer_suite
from .wordnet_ontology import OEWN_2025_SHA256, download_pinned_wordnet


def frozen_phase15d_fingerprint() -> str:
    phase12 = induce_mixed_task_model(calibration_interactions())
    algebra = build_guarded_algebra_model()
    state_machine = GenericStateMachine()
    temporal_machine = GenericTemporalMachine()
    quantifier = build_public_quantifier()
    graph = build_phase14b_graph()
    payload = {
        "phase12": phase12.render(),
        "algebra": algebra.render(),
        "state_machine": state_machine.render(),
        "temporal_machine": temporal_machine.render(),
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
        "causal_judgement": "counterfactual causation, norm sensitivity, intention, and preemption",
        "reference_resolution": "syntactic roles, discourse salience, lexical selectional preferences, and ambiguity calibration",
        "formal_validity": "quantified proposition normalization and proof or countermodel search",
        "adjective_order": "latent semantic adjective classes and language-specific ordering constraints",
        "belief_propagation": "speaker truth-state propagation through quoted positive and negative claims",
    }


def run() -> dict[str, object]:
    output_dir = Path("results")
    wordnet_path = output_dir / "cache" / "english-wordnet-2025.zip"
    source_path, source_sha256, _source_bytes = download_pinned_wordnet(wordnet_path)
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    manifest = load_phase16a_public_transfer_suite(examples_per_task=40)
    original, _source_hashes = build_phase13a_manifest()
    second = load_phase15a_public_transfer_suite(examples_per_task=40)
    prior_prompts = {row.prompt for row in original.examples}
    prior_prompts.update(row.prompt for row in second.examples)
    exact_prior_prompt_overlap = sum(row.prompt in prior_prompts for row in manifest.examples)

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
        model_id="mpm-phase15d-frozen-before-phase16-adaptation",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase15d_worker"),
        timeout_seconds=300.0,
    )
    fingerprint_after = frozen_phase15d_fingerprint()
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
            "tasks": list(PHASE16A_TASKS),
            "task_blob_sha1": {
                task: config["blob_sha1"] for task, config in PHASE16A_TASKS.items()
            },
            "examples_per_axis": {
                axis: int(row["examples"]) for axis, row in axes.items()
            },
            "exact_prompt_overlap_with_first_two_public_slices": exact_prior_prompt_overlap,
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
            "surface_compilers_added": 0,
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
                and exact_prior_prompt_overlap == 0
            ),
            "benchmark_specialization_used": False,
            "new_surface_compiler_used": False,
            "third_slice_capability_claim_allowed": False,
            "runtime_pareto_allowed": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "the third slice is still a five-task benchmark sample rather than a complete measure of intelligence",
            "only the first forty examples of each public task are used",
            "the frozen system already contains benchmark-informed compilers from Phase 15, although none target these five tasks",
            "WordNet and fixed provenance documents remain available to the frozen worker",
            "no matched open-model comparison is included",
            "a low score identifies missing mechanisms but does not select the correct architecture by itself",
            "free-form dialogue, real-repository coding, long context, multimodal perception, and autonomous parser induction remain untested",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    model = payload["frozen_model"]
    score = payload["score"]
    lines = [
        "# Phase 16a results: frozen third public capability slice",
        "",
        "The complete Phase 15d system is frozen before five further public tasks are",
        "evaluated. No benchmark example, target, document, primitive, handler, or surface",
        "compiler is added.",
        "",
        "## Anti-specialization checks",
        "",
        f"- public examples / axes: **{payload['suite']['examples']} / {payload['suite']['axes']}**",
        f"- model fingerprint unchanged: **{model['unchanged']}**",
        f"- exact overlap with the first two public slices: **{payload['suite']['exact_prompt_overlap_with_first_two_public_slices']}**",
        f"- benchmark training examples / targets: **{payload['suite']['benchmark_examples_used_for_training']} / {payload['suite']['benchmark_targets_used_for_training']}**",
        f"- new handlers / primitives / documents / compilers: **{model['benchmark_specific_handlers_added']} / {model['benchmark_specific_primitives_added']} / {model['benchmark_specific_documents_added']} / {model['surface_compilers_added']}**",
        "",
        "## Frozen public accuracy",
        "",
        "| axis | correct | answered | wrong | abstained | examples | accuracy |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for axis, row in payload["axis_scores"].items():
        lines.append(
            f"| {axis.replace('_', ' ')} | {row['correct']} | {row['answered']} | {row['wrong']} | {row['abstained']} | {row['examples']} | {100 * row['accuracy']:.1f}% |"
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
            "This is a frozen failure boundary. No result here authorizes adaptation",
            "claims, open-model parity, runtime Pareto, or general-LLM parity.",
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
    (output_dir / "phase16a.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "phase16a.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
