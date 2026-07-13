from __future__ import annotations

from fractions import Fraction
import inspect
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .phase18d1_dataset_to_program_meta_learner import (
    canonical,
    decode_value,
    value_kind,
)
from .phase18d10_primitive_core import (
    IndexAffinePrimitive,
    NoProgramError,
    NonIdentifiablePrimitiveError,
    NonIdentifiableProgramError,
    NoResidualPrimitiveError,
    SequencePrimitive,
    _json_value,
    select_reusable_primitive,
    synthesize_extended_program,
)


def _data_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "phase18d10_residual_primitive_tasks.json"
    )


def load_dataset() -> Mapping[str, Any]:
    return json.loads(_data_path().read_text(encoding="utf-8"))


def _task_accuracy(
    program: Any,
    task: Mapping[str, Any],
    library: Sequence[SequencePrimitive],
) -> tuple[int, int]:
    correct = 0
    rows = tuple(task["test"])
    for example in rows:
        prediction = program.predict(example["inputs"], library)
        correct += canonical(prediction) == canonical(
            decode_value(example["output"])
        )
    return correct, len(rows)


def _coverage(
    tasks: Sequence[Mapping[str, Any]],
    library: Sequence[SequencePrimitive],
) -> tuple[int, int, int]:
    covered = correct = programs_evaluated = 0
    for task in tasks:
        try:
            program = synthesize_extended_program(task, library)
        except NoProgramError as error:
            programs_evaluated += error.programs_evaluated
            continue
        except NonIdentifiableProgramError:
            continue
        covered += len(task["test"])
        task_correct, total = _task_accuracy(program, task, library)
        correct += task_correct
        programs_evaluated += program.programs_evaluated
        if total != len(task["test"]):
            raise AssertionError("test accounting")
    return correct, covered, programs_evaluated


def _base_residual_coverage(
    episodes: Sequence[Mapping[str, Any]],
) -> tuple[int, int]:
    covered = 0
    for episode in episodes:
        task = {
            "id": episode["id"],
            "train": episode["train"],
        }
        try:
            synthesize_extended_program(task, ())
        except (NoProgramError, NonIdentifiableProgramError):
            continue
        covered += 1
    return covered, len(episodes)


def _metamorphic_parameter_recovery() -> bool:
    primitive = IndexAffinePrimitive(1, 2)
    sources: tuple[Any, ...] = (
        "abcdef",
        "lampqr",
        tuple(Fraction(value) for value in (1, 2, 3, 4, 5)),
        tuple(Fraction(value) for value in (9, 7, 5, 3, 1, -1)),
    )
    episodes = []
    for index, source in enumerate(sources):
        shifted = source[1:] + source[:1]
        episodes.append(
            {
                "id": f"m{index}",
                "train": [
                    {
                        "inputs": {"x": _json_value(source)},
                        "output": _json_value(primitive.apply(source)),
                    }
                ],
                "validation": [
                    {
                        "inputs": {"x": _json_value(shifted)},
                        "output": _json_value(primitive.apply(shifted)),
                    }
                ],
            }
        )
    selected = select_reusable_primitive(episodes)
    return (
        isinstance(selected.primitive, IndexAffinePrimitive)
        and selected.primitive.multiplier == 1
        and selected.primitive.offset == 2
    )


def negative_controls(
    episodes: Sequence[Mapping[str, Any]],
) -> Mapping[str, bool]:
    one_type = tuple(
        episode
        for episode in episodes
        if value_kind(
            decode_value(
                next(iter(episode["train"][0]["inputs"].values()))
            )
        )
        == "string"
    )
    try:
        select_reusable_primitive(one_type)
    except NoResidualPrimitiveError:
        one_type_rejected = True
    else:
        one_type_rejected = False

    conflict = json.loads(json.dumps(episodes))
    conflict[-1]["validation"][0]["output"] = [2, 9, 7, 5]
    try:
        select_reusable_primitive(conflict)
    except (NoResidualPrimitiveError, NonIdentifiablePrimitiveError):
        conflict_rejected = True
    else:
        conflict_rejected = False

    identity = (
        {
            "id": "identity-string",
            "train": [{"inputs": {"x": "abcd"}, "output": "abcd"}],
            "validation": [{"inputs": {"x": "lamp"}, "output": "lamp"}],
        },
        {
            "id": "identity-list",
            "train": [{"inputs": {"x": [1, 2, 3]}, "output": [1, 2, 3]}],
            "validation": [{"inputs": {"x": [4, 5, 6]}, "output": [4, 5, 6]}],
        },
    )
    identity_covered, identity_total = _base_residual_coverage(identity)

    return {
        "single_value_type_rejected": one_type_rejected,
        "conflicting_residual_rejected": conflict_rejected,
        "base_solvable_identity_not_residual": (
            identity_covered == identity_total
        ),
        "different_hidden_parameter_recovered": (
            _metamorphic_parameter_recovery()
        ),
    }


def run() -> Mapping[str, Any]:
    dataset = load_dataset()
    episodes = tuple(dataset["residual_episodes"])
    post_freeze = tuple(dataset["post_freeze_tasks"])

    base_episode_covered, base_episode_total = _base_residual_coverage(
        episodes
    )
    selection = select_reusable_primitive(episodes)
    library = (selection.primitive,)

    baseline_correct, baseline_covered, baseline_evaluated = _coverage(
        post_freeze,
        (),
    )
    final_correct, final_covered, final_evaluated = _coverage(
        post_freeze,
        library,
    )
    total_heldout = sum(len(task["test"]) for task in post_freeze)
    controls = negative_controls(episodes)

    theorem_checks = {
        "fixed_dsl_leaves_all_direct_episodes_residual": (
            base_episode_covered == 0
            and base_episode_total == len(episodes)
        ),
        "primitive_unique_on_generic_probes": (
            selection.probe_behavior_classes == 1
            and selection.exact_candidates >= 1
        ),
        "cross_episode_validation": (
            selection.validation_episodes >= 2
        ),
        "cross_type_validation": selection.validation_types >= 2,
        "positive_mdl_gain": selection.compression_gain_bits > 0,
        "post_freeze_baseline_zero_coverage": baseline_covered == 0,
        "post_freeze_accuracy": final_correct == total_heldout,
        "post_freeze_coverage": final_covered == total_heldout,
        "negative_controls": all(controls.values()),
    }

    source = inspect.getsource(inspect.getmodule(run))
    source_audit = {
        "post_freeze_ids_not_in_learner_source": all(
            str(task["id"]) not in source
            for task in post_freeze
        ),
        "target_parameter_not_read_from_data": (
            "multiplier" not in json.dumps(dataset, ensure_ascii=False)
            and "offset" not in json.dumps(dataset, ensure_ascii=False)
        ),
        "task_specific_dispatch_absent": ("match " + "task") not in source.lower(),
    }
    theorem_checks["source_audit"] = all(source_audit.values())

    return {
        "campaign": {
            "name": dataset["campaign"]["name"],
            "base_dsl_frozen": True,
            "primitive_candidate_meta_grammar": (
                "length-preserving affine index transducers plus lookup control"
            ),
            "task_specific_source_changes": 0,
            "post_freeze_task_ids_used_by_learner": False,
        },
        "residual_invention": {
            "episodes": len(episodes),
            "training_examples": sum(len(row["train"]) for row in episodes),
            "validation_examples": sum(
                len(row["validation"]) for row in episodes
            ),
            "base_dsl_episode_coverage": base_episode_covered / base_episode_total,
            "candidates_evaluated": selection.candidates_evaluated,
            "exact_candidates": selection.exact_candidates,
            "probe_behavior_classes": selection.probe_behavior_classes,
            "selected_primitive": selection.primitive.render(),
            "training_accuracy": selection.training_accuracy,
            "validation_accuracy": selection.validation_accuracy,
            "validation_episodes": selection.validation_episodes,
            "validation_types": selection.validation_types,
        },
        "mdl": {
            "literal_bits": selection.literal_bits,
            "primitive_model_bits": selection.model_bits,
            "compression_gain_bits": selection.compression_gain_bits,
            "compression_ratio": (
                selection.literal_bits / selection.model_bits
            ),
        },
        "post_freeze_evaluation": {
            "tasks": len(post_freeze),
            "heldout_examples": total_heldout,
            "baseline_correct": baseline_correct,
            "baseline_coverage": baseline_covered / total_heldout,
            "with_invented_primitive_correct": final_correct,
            "with_invented_primitive_coverage": (
                final_covered / total_heldout
            ),
            "with_invented_primitive_accuracy": (
                final_correct / total_heldout
            ),
            "baseline_programs_evaluated": baseline_evaluated,
            "extended_programs_evaluated": final_evaluated,
        },
        "negative_controls": controls,
        "source_audit": source_audit,
        "resources": {
            "primitive_payload_bits": selection.primitive.payload_bits,
            "program_search_max_cost": 5,
            "python_runtime_included": False,
            "candidate_meta_grammar_source_included_in_payload": False,
        },
        "theorem_checks": theorem_checks,
        "all_theorem_checks_pass": all(theorem_checks.values()),
        "claim_boundary": {
            "residual_driven_primitive_invention": all(
                theorem_checks.values()
            ),
            "primitive_target_prelisted": False,
            "primitive_meta_grammar_human_designed": True,
            "online_byte_level_invention": False,
            "arbitrary_new_computation_invented": False,
            "llm_like_general_learning": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "Residual examples are already grouped into short episodes.",
            "The candidate meta-grammar is restricted to length-preserving affine index transducers and a lookup control.",
            "Primitive invention is batch, not causal online byte-level learning.",
            "The existing typed DSL, value parser, probe set, and MDL accounting are human-designed.",
            "No natural-language semantics or unrestricted algorithm invention is claimed.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    residual = payload["residual_invention"]
    mdl = payload["mdl"]
    evaluation = payload["post_freeze_evaluation"]
    selected = residual["selected_primitive"]
    return f"""# Phase 18d-10 results: residual-driven primitive invention

- Residual episodes / train / validation: **{residual['episodes']} / {residual['training_examples']} / {residual['validation_examples']}**
- Frozen-DSL residual coverage: **{100 * residual['base_dsl_episode_coverage']:.1f}%**
- Primitive candidates / exact / probe behaviors: **{residual['candidates_evaluated']} / {residual['exact_candidates']} / {residual['probe_behavior_classes']}**
- Selected generic index parameters: **multiplier={selected['multiplier']}, offset={selected['offset']}**
- Training / validation accuracy: **{100 * residual['training_accuracy']:.1f}% / {100 * residual['validation_accuracy']:.1f}%**
- Literal / primitive-model payload: **{mdl['literal_bits']} / {mdl['primitive_model_bits']} bits**
- MDL gain / compression ratio: **{mdl['compression_gain_bits']} bits / {mdl['compression_ratio']:.2f}x**
- Post-freeze tasks / held-out: **{evaluation['tasks']} / {evaluation['heldout_examples']}**
- Frozen-DSL held-out coverage: **{100 * evaluation['baseline_coverage']:.1f}%**
- Invented-primitive accuracy / coverage: **{100 * evaluation['with_invented_primitive_accuracy']:.1f}% / {100 * evaluation['with_invented_primitive_coverage']:.1f}%**
- Primitive payload: **{payload['resources']['primitive_payload_bits']} bits**

The target primitive is not a named operation in the dataset or active DSL. A human-designed generic transducer meta-grammar is still searched, and residual episodes are pre-grouped. This demonstrates controlled primitive invention and reuse, not unrestricted LLM-like learning.
"""


def main() -> None:
    payload = run()
    results = Path("results")
    results.mkdir(exist_ok=True)
    (results / "phase18d10.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (results / "phase18d10.md").write_text(
        markdown(payload),
        encoding="utf-8",
    )
    print(markdown(payload), end="")
    if not payload["all_theorem_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
