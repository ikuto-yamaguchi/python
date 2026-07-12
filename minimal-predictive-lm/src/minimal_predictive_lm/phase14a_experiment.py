from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

from .benchmark_harness import RunPolicy, answer_is_correct, run_command_adapter, score_report
from .phase13a_experiment import build_phase13a_manifest
from .phase13d_experiment import build_public_quantifier
from .wordnet_ontology import (
    OEWN_2025_SHA256,
    OEWN_2025_URL,
    OntologyBackedQuantifier,
    OntologyDecision,
    WordNetNounOntology,
    download_pinned_wordnet,
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
        output[axis] = {
            "examples": len(rows),
            "answered": answered,
            "correct": correct,
            "wrong": answered - correct,
            "accuracy": correct / len(rows),
            "coverage": answered / len(rows),
        }
    return output


def _decision_payload(
    ontology: WordNetNounOntology,
    decision: OntologyDecision,
) -> dict[str, object]:
    return {
        "item": decision.item,
        "concept": decision.concept,
        "value": decision.value,
        "reason": decision.reason,
        "item_candidates": list(decision.item_candidates),
        "concept_candidates": list(decision.concept_candidates),
        "proof": [list(row) for row in ontology.proof_lemmas(decision)],
    }


def _cross_domain_queries(ontology: WordNetNounOntology) -> dict[str, object]:
    checks = (
        ("salmon", "animal", True),
        ("violin", "instrument", True),
        ("router", "artifact", True),
        ("apple", "food", True),
        ("violin", "fruit", False),
        ("unknownquorp", "animal", None),
    )
    rows: list[dict[str, object]] = []
    correct = 0
    for item, concept, expected in checks:
        decision = ontology.is_a(item, concept)
        correct += int(decision.value is expected)
        rows.append(
            {
                **_decision_payload(ontology, decision),
                "expected": expected,
                "observed": decision.value,
            }
        )
    return {
        "examples": len(rows),
        "correct": correct,
        "accuracy": correct / len(rows),
        "rows": rows,
    }


def _collect_public_proofs(
    manifest,
    ontology: WordNetNounOntology,
    predictions: dict[str, str],
) -> dict[str, object]:
    grounded = OntologyBackedQuantifier(build_public_quantifier(), ontology)
    proof_examples: dict[str, object] = {}
    unresolved_items: set[str] = set()
    wrong_examples: list[dict[str, object]] = []
    resolved_true = 0
    resolved_false = 0
    unknown = 0
    for example in manifest.examples:
        if example.axis != "object_counting":
            continue
        local_answer = grounded.answer(example.prompt)
        parsed = grounded.base.parse(example.prompt)
        if parsed is None:
            continue
        for decision in grounded.last_decisions:
            if decision.value is True:
                resolved_true += 1
                proof_examples.setdefault(
                    parsed.query_concept,
                    _decision_payload(ontology, decision),
                )
            elif decision.value is False:
                resolved_false += 1
            else:
                unknown += 1
                unresolved_items.add(decision.item)
        prediction = predictions.get(example.example_id, "")
        if not answer_is_correct(example, prediction):
            wrong_examples.append(
                {
                    "id": example.example_id,
                    "prompt": example.prompt,
                    "query_concept": parsed.query_concept,
                    "target": example.target,
                    "worker_prediction": prediction,
                    "local_answer": local_answer,
                    "items": [
                        {
                            "surface": item.surface,
                            "quantity": item.quantity,
                            "decision": _decision_payload(ontology, decision),
                        }
                        for item, decision in zip(parsed.items, grounded.last_decisions)
                    ],
                }
            )
    return {
        "resolved_true": resolved_true,
        "resolved_false": resolved_false,
        "unknown": unknown,
        "unresolved_items": sorted(unresolved_items),
        "proof_examples": proof_examples,
        "wrong_examples": wrong_examples,
    }


def run() -> dict[str, object]:
    output_dir = Path("results")
    cache_path = output_dir / "cache" / "english-wordnet-2025.zip"
    source_path, source_sha256, source_bytes = download_pinned_wordnet(cache_path)
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    manifest, source_hashes = build_phase13a_manifest()
    policy = RunPolicy(
        max_output_chars=256,
        stop_sequences=("\n\n",),
        tools_allowed=("pinned-open-english-wordnet-2025",),
        temperature=0.0,
        seed=0,
    )
    before = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase13d-generic-quantifier",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase13d_worker"),
        timeout_seconds=300.0,
    )
    after = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase14a-wordnet-proof-cache",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase14a_worker"),
        timeout_seconds=300.0,
    )
    before_score = score_report(manifest, before)
    after_score = score_report(manifest, after)
    before_predictions = {row.example_id: row.text for row in before.predictions}
    after_predictions = {row.example_id: row.text for row in after.predictions}
    before_axes = _axis_scores(manifest, before_predictions)
    after_axes = _axis_scores(manifest, after_predictions)

    ontology = WordNetNounOntology.from_zip_path(source_path)
    cross_domain = _cross_domain_queries(ontology)
    public_proofs = _collect_public_proofs(manifest, ontology, after_predictions)
    ontology_metrics = ontology.metrics()
    cache_bytes = (ontology_metrics.cache_bits + 7) // 8

    return {
        "suite": {
            "name": manifest.name,
            "manifest_sha256": manifest.sha256,
            "benchmark_source_hashes": source_hashes,
            "public": manifest.public,
            "examples": len(manifest.examples),
            "axes": len(after_axes),
            "benchmark_examples_used_for_training": 0,
        },
        "ontology": {
            "source": OEWN_2025_URL,
            "license_id": "CC-BY-4.0",
            "release": "2025",
            "source_sha256": source_sha256,
            "expected_source_sha256": OEWN_2025_SHA256,
            "source_bytes": source_bytes,
            "noun_synsets": ontology_metrics.synsets,
            "lemmas": ontology_metrics.lemmas,
            "hypernym_edges": ontology_metrics.hypernym_edges,
            "query_cache_entries": ontology_metrics.cache_entries,
            "query_cache_bits": ontology_metrics.cache_bits,
            "query_cache_bytes": cache_bytes,
            "cache_to_source_ratio": cache_bytes / source_bytes,
            "queries": ontology_metrics.queries,
            "cache_hits": ontology_metrics.cache_hits,
            "synset_reads": ontology_metrics.synset_reads,
            "edge_reads": ontology_metrics.edge_reads,
            "benchmark_specific_handlers_added": 0,
            "benchmark_specific_item_lexicon_entries": 0,
            "query_driven_compilation": True,
            "cross_domain_checks": cross_domain,
            "public_proofs": public_proofs,
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
            "general_external_ontology_used": True,
            "source_checksum_pinned": source_sha256 == OEWN_2025_SHA256,
            "benchmark_specialization_used": False,
            "cross_domain_transfer_passed": cross_domain["accuracy"] == 1.0,
            "object_counting_fully_resolved": after_axes["object_counting"]["accuracy"] == 1.0,
            "all_answered_predictions_correct": after_score.correct == after_score.answered,
            "public_multi_domain_quality_parity_allowed": False,
            "public_multi_domain_runtime_pareto_allowed": False,
            "general_llm_parity_allowed": False,
            "stage_c_score_changed": False,
        },
        "limitations": [
            "Open English WordNet is a large human-curated external knowledge resource rather than knowledge induced from the model's own experience",
            "word-sense disambiguation uses an any-sense hypernym rule and can over-classify genuinely ambiguous words",
            "compound and plural normalization is a bounded human-designed morphology layer",
            "the full external ontology cost is counted in model_bytes even though only a small proof cache is used",
            "no matched open-model comparison is included",
            "free-form generation, coding, long context, and interactive knowledge acquisition remain untested",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    ontology = payload["ontology"]
    before = payload["before"]
    after = payload["after"]
    wrong_count = len(ontology["public_proofs"]["wrong_examples"])
    lines = [
        "# Phase 14a results: pinned general ontology with proof-cache compilation",
        "",
        "A fixed Open English WordNet release is treated as a general external knowledge",
        "source. The benchmark supplies no training examples or item-category dictionary.",
        "Only query-relevant hypernym proofs are retained in the compact runtime cache.",
        "",
        "## Knowledge-source accounting",
        "",
        f"- source SHA-256: **{ontology['source_sha256']}**",
        f"- full source bytes: **{ontology['source_bytes']:,}**",
        f"- noun synsets / lemmas / hypernym edges: **{ontology['noun_synsets']:,} / {ontology['lemmas']:,} / {ontology['hypernym_edges']:,}**",
        f"- compiled proof cache: **{ontology['query_cache_entries']} entries / {ontology['query_cache_bytes']:,} bytes**",
        f"- cache/source ratio: **{100 * ontology['cache_to_source_ratio']:.4f}%**",
        f"- synset / edge reads: **{ontology['synset_reads']:,} / {ontology['edge_reads']:,}**",
        f"- benchmark-specific handlers / item lexicon: **{ontology['benchmark_specific_handlers_added']} / {ontology['benchmark_specific_item_lexicon_entries']}**",
        f"- cross-domain ontology checks: **{ontology['cross_domain_checks']['correct']}/{ontology['cross_domain_checks']['examples']}**",
        "",
        "## Public accuracy before and after",
        "",
        "| axis | Phase 13d | Phase 14a |",
        "|---|---:|---:|",
    ]
    for axis in after["axis_scores"]:
        lines.append(
            f"| {axis.replace('_', ' ')} | {100 * before['axis_scores'][axis]['accuracy']:.1f}% | {100 * after['axis_scores'][axis]['accuracy']:.1f}% |"
        )
    lines.extend(
        [
            "",
            f"Overall: **{100 * before['score']['overall_accuracy']:.1f}% → {100 * after['score']['overall_accuracy']:.1f}%**",
            f"Coverage: **{100 * before['score']['coverage']:.1f}% → {100 * after['score']['coverage']:.1f}%**",
            f"Answered/correct: **{after['score']['answered']} / {after['score']['correct']}**",
            f"Saved wrong-example diagnostics: **{wrong_count}**",
            "",
            "## Claim boundary",
            "",
            "This phase demonstrates generic ontology retrieval and compact proof caching.",
            "It does not demonstrate autonomous world-knowledge learning: the external",
            "ontology is human-curated and its full storage/runtime cost is counted.",
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
    (output_dir / "phase14a.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "phase14a.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
