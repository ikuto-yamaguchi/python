from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

from .benchmark_harness import RunPolicy, run_command_adapter, score_report
from .corrected_proposition_machine import CorrectedPropositionMachine
from .induced_proposition_machine import (
    InducedPropositionMachine,
    independent_clause_observations,
)
from .phase13a_experiment import build_phase13a_manifest
from .phase15a_experiment import axis_scores
from .phase15a_public_benchmarks import load_phase15a_public_transfer_suite
from .phase16a_public_benchmarks import load_phase16a_public_transfer_suite
from .phase16d_experiment import build_chain_prompt
from .wordnet_ontology import download_pinned_wordnet


def _distribution_shift_audit(machine: InducedPropositionMachine) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for seed in range(100):
        claim_count = 1 + (seed * 29) % 96
        order = ("forward", "reverse", "shuffled")[seed % 3]
        prompt, expected = build_chain_prompt(claim_count, seed=seed + 301, order=order)
        prediction = machine.predict(prompt)
        rows.append(
            {
                "seed": seed,
                "claims": claim_count,
                "order": order,
                "expected": expected,
                "actual": prediction.output,
                "correct": prediction.output == expected,
                "operations": prediction.operations,
            }
        )
    return {
        "examples": len(rows),
        "correct": sum(int(row["correct"]) for row in rows),
        "maximum_claims": max(int(row["claims"]) for row in rows),
        "maximum_operations": max(int(row["operations"]) for row in rows),
        "failures": [row for row in rows if not row["correct"]],
    }


def _abstention_audit(machine: InducedPropositionMachine) -> dict[str, object]:
    cases = {
        "unknown_clause_order": (
            "Question: BaseA is reliable. According to BaseA, JudgeB is reliable. "
            "Does JudgeB tell the truth?"
        ),
        "unknown_truth_phrase": (
            "Question: BaseA is trustworthy. JudgeB says BaseA is reliable. "
            "Does JudgeB tell the truth?"
        ),
        "contradiction": (
            "Question: BaseA is reliable. JudgeB says BaseA is reliable. "
            "JudgeB reports BaseA is unreliable. Does JudgeB tell the truth?"
        ),
        "unanchored_cycle": (
            "Question: AnchorA is reliable. NodeB says NodeC is reliable. "
            "NodeC claims NodeB is reliable. Does NodeB tell the truth?"
        ),
    }
    predictions = {name: machine.predict(prompt).output for name, prompt in cases.items()}
    return {
        "predictions": predictions,
        "all_abstained": all(output is None for output in predictions.values()),
    }


def run() -> dict[str, object]:
    output_dir = Path("results")
    source_path, source_sha256, _source_bytes = download_pinned_wordnet(
        output_dir / "cache" / "english-wordnet-2025.zip"
    )
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    third = load_phase16a_public_transfer_suite(examples_per_task=40)
    original, _source_hashes = build_phase13a_manifest()
    second = load_phase15a_public_transfer_suite(examples_per_task=40)
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

    manual = run_command_adapter(
        third,
        policy,
        model_id="mpm-phase16c-manual-claim-compiler",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16c_worker"),
        timeout_seconds=300.0,
    )
    induced = run_command_adapter(
        third,
        policy,
        model_id="mpm-phase16f-induced-claim-compiler",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16f_worker"),
        timeout_seconds=300.0,
    )
    original_induced = run_command_adapter(
        original,
        policy,
        model_id="mpm-phase16f-original-regression",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16f_worker"),
        timeout_seconds=300.0,
    )
    second_induced = run_command_adapter(
        second,
        policy,
        model_id="mpm-phase16f-second-regression",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase16f_worker"),
        timeout_seconds=300.0,
    )

    manual_score = score_report(third, manual)
    induced_score = score_report(third, induced)
    original_score = score_report(original, original_induced)
    second_score = score_report(second, second_induced)
    manual_predictions = {row.example_id: row.text for row in manual.predictions}
    induced_predictions = {row.example_id: row.text for row in induced.predictions}
    manual_axes = axis_scores(third, manual_predictions)
    induced_axes = axis_scores(third, induced_predictions)
    exact_prediction_equivalence = sum(
        manual_predictions[row.example_id] == induced_predictions[row.example_id]
        for row in third.examples
    )

    manual_machine = CorrectedPropositionMachine()
    machine = InducedPropositionMachine()
    shifted = _distribution_shift_audit(machine)
    abstention = _abstention_audit(machine)
    compiler = machine.induced_clause_compiler

    return {
        "phase": "16f",
        "induction_protocol": {
            "public_benchmark_format_inspected": True,
            "public_benchmark_examples_used_as_template_observations": 0,
            "public_benchmark_targets_used": 0,
            "canonical_clause_observations": len(independent_clause_observations()),
            "canonical_event_supervision": True,
            "strict_zero_shot_claim_allowed": False,
            "autonomous_parser_induction_claim_allowed": False,
            "benchmark_task_name_branches": compiler.benchmark_task_name_branches,
        },
        "compiler": {
            "templates": len(compiler.templates),
            "template_rendering": [template.render() for template in compiler.templates],
            "description_bits": compiler.description_bits,
            "description_bytes": (compiler.description_bits + 7) // 8,
            "truth_phrase_groundings": len(compiler.truth_phrases),
            "attribution_phrase_groundings": len(compiler.attribution_phrases),
            "manual_claim_surface_compilers_before": 1,
            "manual_claim_surface_compilers_after": 0,
            "induced_claim_surface_compilers_after": 1,
            "manual_proposition_description_bytes": (
                manual_machine.description_bits + 7
            )
            // 8,
            "induced_proposition_description_bytes": (
                machine.description_bits + 7
            )
            // 8,
        },
        "suite": {
            "name": third.name,
            "manifest_sha256": third.sha256,
            "examples": len(third.examples),
            "axes": len(induced_axes),
            "wordnet_sha256": source_sha256,
        },
        "manual": {
            "score": asdict(manual_score),
            "axis_scores": manual_axes,
            "resources": asdict(manual.resources),
        },
        "induced": {
            "score": asdict(induced_score),
            "axis_scores": induced_axes,
            "resources": asdict(induced.resources),
        },
        "equivalence": {
            "exact_public_predictions": exact_prediction_equivalence,
            "public_examples": len(third.examples),
            "belief_40_of_40_retained": induced_axes["belief_propagation"]["correct"] == 40,
            "formal_40_of_40_retained": induced_axes["formal_validity"]["correct"] == 40,
        },
        "distribution_shift": shifted,
        "abstention": abstention,
        "regressions": {
            "original_public": {
                "manifest_sha256": original.sha256,
                "score": asdict(original_score),
                "resources": asdict(original_induced.resources),
            },
            "second_public": {
                "manifest_sha256": second.sha256,
                "score": asdict(second_score),
                "resources": asdict(second_induced.resources),
            },
        },
        "gates": {
            "three_templates_induced": len(compiler.templates) == 3,
            "public_prediction_equivalence_200_of_200": (
                exact_prediction_equivalence == len(third.examples)
            ),
            "belief_40_of_40_retained": induced_axes["belief_propagation"]["correct"] == 40,
            "formal_40_of_40_retained": induced_axes["formal_validity"]["correct"] == 40,
            "random_shift_100_of_100": shifted["correct"] == shifted["examples"],
            "unknown_and_conflicting_forms_abstain": abstention["all_abstained"],
            "all_answered_predictions_correct": induced_score.answered == induced_score.correct,
            "original_public_200_of_200_retained": original_score.correct == 200,
            "second_public_raw_198_of_200_retained": second_score.correct == 198,
            "benchmark_task_name_specialization_used": False,
            "autonomous_parser_induction_allowed": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "canonical clause events and argument roles are supervised rather than discovered from consequences alone",
            "truth and attribution phrase meanings remain independently supervised groundings",
            "the template-induction algorithm and token classes are human-designed",
            "templates require exact token-class order and abstain on syntactic alternations",
            "the controlled formal-logic surface compiler remains human-designed",
            "this phase preserves an existing public capability rather than opening a new axis",
            "reference resolution, adjective ordering, and natural-language causal judgement remain unsolved",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    protocol = payload["induction_protocol"]
    compiler = payload["compiler"]
    manual = payload["manual"]
    induced = payload["induced"]
    shifted = payload["distribution_shift"]
    regressions = payload["regressions"]
    lines = [
        "# Phase 16f results: supervised clause-template induction",
        "",
        "Seven independent raw-clause plus canonical-event observations induce three",
        "token-class templates for base claims, attributed claims, and queries. The",
        "hand-written claim regex is removed from the evaluated path; the same queue",
        "runtime and controlled formal-logic compiler are retained.",
        "",
        "## Disclosure",
        "",
        f"- public format inspected: **{protocol['public_benchmark_format_inspected']}**",
        f"- public examples / targets used as template observations: **{protocol['public_benchmark_examples_used_as_template_observations']} / {protocol['public_benchmark_targets_used']}**",
        f"- canonical event supervision: **{protocol['canonical_event_supervision']}**",
        f"- strict zero-shot / autonomous parser claim: **{protocol['strict_zero_shot_claim_allowed']} / {protocol['autonomous_parser_induction_claim_allowed']}**",
        "",
        "## Compiler",
        "",
        f"- observations / induced templates: **{protocol['canonical_clause_observations']} / {compiler['templates']}**",
        f"- compiler payload: **{compiler['description_bytes']} bytes**",
        f"- manual claim compilers: **{compiler['manual_claim_surface_compilers_before']} → {compiler['manual_claim_surface_compilers_after']}**",
        f"- induced claim compilers: **{compiler['induced_claim_surface_compilers_after']}**",
        "",
        "## Public equivalence",
        "",
        f"- exact predictions: **{payload['equivalence']['exact_public_predictions']}/{payload['equivalence']['public_examples']}**",
        f"- manual correct/answered: **{manual['score']['correct']}/{manual['score']['answered']}**",
        f"- induced correct/answered: **{induced['score']['correct']}/{induced['score']['answered']}**",
        f"- belief / formal retained: **{induced['axis_scores']['belief_propagation']['correct']}/40 / {induced['axis_scores']['formal_validity']['correct']}/40**",
        "",
        "## Shift and regressions",
        "",
        f"- random generated chains: **{shifted['correct']}/{shifted['examples']}**",
        f"- unknown/conflicting forms all abstained: **{payload['abstention']['all_abstained']}**",
        f"- original public: **{regressions['original_public']['score']['correct']}/{regressions['original_public']['score']['examples']}**",
        f"- second public raw: **{regressions['second_public']['score']['correct']}/{regressions['second_public']['score']['examples']}**",
        "",
        "## Claim boundary",
        "",
        "This removes one hand-written claim surface compiler from the evaluated path.",
        "It is supervised template induction, not autonomous language acquisition, broad",
        "syntax understanding, or general-LLM parity.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "phase16f.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "phase16f.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
