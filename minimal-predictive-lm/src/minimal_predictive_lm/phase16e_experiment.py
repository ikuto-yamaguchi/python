from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
import random

from .generic_causal_machine import (
    CausalEvent,
    CausalScenario,
    IntentEvidence,
    NormAwareCausalMachine,
    OutcomeRule,
)


def _base_cases() -> tuple[tuple[str, CausalScenario, bool], ...]:
    conjunctive = (
        CausalEvent("normal_input", True, True),
        CausalEvent("abnormal_input", True, False),
    )
    redundant = (
        CausalEvent("unexpected_extra", True, False),
        CausalEvent("usual_sufficient", True, True),
    )
    contingency = (
        CausalEvent("retained_normal", True, True),
        CausalEvent("abnormal_alternative", True, False),
    )
    threshold = (
        CausalEvent("member_a", True, True),
        CausalEvent("member_b", True, True),
        CausalEvent("member_c", True, False),
    )
    return (
        (
            "normal_conjunct_suppressed",
            CausalScenario(conjunctive, OutcomeRule.all_of("normal_input", "abnormal_input"), "normal_input"),
            False,
        ),
        (
            "abnormal_conjunct_selected",
            CausalScenario(conjunctive, OutcomeRule.all_of("normal_input", "abnormal_input"), "abnormal_input"),
            True,
        ),
        (
            "redundant_abnormal_disjunct",
            CausalScenario(redundant, OutcomeRule.any_of("unexpected_extra", "usual_sufficient"), "unexpected_extra"),
            False,
        ),
        (
            "normality_contingency",
            CausalScenario(contingency, OutcomeRule.any_of("retained_normal", "abnormal_alternative"), "retained_normal"),
            True,
        ),
        (
            "threshold_pivotal",
            CausalScenario(threshold, OutcomeRule(("member_a", "member_b", "member_c"), 3), "member_c"),
            True,
        ),
    )


def _rename_scenario(scenario: CausalScenario, seed: int) -> CausalScenario:
    rng = random.Random(seed)
    names = [event.name for event in scenario.events]
    replacements = {name: f"factor_{seed}_{index}" for index, name in enumerate(names)}
    events = [replace(event, name=replacements[event.name]) for event in scenario.events]
    rng.shuffle(events)
    inputs = [replacements[name] for name in scenario.rule.inputs]
    if seed % 2:
        rng.shuffle(inputs)
    return CausalScenario(
        tuple(events),
        OutcomeRule(tuple(inputs), scenario.rule.threshold),
        replacements[scenario.query],
        scenario.normative_selection,
    )


def _renaming_and_order_audit(machine: NormAwareCausalMachine) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for case_index, (name, scenario, expected) in enumerate(_base_cases()):
        for variant in range(40):
            shifted = _rename_scenario(scenario, seed=case_index * 1000 + variant)
            prediction = machine.judge_cause(shifted)
            rows.append(
                {
                    "case": name,
                    "variant": variant,
                    "expected": expected,
                    "actual": prediction.output,
                    "classification": prediction.classification,
                    "correct": prediction.output is expected,
                    "operations": prediction.operations,
                }
            )
    return {
        "examples": len(rows),
        "correct": sum(int(row["correct"]) for row in rows),
        "maximum_operations": max(int(row["operations"]) for row in rows),
        "failures": [row for row in rows if not row["correct"]],
    }


def _intent_audit(machine: NormAwareCausalMachine) -> dict[str, object]:
    cases = (
        (
            "direct_goal",
            IntentEvidence(True, controlled_action=True, expected_path=True, goal=True),
            True,
        ),
        (
            "foreseen_side_effect",
            IntentEvidence(True, controlled_action=True, expected_path=True, foresaw_side_effect=True),
            True,
        ),
        (
            "lucky_goal",
            IntentEvidence(True, controlled_action=True, expected_path=False, goal=True),
            False,
        ),
        (
            "unforeseen_effect",
            IntentEvidence(True, controlled_action=True, expected_path=True),
            False,
        ),
        (
            "uncontrolled_action",
            IntentEvidence(True, controlled_action=False, expected_path=True, goal=True),
            False,
        ),
        (
            "outcome_absent",
            IntentEvidence(False, controlled_action=True, expected_path=True, goal=True),
            False,
        ),
    )
    rows = []
    for name, evidence, expected in cases:
        prediction = machine.judge_intent(evidence)
        rows.append(
            {
                "case": name,
                "evidence": asdict(evidence),
                "expected": expected,
                "actual": prediction.output,
                "classification": prediction.classification,
                "correct": prediction.output is expected,
            }
        )
    return {
        "examples": len(rows),
        "correct": sum(int(row["correct"]) for row in rows),
        "rows": rows,
    }


def _metamorphic_audit(machine: NormAwareCausalMachine) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for case_name, scenario, expected in _base_cases():
        original = machine.judge_cause(scenario)
        with_irrelevant = CausalScenario(
            scenario.events + (CausalEvent("irrelevant", False, False),),
            scenario.rule,
            scenario.query,
            scenario.normative_selection,
        )
        augmented = machine.judge_cause(with_irrelevant)
        rows.append(
            {
                "case": case_name,
                "expected": expected,
                "original": original.output,
                "with_irrelevant": augmented.output,
                "invariant": original.output == augmented.output == expected,
            }
        )
    return {
        "examples": len(rows),
        "correct": sum(int(row["invariant"]) for row in rows),
        "rows": rows,
    }


def run() -> dict[str, object]:
    machine = NormAwareCausalMachine()
    shifted = _renaming_and_order_audit(machine)
    intent = _intent_audit(machine)
    metamorphic = _metamorphic_audit(machine)
    return {
        "phase": "16e",
        "runtime": {
            "name": "norm-aware-threshold-causal-machine",
            "description_bits": machine.description_bits,
            "description_bytes": (machine.description_bits + 7) // 8,
            "mechanisms": [
                "threshold structural equations",
                "direct intervention",
                "normality-improving contingency search",
                "abnormal conjunct responsibility selection",
                "goal and foreseen-side-effect intent",
                "accidental realization rejection",
            ],
        },
        "protocol": {
            "public_benchmark_examples_used": 0,
            "public_benchmark_targets_used": 0,
            "generated_structured_scenarios": shifted["examples"],
            "rename_and_event_order_shift": True,
            "irrelevant_variable_metamorphism": True,
        },
        "renaming_and_order_shift": shifted,
        "intent": intent,
        "metamorphic": metamorphic,
        "gates": {
            "structured_shift_200_of_200": shifted["correct"] == shifted["examples"],
            "intent_6_of_6": intent["correct"] == intent["examples"],
            "irrelevant_variable_invariance": metamorphic["correct"] == metamorphic["examples"],
            "public_causal_axis_claim_allowed": False,
            "strict_zero_shot_claim_allowed": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "the causal core receives structured variables, normal values, and an outcome equation",
            "natural-language extraction is not implemented in this phase",
            "the current outcome language is a single threshold equation rather than an arbitrary causal DAG",
            "normality declarations are supplied rather than autonomously learned from culture or context",
            "proximate causation, omissions with duties, and multi-stage preemption require a richer graph",
            "the phase creates a causal foundation but does not improve the public causal score yet",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    runtime = payload["runtime"]
    shifted = payload["renaming_and_order_shift"]
    intent = payload["intent"]
    metamorphic = payload["metamorphic"]
    lines = [
        "# Phase 16e results: norm-aware causal core",
        "",
        "This phase introduces a structured causal adjudicator before attempting",
        "natural-language compilation. No public benchmark examples or targets are used.",
        "",
        "## Results",
        "",
        f"- runtime payload: **{runtime['description_bytes']} bytes**",
        f"- renamed and reordered causal scenarios: **{shifted['correct']}/{shifted['examples']}**",
        f"- intentionality cases: **{intent['correct']}/{intent['examples']}**",
        f"- irrelevant-variable invariance: **{metamorphic['correct']}/{metamorphic['examples']}**",
        f"- maximum causal operations: **{shifted['maximum_operations']}**",
        "",
        "## Claim boundary",
        "",
        "The measured claim is limited to the structured threshold-causal fragment.",
        "Public natural-language causal judgement remains unopened because this phase",
        "does not yet infer events, norms, equations, duties, or temporal paths from prose.",
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
    (output_dir / "phase16e.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "phase16e.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
