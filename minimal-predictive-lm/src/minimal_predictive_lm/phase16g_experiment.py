from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import random

from .generic_reference_machine import (
    InducedReferenceMachine,
    ReferenceCandidate,
    ReferenceObservation,
    ReferenceSituation,
    induce_reference_machine,
    reference_accuracy,
)


def _candidate(candidate_id: str, *, compatible: bool = True, **signals: int) -> ReferenceCandidate:
    return ReferenceCandidate.build(candidate_id, compatible=compatible, **signals)


def _two(
    left: ReferenceCandidate,
    right: ReferenceCandidate,
) -> ReferenceSituation:
    return ReferenceSituation((left, right))


def calibration_observations() -> tuple[ReferenceObservation, ...]:
    """Structured evidence observations from non-benchmark discourse situations."""

    return (
        ReferenceObservation(_two(_candidate("a"), _candidate("b")), None),
        ReferenceObservation(
            _two(_candidate("a", subject_continuity=1), _candidate("b")),
            "a",
        ),
        ReferenceObservation(
            _two(_candidate("a"), _candidate("b", object_control=1)),
            "b",
        ),
        ReferenceObservation(
            _two(_candidate("a", subject_control=1), _candidate("b")),
            "a",
        ),
        ReferenceObservation(
            _two(_candidate("a"), _candidate("b", possessive_link=1)),
            "b",
        ),
        ReferenceObservation(
            _two(_candidate("a"), _candidate("b", semantic_fit=1)),
            "b",
        ),
        ReferenceObservation(
            _two(_candidate("a", parallel_role=1), _candidate("b")),
            "a",
        ),
        ReferenceObservation(
            _two(_candidate("a"), _candidate("b", recency=1)),
            "b",
        ),
        ReferenceObservation(
            _two(
                _candidate("a", object_control=1),
                _candidate("b", semantic_fit=1),
            ),
            "a",
        ),
        ReferenceObservation(
            _two(
                _candidate("a", subject_control=1),
                _candidate("b", semantic_fit=1),
            ),
            "a",
        ),
        ReferenceObservation(
            _two(
                _candidate("a", semantic_fit=1),
                _candidate("b", recency=1),
            ),
            "a",
        ),
        ReferenceObservation(
            _two(
                _candidate("a", possessive_link=1),
                _candidate("b", recency=1),
            ),
            "a",
        ),
        ReferenceObservation(
            _two(
                _candidate("a", subject_continuity=1),
                _candidate("b", recency=1),
            ),
            "a",
        ),
        ReferenceObservation(
            _two(
                _candidate("a", parallel_role=1),
                _candidate("b", recency=1),
            ),
            "a",
        ),
        ReferenceObservation(
            _two(
                _candidate("a", semantic_fit=1),
                _candidate("b", possessive_link=1),
            ),
            None,
        ),
        ReferenceObservation(
            _two(
                _candidate("a", subject_continuity=1),
                _candidate("b", possessive_link=1),
            ),
            None,
        ),
        ReferenceObservation(
            _two(
                _candidate("a", object_control=1),
                _candidate("b", subject_control=1),
            ),
            None,
        ),
    )


def build_reference_machine() -> InducedReferenceMachine:
    return induce_reference_machine(calibration_observations(), maximum_weight=4)


def heldout_situations() -> tuple[tuple[str, ReferenceSituation, str | None], ...]:
    return (
        (
            "subject_continuity_over_recency",
            _two(
                _candidate("narrator", subject_continuity=1),
                _candidate("visitor", recency=1),
            ),
            "narrator",
        ),
        (
            "object_control_over_semantics",
            _two(
                _candidate("caller", semantic_fit=1),
                _candidate("recipient", object_control=1),
            ),
            "recipient",
        ),
        (
            "subject_control_over_possession",
            _two(
                _candidate("requester", subject_control=1),
                _candidate("owner", possessive_link=1),
            ),
            "requester",
        ),
        (
            "semantic_fit_over_recency",
            _two(
                _candidate("technician", semantic_fit=1),
                _candidate("customer", recency=1),
            ),
            "technician",
        ),
        (
            "possessive_link_over_recency",
            _two(
                _candidate("supervisor", recency=1),
                _candidate("employee", possessive_link=1),
            ),
            "employee",
        ),
        (
            "parallel_role_over_recency",
            _two(
                _candidate("earlier_subject", parallel_role=1),
                _candidate("recent_object", recency=1),
            ),
            "earlier_subject",
        ),
        (
            "neutral_ambiguity",
            _two(_candidate("scientist"), _candidate("artist")),
            None,
        ),
        (
            "hard_agreement_filter",
            _two(
                _candidate("incompatible", compatible=False, object_control=1),
                _candidate("compatible", recency=1),
            ),
            "compatible",
        ),
    )


def _renamed_situation(
    situation: ReferenceSituation,
    expected: str | None,
    *,
    seed: int,
) -> tuple[ReferenceSituation, str | None]:
    rng = random.Random(seed)
    mapping = {
        candidate.candidate_id: f"entity_{seed}_{index}"
        for index, candidate in enumerate(situation.candidates)
    }
    candidates = [
        ReferenceCandidate(
            mapping[candidate.candidate_id],
            candidate.compatible,
            candidate.signals,
        )
        for candidate in situation.candidates
    ]
    rng.shuffle(candidates)
    return ReferenceSituation(tuple(candidates)), None if expected is None else mapping[expected]


def _shift_audit(machine: InducedReferenceMachine) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    cases = heldout_situations()
    for seed in range(200):
        name, situation, expected = cases[seed % len(cases)]
        shifted, shifted_expected = _renamed_situation(
            situation,
            expected,
            seed=seed + 1000,
        )
        prediction = machine.predict(shifted)
        rows.append(
            {
                "seed": seed,
                "case": name,
                "expected": shifted_expected,
                "actual": prediction.output,
                "correct": prediction.output == shifted_expected,
                "operations": prediction.operations,
            }
        )
    return {
        "examples": len(rows),
        "correct": sum(int(row["correct"]) for row in rows),
        "maximum_operations": max(int(row["operations"]) for row in rows),
        "failures": [row for row in rows if not row["correct"]],
    }


def _metamorphic_audit(machine: InducedReferenceMachine) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for name, situation, expected in heldout_situations():
        if expected is None:
            continue
        original = machine.predict(situation)
        augmented = ReferenceSituation(
            situation.candidates
            + (
                _candidate(
                    f"irrelevant_{name}",
                    compatible=False,
                    object_control=1,
                    semantic_fit=1,
                ),
            )
        )
        after = machine.predict(augmented)
        rows.append(
            {
                "case": name,
                "expected": expected,
                "original": original.output,
                "with_incompatible_distractor": after.output,
                "invariant": original.output == after.output == expected,
            }
        )
    return {
        "examples": len(rows),
        "correct": sum(int(row["invariant"]) for row in rows),
        "rows": rows,
    }


def _ablation_audit(machine: InducedReferenceMachine) -> dict[str, object]:
    situation = _two(
        _candidate("controller", object_control=1),
        _candidate("other"),
    )
    resolved = machine.predict(situation)
    ablated = machine.predict(_two(_candidate("controller"), _candidate("other")))
    return {
        "resolved_before_ablation": resolved.output,
        "ambiguous_after_ablation": ablated.output is None and ablated.ambiguous,
        "scores_before": resolved.scores,
        "scores_after": ablated.scores,
    }


def run() -> dict[str, object]:
    calibration = calibration_observations()
    machine = build_reference_machine()
    heldout_rows = tuple(
        ReferenceObservation(situation, expected)
        for _name, situation, expected in heldout_situations()
    )
    shift = _shift_audit(machine)
    metamorphic = _metamorphic_audit(machine)
    ablation = _ablation_audit(machine)
    weights = machine.weight_map()

    return {
        "phase": "16g",
        "protocol": {
            "public_benchmark_examples_used": 0,
            "public_benchmark_targets_used": 0,
            "structured_calibration_observations": len(calibration),
            "structured_heldout_examples": len(heldout_rows),
            "canonical_reference_evidence_supplied": True,
            "natural_language_compiler_present": False,
            "benchmark_task_name_branches": machine.benchmark_task_name_branches,
        },
        "runtime": {
            "name": "induced-evidence-factored-reference-machine",
            "description_bits": machine.description_bits,
            "description_bytes": (machine.description_bits + 7) // 8,
            "weights": weights,
            "candidate_assignments_evaluated": machine.candidate_assignments_evaluated,
            "agreement": "hard compatibility filter",
            "decision": "unique positive maximum else ambiguous",
            "domain_specific_handlers": machine.domain_specific_handlers,
        },
        "calibration": {
            "examples": len(calibration),
            "accuracy": reference_accuracy(machine, calibration),
        },
        "heldout": {
            "examples": len(heldout_rows),
            "accuracy": reference_accuracy(machine, heldout_rows),
            "predictions": [
                {
                    "case": name,
                    "expected": expected,
                    "prediction": asdict(machine.predict(situation)),
                }
                for name, situation, expected in heldout_situations()
            ],
        },
        "renaming_and_candidate_order_shift": shift,
        "metamorphic": metamorphic,
        "ablation": ablation,
        "gates": {
            "calibration_17_of_17": reference_accuracy(machine, calibration) == 1.0,
            "heldout_8_of_8": reference_accuracy(machine, heldout_rows) == 1.0,
            "renaming_and_order_shift_200_of_200": shift["correct"] == shift["examples"],
            "incompatible_distractor_invariance": metamorphic["correct"] == metamorphic["examples"],
            "evidence_ablation_restores_ambiguity": ablation["ambiguous_after_ablation"],
            "structural_control_outweighs_semantics": (
                weights["object_control"] > weights["semantic_fit"]
                and weights["subject_control"] > weights["semantic_fit"]
            ),
            "semantics_outweighs_recency": weights["semantic_fit"] > weights["recency"],
            "public_reference_axis_claim_allowed": False,
            "strict_zero_shot_claim_allowed": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "candidate mentions, agreement compatibility, and evidence signals are supplied as structured inputs",
            "the natural-language compiler that would derive evidence from syntax and semantics is absent",
            "weights are induced inside a bounded nonnegative integer candidate space",
            "semantic compatibility is an input signal rather than grounded from open-domain knowledge",
            "the core returns ambiguity on tied or nonpositive evidence and does not model graded uncertainty",
            "the phase establishes a reference-resolution core but does not improve the public reference score",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    runtime = payload["runtime"]
    heldout = payload["heldout"]
    shifted = payload["renaming_and_candidate_order_shift"]
    metamorphic = payload["metamorphic"]
    lines = [
        "# Phase 16g results: induced evidence-factored reference core",
        "",
        "A bounded MDL-style search induces evidence weights for grammatical control,",
        "discourse continuity, possession, semantic fit, parallel role, and recency.",
        "Agreement is a hard compatibility filter; ties and nonpositive maxima are",
        "reported as ambiguous.",
        "",
        "## Results",
        "",
        f"- runtime payload: **{runtime['description_bytes']} bytes**",
        f"- candidate weight assignments evaluated: **{runtime['candidate_assignments_evaluated']:,}**",
        f"- induced weights: **{runtime['weights']}**",
        f"- calibration: **{payload['calibration']['accuracy'] * payload['calibration']['examples']:.0f}/{payload['calibration']['examples']}**",
        f"- structured held-out: **{heldout['accuracy'] * heldout['examples']:.0f}/{heldout['examples']}**",
        f"- renamed and candidate-order shifted: **{shifted['correct']}/{shifted['examples']}**",
        f"- incompatible distractor invariance: **{metamorphic['correct']}/{metamorphic['examples']}**",
        f"- evidence ablation restores ambiguity: **{payload['ablation']['ambiguous_after_ablation']}**",
        "",
        "## Claim boundary",
        "",
        "This is a structured evidence integrator, not natural-language pronoun",
        "resolution. Public disambiguation remains unopened until mention candidates",
        "and evidence are derived from raw text without task-specific dictionaries.",
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
    (output_dir / "phase16g.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "phase16g.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
