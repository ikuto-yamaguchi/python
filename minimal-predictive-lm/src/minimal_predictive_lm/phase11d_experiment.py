from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from .raw_primitive_grounding import (
    ContextualBypassPrimitive,
    IdentityPrimitive,
    RawResidualObservation,
    VersionedPrimitiveLibrary,
    induce_raw_primitive_clusters,
    learn_bypass_token,
    propose_residual_extension,
    raw_primitive_accuracy,
)


def _raw_training_stream() -> tuple[RawResidualObservation, ...]:
    return (
        RawResidualObservation(
            "upper-ja",
            "japanese",
            "表示要求。入力「sphinx of black quartz judge my vow」を処理し、"
            "結果「SPHINX OF BLACK QUARTZ JUDGE MY VOW」を返した。",
        ),
        RawResidualObservation(
            "upper-code",
            "code_diff",
            'diff\n- label = "the five boxing wizards jump quickly"\n'
            '+ label = "THE FIVE BOXING WIZARDS JUMP QUICKLY"\ntests PASS',
        ),
        RawResidualObservation(
            "upper-tool",
            "tool_trace",
            "format input='pack my box with five dozen liquor jugs' "
            "output='PACK MY BOX WITH FIVE DOZEN LIQUOR JUGS' status=ok",
        ),
        RawResidualObservation(
            "upper-test",
            "test_log",
            'case source="how vexingly quick daft zebras jump" '
            'observed="HOW VEXINGLY QUICK DAFT ZEBRAS JUMP" PASS',
        ),
        RawResidualObservation(
            "lower-code",
            "code_diff",
            'normalize source="SPHINX OF BLACK QUARTZ" '
            'result="sphinx of black quartz"',
        ),
        RawResidualObservation(
            "lower-tool",
            "tool_trace",
            "tool input='PACK MY BOX' output='pack my box' status=ok",
        ),
        RawResidualObservation(
            "lower-dialogue",
            "dialogue",
            "応答「RUN TEST NOW」を「run test now」として保存。",
        ),
        RawResidualObservation(
            "noise-replacement",
            "test_log",
            'replace source="alpha" result="omega" PASS',
        ),
    )


def _novel_modality() -> tuple[RawResidualObservation, ...]:
    return (
        RawResidualObservation(
            "novel-sensor",
            "sensor",
            'sensor reading="motor line-3" normalized="MOTOR LINE-3" ok',
        ),
        RawResidualObservation(
            "novel-repository",
            "repository",
            "symbol `feature branch` compiled as `FEATURE BRANCH`",
        ),
    )


def _unicode_shift() -> tuple[RawResidualObservation, ...]:
    return (
        RawResidualObservation(
            "unicode-sensor",
            "sensor",
            'sensor input="café déjà vu" output="CAFÉ DÉJÀ VU" status=ok',
        ),
        RawResidualObservation(
            "unicode-tool",
            "tool_trace",
            "tool input='straße' output='STRASSE' status=ok",
        ),
    )


def _context_conflicts() -> tuple[RawResidualObservation, ...]:
    return (
        RawResidualObservation(
            "literal-ja",
            "japanese",
            'mode=verbatim input="keep lower" output="keep lower" status=ok',
        ),
        RawResidualObservation(
            "literal-tool",
            "tool_trace",
            "verbatim tool input='raw command' output='raw command' status=ok",
        ),
    )


def run() -> dict[str, object]:
    training = _raw_training_stream()
    clusters = induce_raw_primitive_clusters(training)
    uppercase = next(row for row in clusters if row.primitive.offset == -32)
    lowercase = next(row for row in clusters if row.primitive.offset == 32)

    expected_upper = {
        "upper-ja",
        "upper-code",
        "upper-tool",
        "upper-test",
    }
    expected_lower = {
        "lower-code",
        "lower-tool",
        "lower-dialogue",
    }
    clustered = set(uppercase.support_observations) | set(lowercase.support_observations)
    clustering_accuracy = (
        len(set(uppercase.support_observations) & expected_upper)
        + len(set(lowercase.support_observations) & expected_lower)
    ) / (len(expected_upper) + len(expected_lower))

    novel = _novel_modality()
    shifted = _unicode_shift()
    conflicts = _context_conflicts()
    upper_training = tuple(
        row for row in training if row.identifier in expected_upper
    )

    library = VersionedPrimitiveLibrary(
        uppercase.primitive,
        reason="cross-channel raw residual cluster",
    )
    before_shift = raw_primitive_accuracy(library.active.primitive, shifted)
    extension = propose_residual_extension(library.active.primitive, shifted)
    extension_decision = library.stage(
        extension,
        upper_training + shifted,
        reason="Unicode residual extension",
        expected_future_calls=100,
    )

    overbroad_decision = library.stage(
        IdentityPrimitive(),
        upper_training + shifted + conflicts,
        reason="overbroad identity update",
        expected_future_calls=100,
    )
    bypass_token = learn_bypass_token(upper_training + shifted, conflicts)
    contextual = ContextualBypassPrimitive(library.active.primitive, bypass_token)
    split_decision = library.stage(
        contextual,
        upper_training + shifted + conflicts,
        reason="context-conditioned representation split",
        expected_future_calls=100,
    )

    final_evidence = upper_training + shifted + conflicts
    cluster_rows = [
        {
            "identifier": row.identifier,
            "primitive": row.primitive.render(),
            "support_observations": list(row.support_observations),
            "support_channels": list(row.support_channels),
            "description_bits": row.description_bits,
            "false_matching_pairs": row.false_matching_pairs,
            "normalized_gain_bits": row.normalized_gain_bits,
        }
        for row in clusters
    ]
    version_rows = [
        {
            "version": row.version,
            "parent_version": row.parent_version,
            "reason": row.reason,
            "kind": row.primitive.kind,
            "description_bits": row.description_bits,
            "evidence_ids": list(row.evidence_ids),
            "render": row.primitive.render(),
        }
        for row in library.versions
    ]

    return {
        "raw_grounding": {
            "observations": len(training),
            "channels": len({row.channel for row in training}),
            "task_family_labels_supplied": False,
            "aligned_examples_supplied": False,
            "message_record_boundaries_supplied": True,
            "clusters": cluster_rows,
            "cluster_count": len(clusters),
            "cluster_assignment_accuracy": clustering_accuracy,
            "noise_observation_clustered": "noise-replacement" in clustered,
            "novel_modality_accuracy": raw_primitive_accuracy(
                uppercase.primitive,
                novel,
            ),
        },
        "versioning": {
            "unicode_accuracy_before_extension": before_shift,
            "extension": asdict(extension_decision),
            "extension_replacements": [list(row) for row in extension.replacements],
            "overbroad_update": asdict(overbroad_decision),
            "learned_bypass_token": bypass_token,
            "context_split": asdict(split_decision),
            "versions": version_rows,
            "active_version": library.active.version,
            "rejected_update_count": len(library.rejected_decisions),
            "final_combined_accuracy": raw_primitive_accuracy(
                library.active.primitive,
                final_evidence,
            ),
        },
        "verdict": {
            "phase11d_success": (
                len(clusters) == 2
                and clustering_accuracy == 1.0
                and "noise-replacement" not in clustered
                and raw_primitive_accuracy(uppercase.primitive, novel) == 1.0
                and before_shift == 0.0
                and extension_decision.accepted
                and overbroad_decision.rolled_back
                and split_decision.accepted
                and raw_primitive_accuracy(library.active.primitive, final_evidence)
                == 1.0
            ),
            "new_domain_specific_solver_code": 0,
            "raw_task_family_boundaries_removed": True,
            "open_ended_grounding_achieved": False,
            "stage_c_score_changed": False,
        },
        "limitations": [
            "individual message/log record boundaries and channel metadata are still supplied",
            "quoted or backticked spans provide a strong generic extraction cue",
            "the latent candidate language is limited to aligned codepoint offsets, residual replacements, and one lexical context guard",
            "the experiment contains only two reusable transformation clusters and one distractor",
            "Unicode residual corrections are exact replacements rather than a learned general Unicode case theory",
            "the context split relies on a repeated verbatim token and does not solve arbitrary pragmatic scope",
            "all evidence is synthetic and does not establish open-domain language grounding",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    grounding = payload["raw_grounding"]
    versioning = payload["versioning"]
    lines = [
        "# Phase 11d results: raw cross-modal primitive grounding and versioning",
        "",
        "The learner receives raw Japanese, code diffs, tool traces, dialogue, and test",
        "logs without task-family labels or pre-aligned StringTransformExample rows.",
        "",
        "## Raw grounding",
        "",
        f"- observations: **{grounding['observations']}**",
        f"- channels: **{grounding['channels']}**",
        f"- discovered clusters: **{grounding['cluster_count']}**",
        f"- cluster assignment accuracy: **{grounding['cluster_assignment_accuracy']:.1%}**",
        f"- unrelated replacement clustered: **{grounding['noise_observation_clustered']}**",
        f"- novel modality accuracy: **{grounding['novel_modality_accuracy']:.1%}**",
        "",
        "| cluster | primitive | support records | channels | bits |",
        "|---|---|---:|---:|---:|",
    ]
    for row in grounding["clusters"]:
        primitive = row["primitive"]
        lines.append(
            f"| {row['identifier']} | offset {primitive['offset']} over "
            f"{primitive['lower_codepoint']}–{primitive['upper_codepoint']} | "
            f"{len(row['support_observations'])} | {len(row['support_channels'])} | "
            f"{row['description_bits']:,} |"
        )
    lines.extend(
        [
            "",
            "## Versioned residual repair",
            "",
            f"- Unicode accuracy before extension: **{versioning['unicode_accuracy_before_extension']:.1%}**",
            f"- Unicode extension accepted: **{versioning['extension']['accepted']}**",
            f"- overbroad identity update rolled back: **{versioning['overbroad_update']['rolled_back']}**",
            f"- learned context guard: **{versioning['learned_bypass_token']}**",
            f"- context split accepted: **{versioning['context_split']['accepted']}**",
            f"- active version: **v{versioning['active_version']}**",
            f"- final combined accuracy: **{versioning['final_combined_accuracy']:.1%}**",
            "",
            "This removes task-family labels, but not all supervision: record boundaries,",
            "quoted spans, channel metadata, and a bounded residual meta-grammar remain.",
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
    (output / "phase11d.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase11d.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
