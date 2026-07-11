from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .concept_first_intelligence import (
    ConceptMachine,
    Interaction,
    LanguageExample,
    WorldState,
    codec_accuracy,
    grounding_lower_bound_bits,
    induce_concepts,
    induce_language_codec,
    language_first_description_bits,
    permutation_equivalent_groundings,
)


RELATION_ACTIONS = {
    "location": ("move_a", "move_b", "move_c"),
    "message": ("emit_a", "emit_b", "emit_c"),
    "owner": ("transfer_a", "transfer_b", "transfer_c"),
    "status": ("verify_a", "verify_b", "verify_c"),
}


def _interaction(
    action_token: str,
    relation: str,
    subject: str,
    value: str,
) -> Interaction:
    before = WorldState.from_dict(
        {
            ("location", subject): "old_place",
            ("message", subject): "none",
            ("owner", subject): "old_owner",
            ("status", subject): "UNKNOWN",
        }
    )
    after = before.as_dict()
    after[(relation, subject)] = value
    return Interaction(
        action_token,
        (subject, value),
        before,
        WorldState.from_dict(after),
    )


def world_interactions() -> list[Interaction]:
    interactions: list[Interaction] = []
    for relation, actions in RELATION_ACTIONS.items():
        for action_index, action_token in enumerate(actions):
            for example_index in range(4):
                interactions.append(
                    _interaction(
                        action_token,
                        relation,
                        f"subject_{action_index}_{example_index}",
                        f"value_{action_index}_{example_index}",
                    )
                )
    return interactions


def _partition_recovery(machine: ConceptMachine) -> float:
    actions = sorted(machine.action_to_concept)
    correct = 0
    comparisons = 0
    relation_by_action = {
        action: relation
        for relation, relation_actions in RELATION_ACTIONS.items()
        for action in relation_actions
    }
    for left_index, left in enumerate(actions):
        for right in actions[left_index + 1 :]:
            expected_same = relation_by_action[left] == relation_by_action[right]
            observed_same = (
                machine.action_to_concept[left]
                == machine.action_to_concept[right]
            )
            correct += int(expected_same == observed_same)
            comparisons += 1
    return correct / comparisons


def _experience_bits(interactions: Iterable[Interaction]) -> int:
    payload = [
        {
            "action": item.action_token,
            "arguments": list(item.arguments),
            "before": list(item.before.facts),
            "after": list(item.after.facts),
            "reward": item.reward,
        }
        for item in interactions
    ]
    return len(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ) * 8


def _concept_ids(machine: ConceptMachine) -> dict[str, str]:
    return {schema.relation: schema.identifier for schema in machine.schemas}


def _language_examples(
    specification: dict[str, dict[str, list[str]]],
    concept_ids: dict[str, str],
) -> list[LanguageExample]:
    return [
        LanguageExample(language, surface, concept_ids[relation])
        for relation, language_surfaces in specification.items()
        for language, surfaces in language_surfaces.items()
        for surface in surfaces
    ]


TRAINING_SPECIFICATION = {
    "location": {
        "ja": ["対象を移動してください", "物体を移動する"],
        "en": ["move the object", "move item now"],
        "tool": ["move_item", "move_target"],
    },
    "message": {
        "ja": ["結果を報告してください", "完了を報告する"],
        "en": ["report the result", "report completion"],
        "tool": ["emit_report", "send_report"],
    },
    "owner": {
        "ja": ["所有者を譲渡してください", "担当を譲渡する"],
        "en": ["transfer ownership", "transfer assignee"],
        "tool": ["transfer_owner", "transfer_assignee"],
    },
    "status": {
        "ja": ["状態を検証してください", "テストを検証する"],
        "en": ["verify status", "verify test"],
        "tool": ["verify_status", "verify_test"],
    },
}


HELDOUT_SPECIFICATION = {
    "location": {
        "ja": ["すぐに対象を移動して"],
        "en": ["please move object"],
        "tool": ["move_item_now"],
    },
    "message": {
        "ja": ["結果を報告して"],
        "en": ["please report result"],
        "tool": ["emit_report_now"],
    },
    "owner": {
        "ja": ["所有権を譲渡して"],
        "en": ["please transfer owner"],
        "tool": ["transfer_owner_now"],
    },
    "status": {
        "ja": ["テストを検証して"],
        "en": ["please verify status"],
        "tool": ["verify_status_now"],
    },
}


NEW_LANGUAGE_CALIBRATION = {
    "location": {"luma": ["nava target", "nava object"]},
    "message": {"luma": ["sora result", "sora completion"]},
    "owner": {"luma": ["tela owner", "tela assignee"]},
    "status": {"luma": ["veta status", "veta test"]},
}


NEW_LANGUAGE_HELDOUT = {
    "location": {"luma": ["please nava item"]},
    "message": {"luma": ["please sora result"]},
    "owner": {"luma": ["please tela owner"]},
    "status": {"luma": ["please veta test"]},
}


def output_templates(
    concept_ids: dict[str, str],
) -> dict[tuple[str, str], str]:
    per_relation = {
        "location": {
            "ja": "{0}を{1}へ移動する",
            "en": "move {0} to {1}",
            "tool": "set_location({0},{1})",
            "luma": "nava {0} {1}",
        },
        "message": {
            "ja": "{0}へ{1}を送信する",
            "en": "send {1} to {0}",
            "tool": "emit({0},{1})",
            "luma": "sora {0} {1}",
        },
        "owner": {
            "ja": "{0}の所有者を{1}にする",
            "en": "assign {0} to {1}",
            "tool": "set_owner({0},{1})",
            "luma": "tela {0} {1}",
        },
        "status": {
            "ja": "{0}の状態を{1}にする",
            "en": "set {0} status to {1}",
            "tool": "set_status({0},{1})",
            "luma": "veta {0} {1}",
        },
    }
    return {
        (language, concept_ids[relation]): template
        for relation, language_templates in per_relation.items()
        for language, template in language_templates.items()
    }


def _planning_accuracy(machine: ConceptMachine) -> tuple[float, int]:
    trials = 0
    correct = 0
    for schema in machine.schemas:
        for subject_index in range(16):
            for value_index in range(16):
                subject = f"novel_subject_{subject_index}"
                value = f"novel_value_{value_index}"
                current = WorldState()
                target = WorldState.from_dict(
                    {(schema.relation, subject): value}
                )
                plan = machine.plan(current, target)
                state = current
                for concept_id, arguments in plan:
                    state = machine.execute(concept_id, arguments, state)
                correct += int(state == target)
                trials += 1
    return correct / trials, trials


def run() -> dict[str, object]:
    interactions = world_interactions()
    machine = induce_concepts(interactions)
    concept_ids = _concept_ids(machine)
    templates = output_templates(concept_ids)

    training = _language_examples(TRAINING_SPECIFICATION, concept_ids)
    heldout = _language_examples(HELDOUT_SPECIFICATION, concept_ids)
    base_templates = {
        key: value
        for key, value in templates.items()
        if key[0] in {"ja", "en", "tool"}
    }
    codec = induce_language_codec(
        training,
        base_templates,
        minimum_support=2,
    )

    new_language_calibration = _language_examples(
        NEW_LANGUAGE_CALIBRATION,
        concept_ids,
    )
    new_language_heldout = _language_examples(
        NEW_LANGUAGE_HELDOUT,
        concept_ids,
    )
    expanded_codec = induce_language_codec(
        training + new_language_calibration,
        templates,
        minimum_support=2,
    )

    concept_first_bits = machine.description_bits + codec.description_bits
    schema_by_id = {
        schema.identifier: schema for schema in machine.schemas
    }
    language_first_bits = language_first_description_bits(
        training,
        schema_by_id,
        base_templates,
    )
    planning_accuracy, planning_trials = _planning_accuracy(machine)
    experience_bits = _experience_bits(interactions)

    rendered = {
        language: expanded_codec.render(
            language,
            concept_ids["location"],
            ("box_A", "warehouse"),
        )
        for language in ("ja", "en", "tool", "luma")
    }

    return {
        "world_concept_induction": {
            "interactions": len(interactions),
            "opaque_surface_actions": len(machine.action_to_concept),
            "induced_concepts": len(machine.schemas),
            "pairwise_partition_recovery": _partition_recovery(machine),
            "experience_bits": experience_bits,
            "concept_machine_bits": machine.description_bits,
            "experience_to_machine_ratio": (
                experience_bits / machine.description_bits
            ),
            "schemas": [
                {
                    "id": schema.identifier,
                    "relation": schema.relation,
                    "subject_argument": schema.subject_argument,
                    "value_argument": schema.value_argument,
                }
                for schema in machine.schemas
            ],
        },
        "language_as_codec": {
            "training_examples": len(training),
            "selected_rules": len(codec.rules),
            "heldout_examples": len(heldout),
            "heldout_accuracy": codec_accuracy(codec, heldout),
            "codec_bits": codec.description_bits,
            "rendered_same_concept": rendered,
        },
        "language_first_comparison": {
            "concept_first_total_bits": concept_first_bits,
            "language_first_total_bits": language_first_bits,
            "language_first_to_concept_first_ratio": (
                language_first_bits / concept_first_bits
            ),
            "note": (
                "the language-first payload repeats transition schema and "
                "output template for every surface program; the concept-first "
                "payload stores world schemas once and language bindings "
                "separately"
            ),
        },
        "new_language": {
            "calibration_interactions": len(new_language_calibration),
            "heldout_examples": len(new_language_heldout),
            "heldout_accuracy": codec_accuracy(
                expanded_codec,
                new_language_heldout,
            ),
            "additional_bits": (
                expanded_codec.description_bits - codec.description_bits
            ),
        },
        "language_free_planning": {
            "trials": planning_trials,
            "accuracy": planning_accuracy,
            "language_feature_reads": 0,
        },
        "identifiability": {
            "concepts": len(machine.schemas),
            "equivalent_text_only_groundings": (
                permutation_equivalent_groundings(len(machine.schemas))
            ),
            "minimum_external_grounding_bits": grounding_lower_bound_bits(
                len(machine.schemas)
            ),
            "interpretation": (
                "text-only statistics are invariant under a permutation of "
                "latent concept names; interaction, perception, reward, or "
                "trusted demonstration must break the symmetry"
            ),
        },
        "stage_c": {
            "readiness_points": 7,
            "maximum_points": 24,
            "changed_by_this_phase": 0,
            "reason": (
                "this is a synthetic architecture experiment, not a public "
                "open-domain benchmark"
            ),
        },
        "limitations": [
            "the experiment supplies a finite state relation vocabulary",
            "each interaction changes exactly one fact",
            "arguments are already segmented before language grounding",
            "near held-out language shares lexical roots with calibration examples",
            "language carries abstract and social knowledge that cannot always be recovered from local physical interaction",
            "no finite learner can eliminate unavoidable identification, observation, and search costs",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    world = payload["world_concept_induction"]
    codec = payload["language_as_codec"]
    comparison = payload["language_first_comparison"]
    new_language = payload["new_language"]
    planning = payload["language_free_planning"]
    identifiability = payload["identifiability"]
    lines = [
        "# Phase 10c results: concept-first intelligence and language as a codec",
        "",
        "World concepts are induced from state transitions before language is attached.",
        "Language is then learned as a sparse bidirectional codec over the shared concepts.",
        "",
        "## Non-linguistic concept induction",
        "",
        f"- interactions: **{world['interactions']}**",
        f"- opaque surface actions: **{world['opaque_surface_actions']}**",
        f"- induced concepts: **{world['induced_concepts']}**",
        f"- pairwise partition recovery: **{world['pairwise_partition_recovery']:.1%}**",
        f"- experience / concept-machine bits: **{world['experience_bits']:,} / {world['concept_machine_bits']:,}**",
        f"- compression ratio: **{world['experience_to_machine_ratio']:.2f}x**",
        "",
        "## Language as codec",
        "",
        f"- calibration examples: **{codec['training_examples']}**",
        f"- selected rules: **{codec['selected_rules']}**",
        f"- near held-out accuracy: **{codec['heldout_accuracy']:.1%}**",
        f"- codec bits: **{codec['codec_bits']:,}**",
        "",
        "## Language-first versus concept-first",
        "",
        f"- concept-first total: **{comparison['concept_first_total_bits']:,} bits**",
        f"- language-first repeated programs: **{comparison['language_first_total_bits']:,} bits**",
        f"- language-first / concept-first: **{comparison['language_first_to_concept_first_ratio']:.2f}x**",
        "",
        "## New language",
        "",
        f"- calibration interactions: **{new_language['calibration_interactions']}**",
        f"- held-out accuracy: **{new_language['heldout_accuracy']:.1%}**",
        f"- additional bits: **{new_language['additional_bits']:,}**",
        "",
        "## Language-free planning",
        "",
        f"- unseen target transitions: **{planning['trials']:,}**",
        f"- accuracy: **{planning['accuracy']:.1%}**",
        f"- language feature reads: **{planning['language_feature_reads']}**",
        "",
        "## Grounding lower bound",
        "",
        f"- text-only equivalent groundings: **{identifiability['equivalent_text_only_groundings']}**",
        f"- minimum symmetry-breaking evidence: **{identifiability['minimum_external_grounding_bits']:.3f} bits**",
        "",
        "This phase does not increase the Stage-C score because it is a synthetic",
        "architecture experiment rather than public open-domain evidence.",
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
    (output / "phase10c.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase10c.md").write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
