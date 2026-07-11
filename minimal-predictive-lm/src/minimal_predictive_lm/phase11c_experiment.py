from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from .primitive_invention import (
    InventedStringProgram,
    StringTransformExample,
    decide_primitive_adoption,
    evaluate_primitive_proposals,
    primitive_accuracy,
    select_reusable_primitive,
)
from .universal_program_induction import (
    TransitionTrace,
    UnexpressibleTaskError,
    induce_program,
)


def _training_examples() -> tuple[StringTransformExample, ...]:
    return (
        StringTransformExample(
            "inventory_labels",
            "sphinx of black quartz judge my vow",
            "SPHINX OF BLACK QUARTZ JUDGE MY VOW",
        ),
        StringTransformExample(
            "inventory_labels",
            "the five boxing wizards jump quickly",
            "THE FIVE BOXING WIZARDS JUMP QUICKLY",
        ),
        StringTransformExample(
            "tool_commands",
            "pack my box with five dozen liquor jugs",
            "PACK MY BOX WITH FIVE DOZEN LIQUOR JUGS",
        ),
        StringTransformExample(
            "tool_commands",
            "how vexingly quick daft zebras jump",
            "HOW VEXINGLY QUICK DAFT ZEBRAS JUMP",
        ),
    )


def _validation_examples() -> tuple[StringTransformExample, ...]:
    return (
        StringTransformExample("inventory_labels", "phase eleven status 17", "PHASE ELEVEN STATUS 17"),
        StringTransformExample("tool_commands", "run test then report", "RUN TEST THEN REPORT"),
        StringTransformExample("dialogue_output", "open file-z please", "OPEN FILE-Z PLEASE"),
        StringTransformExample("dialogue_output", "warning code 42", "WARNING CODE 42"),
    )


def _novel_domain_examples() -> tuple[StringTransformExample, ...]:
    return (
        StringTransformExample("repository_symbols", "feature branch", "FEATURE BRANCH"),
        StringTransformExample("repository_symbols", "commit id 7f", "COMMIT ID 7F"),
        StringTransformExample("sensor_labels", "motor line-3", "MOTOR LINE-3"),
        StringTransformExample("sensor_labels", "repair queue", "REPAIR QUEUE"),
    )


def _unicode_shift_examples() -> tuple[StringTransformExample, ...]:
    return (
        StringTransformExample("unicode", "café déjà vu", "CAFÉ DÉJÀ VU"),
        StringTransformExample("unicode", "straße", "STRASSE"),
    )


def _fixed_grammar_failure(examples: tuple[StringTransformExample, ...]) -> tuple[bool, str]:
    traces = tuple(
        TransitionTrace.build((example.source,), {}, {}, example.target)
        for example in examples
    )
    try:
        induce_program(traces, max_depth=3, max_candidates=50_000)
    except UnexpressibleTaskError as exc:
        return True, str(exc)
    return False, "fixed grammar unexpectedly expressed the transformation"


def run() -> dict[str, object]:
    training = _training_examples()
    validation = _validation_examples()
    novel = _novel_domain_examples()
    unicode_shift = _unicode_shift_examples()

    fixed_failure, fixed_failure_message = _fixed_grammar_failure(training)
    proposals = evaluate_primitive_proposals(training, validation)
    selected = select_reusable_primitive(training, validation, minimum_validation_families=3)
    program = InventedStringProgram(selected.primitive)

    long_horizon = decide_primitive_adoption(
        selected,
        validation,
        expected_future_calls=100,
        baseline_error_rate=1.0,
        error_cost_bits=64,
        migration_bits=128,
    )
    one_call = decide_primitive_adoption(
        selected,
        validation,
        expected_future_calls=1,
        baseline_error_rate=1.0,
        error_cost_bits=64,
        migration_bits=128,
    )

    proposal_rows = [
        {
            "kind": proposal.primitive.kind,
            "description_bits": proposal.primitive.description_bits,
            "training_accuracy": proposal.training_accuracy,
            "validation_accuracy": proposal.validation_accuracy,
            "render": proposal.primitive.render(),
        }
        for proposal in proposals
    ]

    return {
        "fixed_grammar": {
            "unexpressible_detected": fixed_failure,
            "message": fixed_failure_message,
        },
        "proposal_generation": {
            "proposal_count": len(proposals),
            "proposals": proposal_rows,
            "task_specific_uppercase_candidate_supplied": False,
            "candidate_families": [
                "whole-string lookup",
                "aligned character map",
                "conditional codepoint offset",
            ],
        },
        "selected_primitive": {
            "kind": selected.primitive.kind,
            "render": selected.primitive.render(),
            "description_bits": selected.primitive.description_bits,
            "training_accuracy": selected.training_accuracy,
            "validation_accuracy": selected.validation_accuracy,
            "validation_families": list(selected.validation_families),
            "program_bits": program.description_bits,
            "novel_domain_accuracy": primitive_accuracy(selected.primitive, novel),
            "unicode_shift_accuracy": primitive_accuracy(selected.primitive, unicode_shift),
        },
        "lifetime_adoption": {
            "one_call": asdict(one_call),
            "one_hundred_calls": asdict(long_horizon),
        },
        "verdict": {
            "phase11c_success": (
                fixed_failure
                and selected.validation_accuracy == 1.0
                and primitive_accuracy(selected.primitive, novel) == 1.0
                and long_horizon.adopted
                and not one_call.adopted
            ),
            "new_engine_code_for_each_application_domain": 0,
            "representation_invention_is_open_ended": False,
            "stage_c_score_changed": False,
        },
        "limitations": [
            "the proposal language is a fixed meta-grammar rather than an unrestricted primitive generator",
            "training strings collectively expose the complete ASCII lowercase interval",
            "the learned codepoint offset does not handle accented letters or one-to-many Unicode case mappings",
            "task boundaries and aligned input/output demonstrations are supplied",
            "cross-family validation is small and synthetic",
            "the normalized lifetime objective uses an explicit experimental error price rather than measured physical energy",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    fixed = payload["fixed_grammar"]
    selected = payload["selected_primitive"]
    adoption = payload["lifetime_adoption"]
    proposals = payload["proposal_generation"]["proposals"]
    lines = [
        "# Phase 11c results: residual-driven primitive invention",
        "",
        "The fixed Phase 11a grammar cannot express the string transformation.  Candidate",
        "representations are proposed from aligned residuals and selected by cross-family",
        "validation plus a normalized lifetime objective.",
        "",
        "## Fixed grammar boundary",
        "",
        f"- unexpressible detected: **{fixed['unexpressible_detected']}**",
        "",
        "## Candidate proposals",
        "",
        "| kind | bits | train | cross-family validation |",
        "|---|---:|---:|---:|",
    ]
    for row in proposals:
        lines.append(
            f"| {row['kind']} | {row['description_bits']:,} | "
            f"{row['training_accuracy']:.1%} | {row['validation_accuracy']:.1%} |"
        )
    lines.extend(
        [
            "",
            "## Selected primitive",
            "",
            f"- kind: **{selected['kind']}**",
            f"- primitive bits: **{selected['description_bits']:,}**",
            f"- program bits: **{selected['program_bits']:,}**",
            f"- validation families: **{len(selected['validation_families'])}**",
            f"- validation accuracy: **{selected['validation_accuracy']:.1%}**",
            f"- unseen application-domain accuracy: **{selected['novel_domain_accuracy']:.1%}**",
            f"- Unicode distribution-shift accuracy: **{selected['unicode_shift_accuracy']:.1%}**",
            "",
            "## Lifetime adoption",
            "",
            f"- one expected call adopted: **{adoption['one_call']['adopted']}**",
            f"- 100 expected calls adopted: **{adoption['one_hundred_calls']['adopted']}**",
            f"- 100-call normalized gain: **{adoption['one_hundred_calls']['normalized_lifetime_gain_bits']:,} bits**",
            "",
            "The result is representation extension inside a bounded meta-grammar, not proof",
            "of unrestricted autonomous primitive invention.",
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
    (output / "phase11c.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase11c.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
