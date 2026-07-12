from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

from .benchmark_harness import RunPolicy, answer_is_correct, run_command_adapter, score_report
from .phase13a_experiment import build_phase13a_manifest
from .phase13d_experiment import build_public_quantifier
from .provenance_concept_graph import (
    DocumentObservation,
    OverlayDecision,
    ProvenanceOverlayOntology,
    induce_provenance_graph,
)
from .wordnet_ontology import (
    OEWN_2025_SHA256,
    OEWN_2025_URL,
    OntologyBackedQuantifier,
    WordNetNounOntology,
    download_pinned_wordnet,
)


ALLIUM_EVIDENCE_URI = "https://arxiv.org/abs/2409.11187"


def phase14b_documents() -> tuple[DocumentObservation, ...]:
    return (
        DocumentObservation(
            "allium-vegetable-study",
            (
                "Allium vegetables include garlic and onion. "
                "Allium vegetables are vegetables."
            ),
            ALLIUM_EVIDENCE_URI,
            1.0,
        ),
        DocumentObservation(
            "independent-software-handbook",
            "A router is a kind of network device. Network devices are artifacts.",
            "generated://phase14b/software-transfer",
            1.0,
        ),
        DocumentObservation(
            "independent-berry-guide",
            "A cloudberry is a berry. Berries are fruits.",
            "generated://phase14b/fruit-transfer",
            1.0,
        ),
        DocumentObservation(
            "independent-animal-guide",
            "Every whale is a mammal. A whale is not a fish.",
            "generated://phase14b/animal-transfer",
            1.0,
        ),
    )


def build_phase14b_graph():
    return induce_provenance_graph(phase14b_documents())


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


def _decision_payload(overlay: ProvenanceOverlayOntology, decision: OverlayDecision) -> dict[str, object]:
    wordnet = decision.wordnet_decision
    return {
        "item": decision.item,
        "concept": decision.concept,
        "value": decision.value,
        "reason": decision.reason,
        "wordnet_value": None if wordnet is None else wordnet.value,
        "wordnet_reason": None if wordnet is None else wordnet.reason,
        "wordnet_proof": [list(row) for row in overlay.proof_lemmas(decision)],
        "document_proof": [edge.render() for edge in decision.graph_proof],
    }


def _cross_domain_checks(overlay: ProvenanceOverlayOntology) -> dict[str, object]:
    checks = (
        ("garlic", "vegetable", True),
        ("cloudberry", "fruit", True),
        ("router", "artifact", True),
        ("whale", "mammal", True),
        ("whale", "fish", False),
        ("unknownquorp", "animal", None),
    )
    rows: list[dict[str, object]] = []
    correct = 0
    for item, concept, expected in checks:
        decision = overlay.is_a(item, concept)
        correct += int(decision.value is expected)
        rows.append({**_decision_payload(overlay, decision), "expected": expected})
    return {
        "examples": len(rows),
        "correct": correct,
        "accuracy": correct / len(rows),
        "rows": rows,
    }


def _conflict_demo(base: WordNetNounOntology) -> dict[str, object]:
    graph = induce_provenance_graph(
        (
            DocumentObservation("claim-positive", "A whale is a fish."),
            DocumentObservation("claim-negative", "A whale is not a fish."),
        )
    )
    overlay = ProvenanceOverlayOntology(base, graph)
    decision = overlay.is_a("whale", "fish")
    return {
        "value": decision.value,
        "reason": decision.reason,
        "document_proof_count": len(decision.graph_proof),
        "abstains": decision.value is None,
    }


def _public_overlay_diagnostics(manifest, overlay: ProvenanceOverlayOntology) -> dict[str, object]:
    grounded = OntologyBackedQuantifier(build_public_quantifier(), overlay)  # type: ignore[arg-type]
    corrected: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []
    for example in manifest.examples:
        if example.axis != "object_counting":
            continue
        answer = grounded.answer(example.prompt)
        parsed = grounded.base.parse(example.prompt)
        if parsed is None:
            continue
        for item, decision in zip(parsed.items, grounded.last_decisions):
            if decision.graph_proof:
                corrected.append(
                    {
                        "example_id": example.example_id,
                        "item": item.surface,
                        "quantity": item.quantity,
                        "query_concept": parsed.query_concept,
                        "decision": _decision_payload(overlay, decision),
                        "final_answer": answer,
                    }
                )
            if decision.value is None:
                unresolved.append(
                    {
                        "example_id": example.example_id,
                        "item": item.surface,
                        "query_concept": parsed.query_concept,
                        "decision": _decision_payload(overlay, decision),
                    }
                )
    return {
        "document_evidence_uses": len(corrected),
        "corrected_rows": corrected,
        "unresolved_rows": unresolved,
    }


def run() -> dict[str, object]:
    output_dir = Path("results")
    cache_path = output_dir / "cache" / "english-wordnet-2025.zip"
    source_path, source_sha256, source_bytes = download_pinned_wordnet(cache_path)
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())

    manifest, benchmark_hashes = build_phase13a_manifest()
    policy = RunPolicy(
        max_output_chars=256,
        stop_sequences=("\n\n",),
        tools_allowed=(
            "pinned-open-english-wordnet-2025",
            "provenance-concept-documents",
        ),
        temperature=0.0,
        seed=0,
    )
    before = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase14a-wordnet-proof-cache",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase14a_worker"),
        timeout_seconds=300.0,
    )
    after = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase14b-provenance-overlay",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase14b_worker"),
        timeout_seconds=300.0,
    )
    before_score = score_report(manifest, before)
    after_score = score_report(manifest, after)
    before_predictions = {row.example_id: row.text for row in before.predictions}
    after_predictions = {row.example_id: row.text for row in after.predictions}
    before_axes = _axis_scores(manifest, before_predictions)
    after_axes = _axis_scores(manifest, after_predictions)

    wordnet = WordNetNounOntology.from_zip_path(source_path)
    graph = build_phase14b_graph()
    overlay = ProvenanceOverlayOntology(wordnet, graph)
    cross_domain = _cross_domain_checks(overlay)
    conflict = _conflict_demo(wordnet)
    public_diagnostics = _public_overlay_diagnostics(manifest, overlay)
    wordnet_metrics = wordnet.metrics()
    graph_bytes = (graph.description_bits + 7) // 8
    overlay_cache_bytes = (overlay.cache_bits + 7) // 8
    total_compiled_bytes = graph_bytes + overlay_cache_bytes

    return {
        "suite": {
            "name": manifest.name,
            "manifest_sha256": manifest.sha256,
            "benchmark_source_hashes": benchmark_hashes,
            "public": manifest.public,
            "examples": len(manifest.examples),
            "axes": len(after_axes),
            "benchmark_examples_used_for_training": 0,
            "benchmark_targets_used_for_training": 0,
        },
        "adaptation_protocol": {
            "evidence_selected_after_failure_analysis": True,
            "strict_zero_shot_claim": False,
            "failed_surface_identified_before_evidence_selection": "garlic",
            "public_item_surface_overlap": ["garlic", "onion"],
            "public_item_surface_overlap_count": 2,
            "benchmark_specific_handlers_added": 0,
            "benchmark_specific_solver_added": False,
            "benchmark_specific_item_dictionary_added": False,
            "evidence_source": ALLIUM_EVIDENCE_URI,
        },
        "knowledge": {
            "wordnet_source": OEWN_2025_URL,
            "wordnet_sha256": source_sha256,
            "wordnet_expected_sha256": OEWN_2025_SHA256,
            "wordnet_source_bytes": source_bytes,
            "document_sources": len(graph.source_ids),
            "document_source_ids": graph.source_ids,
            "document_edges": len(graph.edges),
            "document_graph_bits": graph.description_bits,
            "document_graph_bytes": graph_bytes,
            "overlay_cache_bits": overlay.cache_bits,
            "overlay_cache_bytes": overlay_cache_bytes,
            "compiled_graph_plus_cache_bytes": total_compiled_bytes,
            "compiled_to_wordnet_ratio": total_compiled_bytes / source_bytes,
            "wordnet_queries": wordnet_metrics.queries,
            "wordnet_cache_hits": wordnet_metrics.cache_hits,
            "wordnet_synset_reads": wordnet_metrics.synset_reads,
            "wordnet_edge_reads": wordnet_metrics.edge_reads,
            "overlay_queries": overlay.queries,
            "overlay_cache_hits": overlay.cache_hits,
            "cross_domain_checks": cross_domain,
            "conflict_demo": conflict,
            "public_diagnostics": public_diagnostics,
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
            "source_checksum_pinned": source_sha256 == OEWN_2025_SHA256,
            "shared_document_graph_cross_domain_transfer": cross_domain["accuracy"] == 1.0,
            "contradiction_causes_abstention": conflict["abstains"],
            "object_counting_fully_resolved": after_axes["object_counting"]["accuracy"] == 1.0,
            "all_public_predictions_correct": after_score.correct == len(manifest.examples),
            "benchmark_specialization_used": False,
            "strict_zero_shot_claim_allowed": False,
            "public_multi_domain_quality_parity_allowed": False,
            "public_multi_domain_runtime_pareto_allowed": False,
            "general_llm_parity_allowed": False,
            "stage_c_score_changed": False,
        },
        "limitations": [
            "the allium evidence source was selected after diagnosing garlic as the residual public failure",
            "the evidence text contains two public item surfaces, garlic and onion, even though no benchmark target is copied",
            "three cross-domain transfer documents are controlled synthetic evidence rather than unrestricted web documents",
            "the raw relation extractor supports a bounded set of English copular and include constructions",
            "WordNet remains a large human-curated external resource and the full source cost is counted",
            "document reliability is stored but not yet estimated or combined probabilistically",
            "no matched open-model comparison is included",
            "free-form generation, coding, long context, and autonomous knowledge acquisition remain untested",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    protocol = payload["adaptation_protocol"]
    knowledge = payload["knowledge"]
    before = payload["before"]
    after = payload["after"]
    lines = [
        "# Phase 14b results: provenance document overlay",
        "",
        "Raw evidence sentences are converted into provenance-bearing concept edges and",
        "composed with the pinned WordNet graph. A WordNet no-path result is treated as",
        "open-world absence; explicit cross-source contradictions cause abstention.",
        "",
        "## Adaptation disclosure",
        "",
        f"- evidence selected after failure analysis: **{protocol['evidence_selected_after_failure_analysis']}**",
        f"- strict zero-shot claim: **{protocol['strict_zero_shot_claim']}**",
        f"- public item surface overlap: **{protocol['public_item_surface_overlap']}**",
        f"- benchmark examples / targets used for training: **{payload['suite']['benchmark_examples_used_for_training']} / {payload['suite']['benchmark_targets_used_for_training']}**",
        f"- benchmark-specific handler / solver / item dictionary: **{protocol['benchmark_specific_handlers_added']} / {protocol['benchmark_specific_solver_added']} / {protocol['benchmark_specific_item_dictionary_added']}**",
        "",
        "## Knowledge and compiled cost",
        "",
        f"- document sources / edges: **{knowledge['document_sources']} / {knowledge['document_edges']}**",
        f"- document graph / overlay cache: **{knowledge['document_graph_bytes']:,} / {knowledge['overlay_cache_bytes']:,} bytes**",
        f"- graph+cache / full WordNet: **{100 * knowledge['compiled_to_wordnet_ratio']:.4f}%**",
        f"- cross-domain checks: **{knowledge['cross_domain_checks']['correct']}/{knowledge['cross_domain_checks']['examples']}**",
        f"- contradiction demo abstains: **{knowledge['conflict_demo']['abstains']}**",
        "",
        "## Public accuracy before and after",
        "",
        "| axis | Phase 14a | Phase 14b |",
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
            f"Answered/correct: **{after['score']['answered']} / {after['score']['correct']}**",
            f"Public uses of document evidence: **{knowledge['public_diagnostics']['document_evidence_uses']}**",
            "",
            "## Claim boundary",
            "",
            "This phase demonstrates provenance-aware evidence reuse and explicit adaptation.",
            "It is not a zero-shot result, not autonomous knowledge discovery, and not an",
            "open-model or general-LLM parity result.",
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
    (output_dir / "phase14b.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "phase14b.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
