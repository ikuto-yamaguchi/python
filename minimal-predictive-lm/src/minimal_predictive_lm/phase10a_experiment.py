from __future__ import annotations

import json
from pathlib import Path

from .phase9a_experiment import run as run_phase9a
from .phase9b_experiment import run as run_phase9b
from .phase9c_experiment import run as run_phase9c
from .stage_c_readiness import CapabilityEvidence, build_scorecard, choose_next_axis


def run() -> dict[str, object]:
    phase9a = run_phase9a()
    phase9b = run_phase9b()
    phase9c = run_phase9c()

    distant = phase9a["raw_grounding"]["distant_lexical_shift_accuracy"]
    connector_shift = phase9c["shifted_induction"]["interaction_induced_accuracy"]
    conversation_quality = min(connector_shift, max(distant, 0.0))
    graph_bits = phase9b["memory"]["graph_plus_provenance_bits"]

    scorecard = build_scorecard(
        (
            CapabilityEvidence(
                "conversation",
                2,
                conversation_quality,
                graph_bits,
                "synthetic event graphs plus interaction-induced unseen connectors; distant lexical shift remains weak",
            ),
            CapabilityEvidence(
                "knowledge",
                1,
                1.0,
                36864,
                "closed-world indexed fact retrieval up to 1024 facts; no open-domain knowledge benchmark",
            ),
            CapabilityEvidence(
                "mathematics",
                0,
                0.0,
                0,
                "no natural-language mathematics benchmark or general solver",
            ),
            CapabilityEvidence(
                "code",
                1,
                1.0,
                graph_bits,
                "synthetic one-function repair with test, rollback, second patch, and report",
            ),
            CapabilityEvidence(
                "long_context",
                1,
                1.0,
                6,
                "synthetic 10000-query state-retention test without open long-document understanding",
            ),
            CapabilityEvidence(
                "creative_writing",
                0,
                0.0,
                0,
                "no open-ended creative-writing quality evidence",
            ),
        )
    )
    next_axis = choose_next_axis(
        scorecard,
        {
            "conversation": 3.0,
            "knowledge": 2.0,
            "mathematics": 1.5,
            "code": 2.5,
            "long_context": 2.0,
            "creative_writing": 2.5,
        },
        {
            "conversation": 1.4,
            "knowledge": 1.0,
            "mathematics": 1.1,
            "code": 1.3,
            "long_context": 1.0,
            "creative_writing": 0.8,
        },
    )

    return {
        "definition": (
            "Stage C requires public open-domain evidence and matched-input resource measurement "
            "for conversation, knowledge, mathematics, code, long context, and creative writing"
        ),
        "scorecard": {
            "points": scorecard.level_points,
            "maximum_points": scorecard.maximum_points,
            "normalized_level": scorecard.normalized_level,
            "minimum_quality": scorecard.minimum_quality,
            "stage_c_ready": scorecard.stage_c_ready,
            "pareto_claim_allowed": scorecard.pareto_claim_allowed,
            "description_bits": scorecard.description_bits,
            "weakest_axes": list(scorecard.weakest_axes()),
            "axes": [
                {
                    "axis": item.axis,
                    "level": item.level,
                    "quality": item.quality,
                    "resource_bits": item.resource_bits,
                    "evidence": item.evidence,
                    "matched_inputs": item.matched_inputs,
                    "public_benchmark": item.public_benchmark,
                }
                for item in scorecard.evidence
            ],
        },
        "next_experiment_axis": next_axis,
        "anti_overclaim_gate": (
            "no open-model parity or efficiency claim is allowed until every axis uses the same public inputs, "
            "quality metric, context, tools, and measured model/RSS/compute/energy accounting"
        ),
        "phase10b_plan": [
            "add a natural-language exact-math substrate with generated and public held-out tasks",
            "add retrieval over external documents with provenance and abstention",
            "replace synthetic code repair with a small real repository",
            "add constrained and open creative-writing evaluation with blinded preference scoring",
            "run matched comparisons against 135M and 0.5-0.6B open models",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    scorecard = payload["scorecard"]
    lines = [
        "# Phase 10a results: Stage-C readiness and anti-overclaim gate",
        "",
        payload["definition"],
        "",
        f"- readiness points: **{scorecard['points']} / {scorecard['maximum_points']}**",
        f"- normalized evidence level: **{scorecard['normalized_level']:.1%}**",
        f"- Stage C ready: **{scorecard['stage_c_ready']}**",
        f"- Pareto claim allowed: **{scorecard['pareto_claim_allowed']}**",
        f"- weakest axes: **{', '.join(scorecard['weakest_axes'])}**",
        f"- next selected axis: **{payload['next_experiment_axis']}**",
        "",
        "| axis | level | quality | measured evidence |",
        "|---|---:|---:|---|",
    ]
    for item in scorecard["axes"]:
        lines.append(
            f"| {item['axis']} | {item['level']} | {item['quality']:.1%} | {item['evidence']} |"
        )
    lines.extend(
        [
            "",
            "The scorecard deliberately keeps synthetic success below public open-domain evidence.",
            "A small closed-world task cannot be used to claim parity with an open language model.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase10a.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "phase10a.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
