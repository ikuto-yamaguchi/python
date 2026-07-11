from __future__ import annotations

import json
from pathlib import Path

from .grounded_knowledge import (
    Claim,
    SourceObservation,
    build_knowledge_index,
    learn_source_trust,
)


SOURCE_COUNTS = {
    "official": (98, 2),
    "lab": (90, 10),
    "blog": (70, 30),
    "rumor": (55, 45),
}
VALUES = ("red", "green", "blue")


def calibration_observations() -> list[SourceObservation]:
    return [
        SourceObservation(source, correct)
        for source, (successes, failures) in SOURCE_COUNTS.items()
        for correct, count in ((True, successes), (False, failures))
        for _ in range(count)
    ]


def heldout_claims() -> tuple[list[Claim], dict[str, str]]:
    claims: list[Claim] = []
    truth: dict[str, str] = {}
    for index in range(1000):
        subject = f"item_{index}"
        true_value = VALUES[index % len(VALUES)]
        truth[subject] = true_value
        for source in SOURCE_COUNTS:
            if source == "official":
                correct = index % 50 != 0
            elif source == "lab":
                correct = index % 10 != 0
            elif source == "blog":
                correct = index % 10 < 7
            else:
                correct = index % 20 < 11
            if correct:
                value = true_value
            else:
                offset = 1 if (index + len(source)) % 2 == 0 else 2
                value = VALUES[
                    (VALUES.index(true_value) + offset) % len(VALUES)
                ]
            claims.append(
                Claim(
                    subject,
                    "color",
                    value,
                    source,
                    f"doc://{source}/{index}",
                )
            )
    return claims, truth


def _evaluate(
    index,
    truth: dict[str, str],
    *,
    threshold: float,
    adaptive: bool,
) -> dict[str, object]:
    answered = 0
    correct = 0
    reads = 0
    abstained = 0
    provenance_entries = 0
    for item_index in range(1100):
        subject = f"item_{item_index}"
        answer = index.answer(
            subject,
            "color",
            confidence_threshold=threshold,
            adaptive=adaptive,
        )
        reads += answer.claims_read
        provenance_entries += len(answer.provenance)
        if answer.abstained:
            abstained += 1
            continue
        answered += 1
        correct += int(answer.value == truth.get(subject))
    return {
        "queries": 1100,
        "answered": answered,
        "correct": correct,
        "selective_accuracy": correct / answered if answered else 0.0,
        "coverage": answered / 1100,
        "abstained": abstained,
        "claim_reads": reads,
        "mean_claim_reads": reads / 1100,
        "mean_provenance_entries": provenance_entries / 1100,
    }


def run() -> dict[str, object]:
    observations = calibration_observations()
    trust = learn_source_trust(observations)
    claims, truth = heldout_claims()
    index = build_knowledge_index(claims, trust)

    adaptive = _evaluate(
        index,
        truth,
        threshold=0.8,
        adaptive=True,
    )
    exhaustive = _evaluate(
        index,
        truth,
        threshold=0.8,
        adaptive=False,
    )
    always_answer = _evaluate(
        index,
        truth,
        threshold=0.0,
        adaptive=False,
    )

    conflicts = 0
    for subject in truth:
        values = {
            claim.value
            for claim in index.claims_by_key[("color", subject)]
        }
        conflicts += int(len(values) > 1)

    full_scan_reads = len(claims) * adaptive["queries"]

    return {
        "source_trust": {
            "calibration_observations": len(observations),
            "sources": {
                source: {
                    "successes": item.successes,
                    "failures": item.failures,
                    "posterior_reliability": item.reliability,
                    "evidence_weight": item.weight,
                }
                for source, item in sorted(trust.items())
            },
        },
        "knowledge_corpus": {
            "claims": len(claims),
            "known_subjects": len(truth),
            "unknown_queries": 100,
            "conflicting_subjects": conflicts,
            "index_bits": index.description_bits,
        },
        "policies": {
            "full_scan_claim_reads": full_scan_reads,
            "indexed_exhaustive": exhaustive,
            "adaptive_confidence": adaptive,
            "always_answer": always_answer,
            "adaptive_vs_full_scan_read_reduction": (
                1.0 - adaptive["claim_reads"] / full_scan_reads
            ),
            "adaptive_vs_indexed_exhaustive_read_reduction": (
                1.0
                - adaptive["claim_reads"] / exhaustive["claim_reads"]
            ),
        },
        "stage_c": {
            "readiness_points_before": 7,
            "readiness_points_after": 8,
            "knowledge_level_before": 1,
            "knowledge_level_after": 2,
            "stage_c_ready": False,
            "pareto_claim_allowed": False,
            "reason": (
                "held-out contradiction and abstention evidence is synthetic; "
                "no public open-domain QA benchmark has been run"
            ),
        },
        "limitations": [
            "claims are already parsed into subject-relation-value propositions",
            "source observations are supervised by known truth during calibration",
            "source reliability is stationary and independent across claims",
            "the corpus is synthetic and contains one relation",
            "adaptive stopping optimizes this bounded evidence model, not arbitrary web retrieval",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    corpus = payload["knowledge_corpus"]
    policies = payload["policies"]
    adaptive = policies["adaptive_confidence"]
    exhaustive = policies["indexed_exhaustive"]
    always = policies["always_answer"]
    stage = payload["stage_c"]
    lines = [
        "# Phase 10d results: grounded external knowledge with provenance and abstention",
        "",
        "Source reliability is learned from calibration outcomes. Claims are indexed by",
        "grounded concept keys, contradictory values are retained with provenance, and",
        "the machine abstains when weighted evidence is insufficient.",
        "",
        "## Corpus",
        "",
        f"- claims: **{corpus['claims']:,}**",
        f"- known subjects / unknown queries: **{corpus['known_subjects']:,} / {corpus['unknown_queries']}**",
        f"- conflicting subjects: **{corpus['conflicting_subjects']:,}**",
        f"- indexed knowledge bits: **{corpus['index_bits']:,}**",
        "",
        "## Policies",
        "",
        "| policy | selective accuracy | coverage | claim reads | mean reads |",
        "|---|---:|---:|---:|---:|",
        f"| always answer | {always['selective_accuracy']:.1%} | {always['coverage']:.1%} | {always['claim_reads']:,} | {always['mean_claim_reads']:.3f} |",
        f"| indexed exhaustive + abstain | {exhaustive['selective_accuracy']:.1%} | {exhaustive['coverage']:.1%} | {exhaustive['claim_reads']:,} | {exhaustive['mean_claim_reads']:.3f} |",
        f"| adaptive confidence + abstain | {adaptive['selective_accuracy']:.1%} | {adaptive['coverage']:.1%} | {adaptive['claim_reads']:,} | {adaptive['mean_claim_reads']:.3f} |",
        "",
        f"- naive full-scan reads: **{policies['full_scan_claim_reads']:,}**",
        f"- adaptive reduction vs full scan: **{policies['adaptive_vs_full_scan_read_reduction']:.2%}**",
        f"- adaptive reduction vs indexed exhaustive: **{policies['adaptive_vs_indexed_exhaustive_read_reduction']:.2%}**",
        "",
        "## Stage-C evidence",
        "",
        f"- readiness points: **{stage['readiness_points_before']} → {stage['readiness_points_after']} / 24**",
        f"- knowledge evidence level: **{stage['knowledge_level_before']} → {stage['knowledge_level_after']}**",
        f"- Stage C ready: **{stage['stage_c_ready']}**",
        "",
        "The score remains below public-benchmark evidence because proposition extraction",
        "and the corpus are synthetic.",
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
    (output / "phase10d.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase10d.md").write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
