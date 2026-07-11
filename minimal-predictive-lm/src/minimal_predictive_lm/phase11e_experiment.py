from __future__ import annotations

import json
from pathlib import Path

from .continuous_stream_induction import (
    cluster_coverage,
    event_precision_recall,
    infer_continuous_stream,
)


def _training_stream() -> str:
    return (
        "sphinx became SPHINX and test passed source runA. "
        "もし retry なら quartz to QUARTZ success 根拠 runB。 "
        "zebra changed into ZEBRA status ok origin trace7; "
        "VOW became vow and validation passed source down1. "
        "when rollback QUICK to quick failed evidence test9. "
        "ZEBRA changed into zebra status success origin down2. "
        "unrelated x changed to y and note only."
    )


def _training_expected() -> tuple[tuple[object, ...], ...]:
    return (
        ("sphinx", "SPHINX", "success", False, "runA"),
        ("quartz", "QUARTZ", "success", True, "runB"),
        ("zebra", "ZEBRA", "success", False, "trace7"),
        ("VOW", "vow", "success", False, "down1"),
        ("QUICK", "quick", "failure", True, "test9"),
        ("ZEBRA", "zebra", "success", False, "down2"),
    )


def _novel_stream() -> str:
    return (
        "feature changed into FEATURE and validation passed source repo21. "
        "if recovery MOTOR to motor success evidence sensor4. "
        "pipeline became PIPELINE but test failed origin ci8."
    )


def _novel_expected() -> tuple[tuple[object, ...], ...]:
    return (
        ("feature", "FEATURE", "success", False, "repo21"),
        ("MOTOR", "motor", "success", True, "sensor4"),
        ("pipeline", "PIPELINE", "failure", False, "ci8"),
    )


def _novel_cluster_accuracy(training, novel) -> float:
    if not novel.events:
        return 0.0
    correct = 0
    for event in novel.events:
        matches = [
            cluster
            for cluster in training.clusters
            if cluster.primitive.apply(event.source) == event.target
        ]
        correct += int(len(matches) == 1 and matches[0].primitive.offset == event.offset)
    return correct / len(novel.events)


def run() -> dict[str, object]:
    training = infer_continuous_stream(_training_stream())
    novel = infer_continuous_stream(_novel_stream())
    train_precision, train_recall = event_precision_recall(
        training.events,
        _training_expected(),
    )
    novel_precision, novel_recall = event_precision_recall(
        novel.events,
        _novel_expected(),
    )
    cluster_rows = [
        {
            "identifier": cluster.identifier,
            "primitive": cluster.primitive.render(),
            "support_events": cluster.support_events,
            "description_bits": cluster.description_bits,
            "normalized_gain_bits": cluster.normalized_gain_bits,
        }
        for cluster in training.clusters
    ]
    novel_cluster_accuracy = _novel_cluster_accuracy(training, novel)
    return {
        "continuous_stream": {
            "record_boundaries_supplied": False,
            "channel_metadata_supplied": False,
            "quotes_or_backticks_used": False,
            "generic_punctuation_boundary_cues_used": True,
            "training_stream_bits": training.stream_bits,
            "inferred_events": len(training.events),
            "expected_events": len(_training_expected()),
            "event_precision": train_precision,
            "event_recall": train_recall,
            "candidate_pair_evaluations": training.candidate_pair_evaluations,
            "distractor_ignored": all(
                event.source != "x" and event.target != "y"
                for event in training.events
            ),
        },
        "shared_primitives": {
            "cluster_count": len(training.clusters),
            "cluster_coverage": cluster_coverage(training.clusters, training.events),
            "clusters": cluster_rows,
            "domain_specific_parsers_added": 0,
        },
        "unseen_stream": {
            "events": len(novel.events),
            "event_precision": novel_precision,
            "event_recall": novel_recall,
            "cluster_assignment_accuracy": novel_cluster_accuracy,
            "engine_code_changes": 0,
        },
        "comparison_readiness": {
            "narrow_open_model_comparison_already_available": True,
            "multi_domain_llm_parity_ready": False,
            "remaining_hard_gates": [
                "public multi-domain benchmark from raw inputs",
                "candidate generation beyond bounded transformation meta-grammar",
                "long-form language generation and semantic preference evaluation",
            ],
            "stage_c_score_changed": False,
        },
        "verdict": {
            "phase11e_success": (
                train_precision == 1.0
                and train_recall == 1.0
                and len(training.clusters) == 2
                and cluster_coverage(training.clusters, training.events) == 1.0
                and novel_precision == 1.0
                and novel_recall == 1.0
                and novel_cluster_accuracy == 1.0
            ),
            "open_ended_stream_grounding_achieved": False,
        },
        "limitations": [
            "generic punctuation and line breaks still act as strong event-boundary cues",
            "role induction uses a bounded multilingual cue inventory for result, condition, and provenance",
            "candidate source and target values are restricted to nearby ASCII identifier-like tokens",
            "the transformation family remains constant codepoint offsets",
            "streams are synthetic and short",
            "the experiment does not establish public multi-domain or general LLM parity",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    stream = payload["continuous_stream"]
    shared = payload["shared_primitives"]
    novel = payload["unseen_stream"]
    readiness = payload["comparison_readiness"]
    lines = [
        "# Phase 11e results: continuous mixed-stream event induction",
        "",
        "The learner receives one continuous mixed-style stream without record objects,",
        "task-family labels, channel metadata, quotes, or backticks.",
        "",
        "## Event and role induction",
        "",
        f"- inferred / expected events: **{stream['inferred_events']} / {stream['expected_events']}**",
        f"- event precision / recall: **{stream['event_precision']:.1%} / {stream['event_recall']:.1%}**",
        f"- candidate pair evaluations: **{stream['candidate_pair_evaluations']:,}**",
        f"- unrelated distractor ignored: **{stream['distractor_ignored']}**",
        "",
        "## Shared primitive induction",
        "",
        f"- clusters: **{shared['cluster_count']}**",
        f"- event coverage: **{shared['cluster_coverage']:.1%}**",
        f"- domain-specific parsers added: **{shared['domain_specific_parsers_added']}**",
        "",
        "| cluster | interval | offset | support | bits |",
        "|---|---:|---:|---:|---:|",
    ]
    for cluster in shared["clusters"]:
        primitive = cluster["primitive"]
        lines.append(
            f"| {cluster['identifier']} | "
            f"{primitive['lower_codepoint']}–{primitive['upper_codepoint']} | "
            f"{primitive['offset']} | {cluster['support_events']} | "
            f"{cluster['description_bits']:,} |"
        )
    lines.extend(
        [
            "",
            "## Unseen continuous stream",
            "",
            f"- events: **{novel['events']}**",
            f"- event precision / recall: **{novel['event_precision']:.1%} / {novel['event_recall']:.1%}**",
            f"- primitive-cluster assignment: **{novel['cluster_assignment_accuracy']:.1%}**",
            f"- engine code changes: **{novel['engine_code_changes']}**",
            "",
            "## LLM comparison gate",
            "",
            f"- narrow matched comparison already available: **{readiness['narrow_open_model_comparison_already_available']}**",
            f"- multi-domain LLM parity ready: **{readiness['multi_domain_llm_parity_ready']}**",
            "",
            "This removes supplied record and channel labels, but punctuation, a bounded role",
            "cue inventory, ASCII identifiers, and a fixed offset transformation family remain.",
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
    (output / "phase11e.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase11e.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
