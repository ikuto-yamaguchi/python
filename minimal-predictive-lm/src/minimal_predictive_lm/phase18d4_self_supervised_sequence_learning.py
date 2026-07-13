from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .phase18d1_dataset_to_program_meta_learner import (
    EvaluationError,
    canonical,
    decode_value,
)
from .phase18d3_latent_task_partition import (
    LatentPartition,
    NoLatentPartitionError,
    NonIdentifiableRoutingError,
    discover_partition,
    route_from_support,
)


class InvalidSequenceError(ValueError):
    pass


def load_sequences(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).parents[2] / "data" / "phase18d4_self_supervised_sequences.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported sequence schema")
    return payload


def sequence_to_example(sequence: Sequence[Any]) -> dict[str, Any]:
    if len(sequence) < 2:
        raise InvalidSequenceError("a prediction sequence needs a prefix and next value")
    return {
        "inputs": {f"position_{index}": value for index, value in enumerate(sequence[:-1])},
        "output": sequence[-1],
    }


def prefix_to_inputs(prefix: Sequence[Any]) -> dict[str, Any]:
    if not prefix:
        raise InvalidSequenceError("empty prefix")
    return {f"position_{index}": value for index, value in enumerate(prefix)}


def learn_from_sequences(
    sequences: Sequence[Sequence[Any]],
    *,
    max_cost: int = 3,
    minimum_support: int = 5,
) -> LatentPartition:
    examples = tuple(sequence_to_example(sequence) for sequence in sequences)
    return discover_partition(
        examples,
        max_cost=max_cost,
        minimum_support=minimum_support,
    )


def route_from_sequence_support(
    partition: LatentPartition,
    support_sequences: Sequence[Sequence[Any]],
):
    return route_from_support(
        partition,
        tuple(sequence_to_example(sequence) for sequence in support_sequences),
    )


def evaluate_masked_queries(
    partition: LatentPartition,
    episodes: Sequence[Mapping[str, Any]],
) -> tuple[int, int, int]:
    correct = covered = total = 0
    for episode in episodes:
        total += len(episode["queries"])
        try:
            program = route_from_sequence_support(partition, episode["support"])
        except (InvalidSequenceError, NonIdentifiableRoutingError):
            continue
        covered += len(episode["queries"])
        for query in episode["queries"]:
            try:
                predicted = program.predict(prefix_to_inputs(query["prefix"]))
            except (InvalidSequenceError, EvaluationError):
                continue
            correct += canonical(predicted) == canonical(decode_value(query["target"]))
    return correct, covered, total


def audit_sequence_clusters(
    partition: LatentPartition,
    audit_labels: Sequence[str],
) -> bool:
    labels_seen: set[str] = set()
    for program in partition.programs:
        labels = {str(audit_labels[index]) for index in program.covered_indices}
        if len(labels) != 1:
            return False
        labels_seen.update(labels)
    return labels_seen == set(map(str, audit_labels))


def _failure_controls(final: LatentPartition) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for sequence in ((), (1,)):
        try:
            sequence_to_example(sequence)
        except InvalidSequenceError:
            results[f"short_sequence_{len(sequence)}"] = True
        else:
            results[f"short_sequence_{len(sequence)}"] = False

    try:
        route_from_sequence_support(final, ((0, 0, 0),))
    except NonIdentifiableRoutingError:
        results["ambiguous_prefix_context_abstains"] = True
    else:
        results["ambiguous_prefix_context_abstains"] = False

    try:
        learn_from_sequences(((1, 2, 3), (2, 3, 5), (3, 4, 7), (4, 5, 9)))
    except NoLatentPartitionError:
        results["subminimum_pattern_abstains"] = True
    else:
        results["subminimum_pattern_abstains"] = False
    return results


def run() -> dict[str, Any]:
    payload = load_sequences()
    initial_sequences = tuple(tuple(row) for row in payload["sequences"])
    appended_sequences = tuple(tuple(row) for row in payload["post_freeze_sequences"])

    initial = learn_from_sequences(initial_sequences)
    initial_correct, initial_covered, initial_total = evaluate_masked_queries(
        initial, payload["episodes"]
    )
    final_sequences = initial_sequences + appended_sequences
    final = learn_from_sequences(final_sequences)
    final_episodes = tuple(payload["episodes"]) + tuple(payload["post_freeze_episodes"])
    final_correct, final_covered, final_total = evaluate_masked_queries(
        final, final_episodes
    )

    old_unchanged = set(initial.fingerprint()).issubset(set(final.fingerprint()))
    reversed_partition = learn_from_sequences(tuple(reversed(initial_sequences)))
    controls = _failure_controls(final)
    data_path = Path(__file__).parents[2] / "data" / "phase18d4_self_supervised_sequences.json"
    raw_data = data_path.read_text(encoding="utf-8")
    source = inspect.getsource(inspect.getmodule(run))
    audit_names = tuple(payload["audit_clusters"]) + tuple(payload["post_freeze_audit_clusters"])
    audit_names_absent = all(name not in source for name in audit_names)

    checks = {
        "training_has_no_inputs_key": '"inputs"' not in raw_data,
        "training_has_no_output_key": '"output"' not in raw_data,
        "training_has_no_task_id_key": '"id"' not in raw_data,
        "initial_program_count": len(initial.programs) == 7,
        "final_program_count": len(final.programs) == 8,
        "initial_audit_partition": audit_sequence_clusters(initial, payload["audit_clusters"]),
        "final_audit_partition": audit_sequence_clusters(final, audit_names),
        "initial_masked_accuracy": initial_correct == initial_total,
        "initial_masked_coverage": initial_covered == initial_total,
        "final_masked_accuracy": final_correct == final_total,
        "final_masked_coverage": final_covered == final_total,
        "old_programs_unchanged": old_unchanged,
        "record_order_invariance": initial.fingerprint() == reversed_partition.fingerprint(),
        "audit_names_absent_from_source": audit_names_absent,
        "failure_controls": all(controls.values()),
    }

    return {
        "campaign": {
            "name": "phase18d4-self-supervised-sequence-learning-c1",
            "training_objective": "predict final sequence value from prefix",
            "explicit_input_output_records": False,
            "explicit_task_ids": False,
            "explicit_task_count": False,
            "source_changes_for_appended_behavior": 0,
        },
        "induction": {
            "initial_sequences": len(initial_sequences),
            "initial_latent_programs": len(initial.programs),
            "appended_sequences": len(appended_sequences),
            "final_latent_programs": len(final.programs),
            "final_programs": [program.expression.render() for program in final.programs],
        },
        "evaluation": {
            "initial_correct": initial_correct,
            "initial_covered": initial_covered,
            "initial_total": initial_total,
            "final_correct": final_correct,
            "final_covered": final_covered,
            "final_total": final_total,
        },
        "continual_learning": {
            "old_programs_unchanged": old_unchanged,
            "new_behaviors_from_appended_sequences": len(final.programs) - len(initial.programs),
        },
        "controls": controls,
        "resources": {
            "final_expressions_evaluated": final.stats.expressions_evaluated,
            "final_candidate_behaviors": final.stats.candidate_behaviors,
            "final_exact_cover_nodes": final.stats.exact_cover_nodes,
            "learned_payload_bits": sum(program.payload_bits for program in final.programs),
            "source_bytes": len(Path(__file__).read_bytes()),
            "data_bytes": len(data_path.read_bytes()),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "self_supervised_next_value_program_induction": all(checks.values()),
            "raw_token_language_modeling": False,
            "unsegmented_document_learning": False,
            "autonomous_tokenization": False,
            "open_ended_world_knowledge": False,
            "llm_like_general_learning": False,
        },
        "limitations": [
            "Training records are already segmented typed value sequences.",
            "The final position is fixed as the prediction target, analogous to a next-element objective.",
            "The type system, primitive DSL, partition algorithm, and minimum support remain human-designed.",
            "A complete support sequence is still supplied for few-shot behavior routing.",
            "This is not byte/token prediction over natural documents.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18d-4 results: self-supervised sequence program learning

- Initial next-value sequences: **{induction['initial_sequences']}**
- Inferred initial programs: **{induction['initial_latent_programs']}**
- Appended sequences: **{induction['appended_sequences']}**
- Inferred final programs: **{induction['final_latent_programs']}**
- Initial masked predictions: **{evaluation['initial_correct']}/{evaluation['initial_total']}**
- Final masked predictions: **{evaluation['final_correct']}/{evaluation['final_total']}**
- Source changes for appended behavior: **{payload['campaign']['source_changes_for_appended_behavior']}**
- Old programs unchanged: **{payload['continual_learning']['old_programs_unchanged']}**
- Learned payload: **{resources['learned_payload_bits']} bits**

The learner received complete typed value sequences and learned to predict each final element from its prefix. No training record contained input/output fields, a task ID, or a declared task count. This is a controlled self-supervised next-value experiment, not raw-token language-model pretraining.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18d4.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path("results/phase18d4.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")


if __name__ == "__main__":
    main()
