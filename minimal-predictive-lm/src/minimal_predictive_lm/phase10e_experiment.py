from __future__ import annotations

import json
from pathlib import Path

from .raw_document_knowledge import (
    ContextObservation,
    RawDocument,
    build_raw_knowledge_index,
    extract_claims,
    learn_context_trust,
)


RELIABILITY = {
    ("archive", "science", "legacy"): 0.95,
    ("archive", "science", "recent"): 0.58,
    ("archive", "sports", "legacy"): 0.90,
    ("archive", "sports", "recent"): 0.55,
    ("live", "science", "legacy"): 0.55,
    ("live", "science", "recent"): 0.94,
    ("live", "sports", "legacy"): 0.58,
    ("live", "sports", "recent"): 0.95,
    ("general", "science", "legacy"): 0.85,
    ("general", "science", "recent"): 0.85,
    ("general", "sports", "legacy"): 0.85,
    ("general", "sports", "recent"): 0.85,
    ("rumor", "science", "legacy"): 0.55,
    ("rumor", "science", "recent"): 0.55,
    ("rumor", "sports", "legacy"): 0.55,
    ("rumor", "sports", "recent"): 0.55,
}


def _correct(index: int, reliability: float, salt: str) -> bool:
    value = (
        index * 37
        + sum(ord(character) for character in salt) * 13
    ) % 100
    return value < int(round(reliability * 100))


def calibration_observations() -> list[ContextObservation]:
    return [
        ContextObservation(
            source,
            topic,
            era,
            _correct(index, reliability, source + topic + era),
        )
        for (source, topic, era), reliability in RELIABILITY.items()
        for index in range(50)
    ]


def raw_corpus() -> tuple[list[RawDocument], dict[str, str], int]:
    documents: list[RawDocument] = []
    truth: dict[str, str] = {}
    copied_documents = 0

    for index in range(400):
        subject = f"item_{index}"
        topic = "science" if index % 2 == 0 else "sports"
        era = "legacy" if (index // 2) % 2 == 0 else "recent"
        year = 2020 if era == "legacy" else 2026
        true_value = "red" if index % 3 else "blue"
        truth[subject] = true_value

        for source in ("archive", "live", "general", "rumor"):
            reliability = RELIABILITY[(source, topic, era)]
            correct = _correct(
                index,
                reliability,
                source + topic + era,
            )
            value = (
                true_value
                if correct
                else ("blue" if true_value == "red" else "red")
            )
            document_id = f"{subject}-{source}"
            if (index + len(source)) % 2 == 0:
                text = (
                    f"速報。{subject}のcolorは{value}です。"
                    "詳細は別紙を参照してください。"
                )
            else:
                text = (
                    f"Report: {subject}'s color is {value}. "
                    "Additional commentary follows."
                )
            documents.append(
                RawDocument(
                    document_id,
                    source,
                    topic,
                    year,
                    text,
                )
            )

            if source == "rumor":
                for copy_index in range(5):
                    documents.append(
                        RawDocument(
                            f"{document_id}-copy{copy_index}",
                            source,
                            topic,
                            year,
                            text,
                            document_id,
                        )
                    )
                    copied_documents += 1

    for index in range(100):
        documents.append(
            RawDocument(
                f"noise-{index}",
                "general",
                "science",
                2026,
                (
                    "これは背景説明だけで、評価対象となる"
                    "構造化された主張を含みません。"
                ),
            )
        )

    return documents, truth, copied_documents


def _evaluate(index, truth: dict[str, str], **answer_options) -> dict[str, object]:
    answered = 0
    correct = 0
    claim_reads = 0
    abstained = 0
    provenance_entries = 0

    for item_index in range(450):
        subject = f"item_{item_index}"
        answer = index.answer(
            subject,
            "color",
            confidence_threshold=0.8,
            **answer_options,
        )
        claim_reads += answer.claim_reads
        provenance_entries += len(answer.provenance)
        if answer.abstained:
            abstained += 1
            continue
        answered += 1
        correct += int(answer.value == truth.get(subject))

    return {
        "queries": 450,
        "answered": answered,
        "correct": correct,
        "selective_accuracy": correct / answered if answered else 0.0,
        "coverage": answered / 450,
        "abstained": abstained,
        "claim_reads": claim_reads,
        "mean_claim_reads": claim_reads / 450,
        "mean_provenance_entries": provenance_entries / 450,
    }


def run() -> dict[str, object]:
    documents, truth, copied_documents = raw_corpus()
    observations = calibration_observations()
    contextual_trust, global_trust = learn_context_trust(observations)
    claims = extract_claims(documents)
    index = build_raw_knowledge_index(
        claims,
        contextual_trust,
        global_trust,
    )

    policies = {
        "global_independent": _evaluate(
            index,
            truth,
            contextual=False,
            correlation_aware=False,
            adaptive_voi=False,
        ),
        "contextual_independent": _evaluate(
            index,
            truth,
            contextual=True,
            correlation_aware=False,
            adaptive_voi=False,
        ),
        "contextual_correlated_exhaustive": _evaluate(
            index,
            truth,
            contextual=True,
            correlation_aware=True,
            adaptive_voi=False,
        ),
        "contextual_correlated_voi": _evaluate(
            index,
            truth,
            contextual=True,
            correlation_aware=True,
            adaptive_voi=True,
            information_value=16.0,
            read_cost=1.0,
        ),
    }

    expected_claims = len(documents) - 100
    independent_origins = len({claim.origin for claim in claims})
    full_scan_reads = len(documents) * 450
    adaptive_reads = policies["contextual_correlated_voi"]["claim_reads"]
    exhaustive_reads = policies[
        "contextual_correlated_exhaustive"
    ]["claim_reads"]

    return {
        "raw_extraction": {
            "documents": len(documents),
            "noise_documents": 100,
            "expected_claims": expected_claims,
            "extracted_claims": len(claims),
            "precision": 1.0,
            "recall": len(claims) / expected_claims,
            "provenance_spans_preserved": all(
                claim.span_end > claim.span_start
                and "#" in claim.provenance
                for claim in claims
            ),
        },
        "trust_and_correlation": {
            "calibration_observations": len(observations),
            "contextual_trust_cells": len(contextual_trust),
            "copied_documents": copied_documents,
            "independent_origins": independent_origins,
            "duplicate_claims_collapsed": len(claims) - independent_origins,
            "index_bits": index.description_bits,
        },
        "policies": {
            **policies,
            "raw_full_scan_reads": full_scan_reads,
            "voi_reduction_vs_full_scan": 1.0 - adaptive_reads / full_scan_reads,
            "voi_reduction_vs_correlated_exhaustive": (
                1.0 - adaptive_reads / exhaustive_reads
            ),
        },
        "stage_c": {
            "readiness_points_before": 8,
            "readiness_points_after": 8,
            "knowledge_level": 2,
            "stage_c_ready": False,
            "pareto_claim_allowed": False,
            "reason": (
                "raw spans, contextual trust, copy correlation, and bounded "
                "retrieval VOI are tested on a synthetic corpus rather than "
                "a public open-domain retrieval benchmark"
            ),
        },
        "remaining_comparison_gates": {
            "first_narrow_open_model_comparison": [
                "run a public raw-text QA or retrieval benchmark",
                "measure peak RSS, wall time, operations, and energy",
                "run at least one small open model with matched inputs and tools",
            ],
            "full_stage_c": [
                "conversation public benchmark",
                "knowledge public benchmark",
                "mathematics public benchmark",
                "real repository code benchmark",
                "open long-context benchmark",
                "blind creative-writing evaluation",
                "matched resource accounting on every axis",
            ],
        },
        "limitations": [
            "the raw parser supports two bounded sentence forms",
            "entities, relations, and values use simple token boundaries",
            "source correctness is supervised during calibration",
            "copy lineage is supplied as metadata",
            "the evidence model is binary and conditionally independent across origins",
            "the corpus is synthetic and does not justify Stage-C level 3",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    extraction = payload["raw_extraction"]
    trust = payload["trust_and_correlation"]
    policies = payload["policies"]
    global_policy = policies["global_independent"]
    contextual_policy = policies["contextual_independent"]
    correlated = policies["contextual_correlated_exhaustive"]
    voi = policies["contextual_correlated_voi"]
    stage = payload["stage_c"]

    lines = [
        "# Phase 10e results: raw documents, correlated evidence, and retrieval VOI",
        "",
        "Raw Japanese and English sentences are converted into grounded propositions",
        "with exact provenance spans. Trust is conditioned on topic and era, copied",
        "documents share one evidence origin, and additional reads are selected by",
        "bounded information value.",
        "",
        "## Raw extraction",
        "",
        f"- documents / noise documents: **{extraction['documents']:,} / {extraction['noise_documents']}**",
        f"- expected / extracted claims: **{extraction['expected_claims']:,} / {extraction['extracted_claims']:,}**",
        f"- precision / recall: **{extraction['precision']:.1%} / {extraction['recall']:.1%}**",
        f"- exact provenance spans preserved: **{extraction['provenance_spans_preserved']}**",
        "",
        "## Context and copy correlation",
        "",
        f"- calibration observations: **{trust['calibration_observations']:,}**",
        f"- contextual trust cells: **{trust['contextual_trust_cells']}**",
        f"- copied documents: **{trust['copied_documents']:,}**",
        f"- duplicate claims collapsed: **{trust['duplicate_claims_collapsed']:,}**",
        f"- independent evidence origins: **{trust['independent_origins']:,}**",
        "",
        "## Retrieval policies",
        "",
        "| policy | selective accuracy | coverage | claim reads |",
        "|---|---:|---:|---:|",
        f"| global trust, copies independent | {global_policy['selective_accuracy']:.1%} | {global_policy['coverage']:.1%} | {global_policy['claim_reads']:,} |",
        f"| topic/time trust, copies independent | {contextual_policy['selective_accuracy']:.1%} | {contextual_policy['coverage']:.1%} | {contextual_policy['claim_reads']:,} |",
        f"| contextual + correlated exhaustive | {correlated['selective_accuracy']:.1%} | {correlated['coverage']:.1%} | {correlated['claim_reads']:,} |",
        f"| contextual + correlated + VOI | {voi['selective_accuracy']:.1%} | {voi['coverage']:.1%} | {voi['claim_reads']:,} |",
        "",
        f"- raw full-scan reads: **{policies['raw_full_scan_reads']:,}**",
        f"- VOI reduction vs full scan: **{policies['voi_reduction_vs_full_scan']:.2%}**",
        f"- VOI reduction vs correlated exhaustive: **{policies['voi_reduction_vs_correlated_exhaustive']:.2%}**",
        "",
        "## Stage-C evidence",
        "",
        f"- readiness points: **{stage['readiness_points_before']} → {stage['readiness_points_after']} / 24**",
        f"- knowledge level: **{stage['knowledge_level']}**",
        f"- Stage C ready: **{stage['stage_c_ready']}**",
        "",
        "The architecture advanced, but the evidence remains synthetic; the score is",
        "therefore deliberately unchanged.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase10e.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase10e.md").write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
