from __future__ import annotations

from dataclasses import dataclass
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
    NonIdentifiableRoutingError,
)
from .phase18d4_self_supervised_sequence_learning import (
    audit_sequence_clusters,
    learn_from_sequences,
    prefix_to_inputs,
    route_from_sequence_support,
)


class RawGrammarError(ValueError):
    pass


class NonIdentifiableRawGrammarError(ValueError):
    pass


@dataclass(frozen=True)
class RawGrammar:
    record_separator: str
    field_separator: str
    sequences: tuple[tuple[Any, ...], ...]
    partition: LatentPartition
    candidates_tested: int
    valid_candidates: int

    def fingerprint(self) -> tuple[Any, ...]:
        return (
            self.record_separator,
            self.field_separator,
            self.partition.fingerprint(),
        )


def load_raw_stream(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).parents[2] / "data" / "phase18d5_continuous_raw_stream.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported raw-stream schema")
    return payload


def _delimiter_candidates(raw: str) -> tuple[str, ...]:
    # Candidate discovery does not know field/record roles. JSON quoting and a
    # numeric sign are lexical atom syntax, so they are excluded here.
    candidates = {
        character
        for index, character in enumerate(raw)
        if not character.isalnum()
        and not character.isspace()
        and character not in {'"', "'", "."}
        and not (
            character in {"-", "+"}
            and index + 1 < len(raw)
            and raw[index + 1].isdigit()
        )
    }
    return tuple(sorted(candidates))


def _parse_atom(text: str) -> Any:
    token = text.strip()
    if not token:
        raise RawGrammarError("empty atom")
    try:
        value = json.loads(token)
    except json.JSONDecodeError as exc:
        raise RawGrammarError(f"invalid atom: {token!r}") from exc
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise RawGrammarError("only integer and string atoms are supported")
    return value


def parse_record(text: str, field_separator: str, *, minimum_fields: int = 2) -> tuple[Any, ...]:
    fields = text.split(field_separator)
    if len(fields) < minimum_fields:
        raise RawGrammarError("record has too few fields")
    return tuple(_parse_atom(field) for field in fields)


def parse_raw_stream(
    raw: str,
    record_separator: str,
    field_separator: str,
) -> tuple[tuple[Any, ...], ...]:
    if record_separator == field_separator:
        raise RawGrammarError("separators must differ")
    records = raw.split(record_separator)
    if len(records) < 2 or any(not record.strip() for record in records):
        raise RawGrammarError("invalid record segmentation")
    sequences = tuple(parse_record(record, field_separator) for record in records)
    if any(len(sequence) > 4 for sequence in sequences):
        raise RawGrammarError("implausibly wide record")
    return sequences


def induce_raw_grammar(
    raw: str,
    *,
    minimum_support: int = 5,
    max_cost: int = 3,
) -> RawGrammar:
    symbols = _delimiter_candidates(raw)
    valid: list[tuple[tuple[int, int, int], str, str, tuple[tuple[Any, ...], ...], LatentPartition]] = []
    tested = 0
    for record_separator in symbols:
        for field_separator in symbols:
            if record_separator == field_separator:
                continue
            tested += 1
            try:
                sequences = parse_raw_stream(raw, record_separator, field_separator)
                partition = learn_from_sequences(
                    sequences,
                    max_cost=max_cost,
                    minimum_support=minimum_support,
                )
            except (RawGrammarError, ValueError):
                continue
            score = (
                len(partition.programs),
                sum(program.cost for program in partition.programs),
                -len(sequences),
            )
            valid.append((score, record_separator, field_separator, sequences, partition))

    if not valid:
        raise RawGrammarError(f"no valid delimiter grammar among {tested} candidates")
    best_score = min(row[0] for row in valid)
    best = [row for row in valid if row[0] == best_score]
    behavior_keys = {
        (row[1], row[2], row[4].fingerprint())
        for row in best
    }
    if len(behavior_keys) != 1:
        raise NonIdentifiableRawGrammarError(
            f"score={best_score}, optimum_grammars={len(behavior_keys)}"
        )
    _, record_separator, field_separator, sequences, partition = best[0]
    return RawGrammar(
        record_separator,
        field_separator,
        sequences,
        partition,
        tested,
        len(valid),
    )


def _parse_support(grammar: RawGrammar, raw_record: str) -> tuple[Any, ...]:
    return parse_record(raw_record, grammar.field_separator)


def _parse_prefix(grammar: RawGrammar, raw_prefix: str) -> tuple[Any, ...]:
    return parse_record(raw_prefix, grammar.field_separator, minimum_fields=1)


def evaluate_raw_episodes(
    grammar: RawGrammar,
    episodes: Sequence[Mapping[str, Any]],
) -> tuple[int, int, int]:
    correct = covered = total = 0
    for episode in episodes:
        total += len(episode["queries"])
        try:
            support = (_parse_support(grammar, episode["support"]),)
            program = route_from_sequence_support(grammar.partition, support)
        except (RawGrammarError, NonIdentifiableRoutingError):
            continue
        covered += len(episode["queries"])
        for query in episode["queries"]:
            try:
                prefix = _parse_prefix(grammar, query["prefix"])
                predicted = program.predict(prefix_to_inputs(prefix))
            except (RawGrammarError, EvaluationError):
                continue
            correct += canonical(predicted) == canonical(decode_value(query["target"]))
    return correct, covered, total


def _rename_delimiters(raw: str, record: str, field: str) -> str:
    return raw.replace(",", "\u0000").replace(";", record).replace("\u0000", field)


def _failure_controls(payload: Mapping[str, Any], grammar: RawGrammar) -> dict[str, bool]:
    results: dict[str, bool] = {}
    try:
        induce_raw_grammar("1,2,3,4,5")
    except RawGrammarError:
        results["one_delimiter_kind_abstains"] = True
    else:
        results["one_delimiter_kind_abstains"] = False

    malformed = payload["raw_stream"] + grammar.record_separator + "1" + grammar.field_separator
    try:
        induce_raw_grammar(malformed)
    except RawGrammarError:
        results["malformed_tail_abstains"] = True
    else:
        results["malformed_tail_abstains"] = False

    ambiguous_episode = ({"support": "0,0,0", "queries": [{"prefix": "2,3", "target": 0}]},)
    _, covered, total = evaluate_raw_episodes(grammar, ambiguous_episode)
    results["ambiguous_support_abstains"] = covered == 0 and total == 1
    return results


def run() -> dict[str, Any]:
    payload = load_raw_stream()
    initial = induce_raw_grammar(payload["raw_stream"])
    initial_correct, initial_covered, initial_total = evaluate_raw_episodes(
        initial, payload["episodes"]
    )

    combined_raw = payload["raw_stream"] + initial.record_separator + payload["post_freeze_raw"]
    final = induce_raw_grammar(combined_raw)
    all_episodes = tuple(payload["episodes"]) + tuple(payload["post_freeze_episodes"])
    final_correct, final_covered, final_total = evaluate_raw_episodes(final, all_episodes)
    old_unchanged = set(initial.partition.fingerprint()).issubset(
        set(final.partition.fingerprint())
    )

    records = payload["raw_stream"].split(initial.record_separator)
    reversed_raw = initial.record_separator.join(reversed(records))
    reversed_grammar = induce_raw_grammar(reversed_raw)
    renamed_raw = _rename_delimiters(payload["raw_stream"], "|", "~")
    renamed_grammar = induce_raw_grammar(renamed_raw)
    controls = _failure_controls(payload, final)
    source = inspect.getsource(inspect.getmodule(run))
    audit_names = tuple(payload["audit_clusters"]) + tuple(payload["post_freeze_audit_clusters"])

    checks = {
        "initial_separator_inferred": (initial.record_separator, initial.field_separator) == (";", ","),
        "renamed_separator_inferred": (renamed_grammar.record_separator, renamed_grammar.field_separator) == ("|", "~"),
        "initial_program_count": len(initial.partition.programs) == 7,
        "final_program_count": len(final.partition.programs) == 8,
        "initial_audit_partition": audit_sequence_clusters(initial.partition, payload["audit_clusters"]),
        "final_audit_partition": audit_sequence_clusters(final.partition, audit_names),
        "initial_accuracy": initial_correct == initial_total,
        "initial_coverage": initial_covered == initial_total,
        "final_accuracy": final_correct == final_total,
        "final_coverage": final_covered == final_total,
        "old_programs_unchanged": old_unchanged,
        "record_order_invariance": initial.partition.fingerprint() == reversed_grammar.partition.fingerprint(),
        "delimiter_rename_behavior_invariance": initial.partition.fingerprint() == renamed_grammar.partition.fingerprint(),
        "audit_names_absent_from_source": all(name not in source for name in audit_names),
        "failure_controls": all(controls.values()),
        "training_is_one_raw_string": isinstance(payload["raw_stream"], str),
        "no_sequence_array_training_key": "sequences" not in payload,
    }

    data_path = Path(__file__).parents[2] / "data" / "phase18d5_continuous_raw_stream.json"
    return {
        "campaign": {
            "name": "phase18d5-continuous-raw-segmentation-c1",
            "training_stream_type": "one continuous string",
            "record_separator_supplied": False,
            "field_separator_supplied": False,
            "task_ids_supplied": False,
            "task_count_supplied": False,
            "source_changes_for_appended_behavior": 0,
        },
        "induction": {
            "punctuation_candidates": list(_delimiter_candidates(payload["raw_stream"])),
            "delimiter_pairs_tested": initial.candidates_tested,
            "valid_delimiter_grammars": initial.valid_candidates,
            "record_separator": initial.record_separator,
            "field_separator": initial.field_separator,
            "initial_records": len(initial.sequences),
            "initial_latent_programs": len(initial.partition.programs),
            "final_records": len(final.sequences),
            "final_latent_programs": len(final.partition.programs),
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
            "new_behaviors_from_appended_raw_text": len(final.partition.programs) - len(initial.partition.programs),
        },
        "controls": controls,
        "resources": {
            "final_expressions_evaluated": final.partition.stats.expressions_evaluated,
            "final_candidate_behaviors": final.partition.stats.candidate_behaviors,
            "final_exact_cover_nodes": final.partition.stats.exact_cover_nodes,
            "learned_payload_bits": sum(program.payload_bits for program in final.partition.programs)
            + 16,
            "source_bytes": len(Path(__file__).read_bytes()),
            "data_bytes": len(data_path.read_bytes()),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "delimiter_and_program_induction_from_continuous_text": all(checks.values()),
            "autonomous_general_tokenization": False,
            "raw_natural_language_pretraining": False,
            "learned_atom_parser": False,
            "open_ended_world_model": False,
            "llm_like_general_learning": False,
        },
        "limitations": [
            "The atom syntax is fixed to JSON integer or quoted-string literals.",
            "Delimiter candidates are single punctuation characters.",
            "The final field of each inferred record remains the next-value target.",
            "The type system, primitive DSL, partition objective, and minimum support are human-designed.",
            "Evaluation still provides a complete local support record to select a behavior.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18d-5 results: continuous raw-stream segmentation

- Training input: **one continuous string**
- Delimiter pairs tested / valid: **{induction['delimiter_pairs_tested']} / {induction['valid_delimiter_grammars']}**
- Inferred record / field separators: **{induction['record_separator']!r} / {induction['field_separator']!r}**
- Initial records / latent programs: **{induction['initial_records']} / {induction['initial_latent_programs']}**
- Final records / latent programs: **{induction['final_records']} / {induction['final_latent_programs']}**
- Initial held-out: **{evaluation['initial_correct']}/{evaluation['initial_total']}**
- Final held-out: **{evaluation['final_correct']}/{evaluation['final_total']}**
- Source changes for appended behavior: **{payload['campaign']['source_changes_for_appended_behavior']}**
- Learned payload including delimiter roles: **{resources['learned_payload_bits']} bits**

The learner inferred record and field punctuation, converted the resulting records into next-value sequences, and discovered their latent programs. It did not receive sequence arrays, task IDs, or delimiter roles. The atom reader and typed DSL are still fixed, so this is not general tokenization or natural-language pretraining.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18d5.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path("results/phase18d5.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")


if __name__ == "__main__":
    main()
