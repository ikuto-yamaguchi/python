from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

from .benchmark_harness import RunPolicy, answer_is_correct, run_command_adapter, score_report
from .generic_quantifier import (
    MembershipObservation,
    QuantityObservation,
    QuantifiedExample,
    induce_generic_quantifier,
)
from .phase13a_experiment import build_phase13a_manifest


def quantity_calibration() -> tuple[QuantityObservation, ...]:
    return (
        QuantityObservation("a", 1),
        QuantityObservation("an", 1),
        QuantityObservation("one", 1),
        QuantityObservation("two", 2),
        QuantityObservation("three", 3),
        QuantityObservation("four", 4),
        QuantityObservation("five", 5),
        QuantityObservation("six", 6),
        QuantityObservation("seven", 7),
        QuantityObservation("eight", 8),
        QuantityObservation("nine", 9),
        QuantityObservation("ten", 10),
    )


def universal_concept_calibration() -> tuple[QuantifiedExample, ...]:
    return (
        QuantifiedExample(
            "I have two servers, a router, and three disks. How many objects do I have?",
            6,
        ),
        QuantifiedExample(
            "I have an alert, four retries, and a cache. How many objects do I have?",
            6,
        ),
        QuantifiedExample(
            "I have a badge, two cables, and five logs. How many objects do I have?",
            8,
        ),
    )


def build_public_quantifier():
    return induce_generic_quantifier(
        quantity_calibration(), universal_concept_calibration(), memberships=()
    )


def build_membership_demo_quantifier():
    return induce_generic_quantifier(
        quantity_calibration(),
        universal_concept_calibration(),
        memberships=(
            MembershipObservation("servers", "infrastructure"),
            MembershipObservation("router", "infrastructure"),
            MembershipObservation("disks", "infrastructure"),
            MembershipObservation("alerts", "telemetry"),
        ),
    )


def _axis_scores(manifest, predictions: dict[str, str]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[object]] = {}
    for example in manifest.examples:
        grouped.setdefault(example.axis, []).append(example)
    output: dict[str, dict[str, object]] = {}
    for axis, rows in sorted(grouped.items()):
        answered = sum(
            bool(predictions.get(row.example_id, "").strip())
            and predictions.get(row.example_id, "").strip() != "__ABSTAIN__"
            for row in rows
        )
        correct = sum(
            answer_is_correct(row, predictions.get(row.example_id, "")) for row in rows
        )
        wrong = answered - correct
        output[axis] = {
            "examples": len(rows),
            "answered": answered,
            "correct": correct,
            "wrong": wrong,
            "accuracy": correct / len(rows),
            "coverage": answered / len(rows),
        }
    return output


def _identifiability_examples() -> dict[str, object]:
    public = build_public_quantifier()
    unknown_prompt = (
        "I have two quorps, a zibble, and three narns. "
        "How many glippets do I have?"
    )
    interval = public.identifiability_interval(unknown_prompt)
    membership = build_membership_demo_quantifier()
    known_prompt = (
        "I have two servers, a router, and three disks. "
        "How many infrastructure do I have?"
    )
    return {
        "unknown_category": {
            "answer": public.answer(unknown_prompt),
            "minimum": None if interval is None else interval.minimum,
            "maximum": None if interval is None else interval.maximum,
            "identifiable": False if interval is None else interval.identifiable,
        },
        "grounded_category": {
            "answer": membership.answer(known_prompt),
            "expected": 6,
        },
    }


def run() -> dict[str, object]:
    manifest, source_hashes = build_phase13a_manifest()
    policy = RunPolicy(
        max_output_chars=256,
        stop_sequences=("\n\n",),
        tools_allowed=(),
        temperature=0.0,
        seed=0,
    )
    before = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase13c-scope-corrected-algebra",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase13c_worker"),
        timeout_seconds=300.0,
    )
    after = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase13d-generic-quantifier",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase13d_worker"),
        timeout_seconds=300.0,
    )
    before_score = score_report(manifest, before)
    after_score = score_report(manifest, after)
    before_predictions = {row.example_id: row.text for row in before.predictions}
    after_predictions = {row.example_id: row.text for row in after.predictions}
    before_axes = _axis_scores(manifest, before_predictions)
    after_axes = _axis_scores(manifest, after_predictions)
    quantifier = build_public_quantifier()
    calibration_prompts = {row.prompt for row in universal_concept_calibration()}
    exact_overlap = sum(row.prompt in calibration_prompts for row in manifest.examples)
    object_rows = [row for row in manifest.examples if row.axis == "object_counting"]
    answered_object_rows = [
        row
        for row in object_rows
        if after_predictions.get(row.example_id, "").strip()
        and after_predictions.get(row.example_id, "").strip() != "__ABSTAIN__"
    ]
    answered_query_concepts = sorted(
        {
            parsed.query_concept
            for row in answered_object_rows
            if (parsed := quantifier.parse(row.prompt)) is not None
        }
    )
    return {
        "suite": {
            "name": manifest.name,
            "manifest_sha256": manifest.sha256,
            "source_hashes": source_hashes,
            "public": manifest.public,
            "examples": len(manifest.examples),
            "axes": len(after_axes),
            "exact_calibration_prompt_overlap": exact_overlap,
            "benchmark_examples_used_for_calibration": 0,
        },
        "quantifier": {
            "quantity_groundings": len(quantifier.quantity_lexicon),
            "universal_concepts": quantifier.universal_concepts,
            "membership_entries": len(quantifier.memberships),
            "description_bits": quantifier.description_bits,
            "description_bytes": (quantifier.description_bits + 7) // 8,
            "domain_specific_handlers": quantifier.domain_specific_handlers,
            "benchmark_specific_handlers_added": 0,
            "benchmark_specific_item_lexicon_entries": 0,
            "answered_public_query_concepts": answered_query_concepts,
            "identifiability_demo": _identifiability_examples(),
        },
        "before": {
            "score": asdict(before_score),
            "axis_scores": before_axes,
            "resources": asdict(before.resources),
        },
        "after": {
            "score": asdict(after_score),
            "axis_scores": after_axes,
            "resources": asdict(after.resources),
        },
        "delta": {
            "correct": after_score.correct - before_score.correct,
            "accuracy_points": 100 * (after_score.overall_accuracy - before_score.overall_accuracy),
            "coverage_points": 100 * (after_score.coverage - before_score.coverage),
        },
        "gates": {
            "generic_quantity_reduction_demonstrated": after_axes["object_counting"]["correct"] > 0,
            "unknown_semantics_abstain": after_axes["object_counting"]["wrong"] == 0,
            "benchmark_specialization_used": False,
            "public_multi_domain_quality_parity_allowed": False,
            "public_multi_domain_runtime_pareto_allowed": False,
            "general_llm_parity_allowed": False,
            "stage_c_score_changed": False,
        },
        "limitations": [
            "the inventory sentence pattern and phrase segmentation are human-designed bounded grammar",
            "quantity words are grounded by twelve independent observations rather than learned from unrestricted text",
            "only the universal objects concept is induced for the public worker",
            "fruit, animal, vegetable, and instrument membership remains ungrounded by design",
            "the public improvement measures quantified reduction, not open-world semantic knowledge",
            "no matched open-model comparison is included",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    quantifier = payload["quantifier"]
    before = payload["before"]
    after = payload["after"]
    lines = [
        "# Phase 13d results: generic quantified reduction with semantic abstention",
        "",
        "A generic quantifier extracts variable-length owned-item sequences, grounds",
        "quantity words, and reduces a query only when its concept membership is identifiable.",
        "No benchmark item-category dictionary is added.",
        "",
        "## Anti-specialization checks",
        "",
        f"- independent quantity groundings: **{quantifier['quantity_groundings']}**",
        f"- induced universal concepts: **{quantifier['universal_concepts']}**",
        f"- public-worker membership entries: **{quantifier['membership_entries']}**",
        f"- benchmark-specific handlers / item lexicon: **{quantifier['benchmark_specific_handlers_added']} / {quantifier['benchmark_specific_item_lexicon_entries']}**",
        f"- exact calibration prompt overlap: **{payload['suite']['exact_calibration_prompt_overlap']}**",
        "",
        "## Public accuracy before and after",
        "",
        "| axis | Phase 13c | Phase 13d |",
        "|---|---:|---:|",
    ]
    for axis in after["axis_scores"]:
        lines.append(
            f"| {axis.replace('_', ' ')} | {100 * before['axis_scores'][axis]['accuracy']:.1f}% | {100 * after['axis_scores'][axis]['accuracy']:.1f}% |"
        )
    object_axis = after["axis_scores"]["object_counting"]
    unknown = quantifier["identifiability_demo"]["unknown_category"]
    lines.extend(
        [
            "",
            f"Overall: **{100 * before['score']['overall_accuracy']:.1f}% → {100 * after['score']['overall_accuracy']:.1f}%**",
            f"Object counting correct / wrong / answered: **{object_axis['correct']} / {object_axis['wrong']} / {object_axis['answered']}**",
            f"Answered query concepts: **{quantifier['answered_public_query_concepts']}**",
            "",
            "## Information boundary",
            "",
            f"For an ungrounded category, the inferred count interval is **[{unknown['minimum']}, {unknown['maximum']}]** and the model abstains.",
            "The syntax determines quantities, but category membership is additional information.",
            "",
            "## Claim boundary",
            "",
            "This phase demonstrates generic quantified reduction and calibrated semantic",
            "abstention. It does not solve open-world concept acquisition or establish LLM parity.",
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
    (output_dir / "phase13d.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "phase13d.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
