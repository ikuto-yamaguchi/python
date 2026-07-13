from __future__ import annotations

from dataclasses import dataclass
import inspect
import json
from pathlib import Path
from typing import Any, Mapping, Sequence
import unicodedata

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


class ByteGrammarError(ValueError):
    pass


class NonIdentifiableByteGrammarError(ValueError):
    pass


@dataclass(frozen=True)
class ByteGrammar:
    record_separator: int
    field_separator: int
    numeric_zero_codepoint: int
    sequences: tuple[tuple[Any, ...], ...]
    partition: LatentPartition
    candidates_tested: int
    valid_candidates: int

    def program_fingerprint(self) -> tuple[Any, ...]:
        return self.partition.fingerprint()

    @property
    def codec_payload_bits(self) -> int:
        return 8 + 8 + 16


def load_byte_stream(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).parents[2] / "data" / "phase18d6_utf8_byte_stream.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported byte-stream schema")
    return payload


def _bytes_from_hex(value: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise ByteGrammarError("invalid hexadecimal byte stream") from exc


def _delimiter_candidates(raw: bytes) -> tuple[int, ...]:
    return tuple(
        sorted(
            {
                value
                for value in raw
                if 33 <= value <= 126
                and not chr(value).isalnum()
                and chr(value) not in {'"', "'", ".", "+", "-"}
            }
        )
    )


def _split_records(raw: bytes, record_separator: int, field_separator: int) -> tuple[tuple[bytes, ...], ...]:
    if record_separator == field_separator:
        raise ByteGrammarError("separator roles must differ")
    record_token = bytes((record_separator,))
    field_token = bytes((field_separator,))
    records = raw.split(record_token)
    if len(records) < 2 or any(not record for record in records):
        raise ByteGrammarError("invalid record segmentation")
    rows = tuple(tuple(record.split(field_token)) for record in records)
    if any(len(row) < 2 or len(row) > 4 or any(not atom for atom in row) for row in rows):
        raise ByteGrammarError("invalid field segmentation")
    return rows


def _decode_utf8(atom: bytes) -> str:
    try:
        text = atom.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ByteGrammarError("atom is not valid UTF-8") from exc
    if not text or any(not character.isprintable() for character in text):
        raise ByteGrammarError("atom is not printable UTF-8")
    return text


def _is_numeric_glyph(text: str) -> bool:
    return len(text) == 1 and unicodedata.category(text) == "Co"


def _zero_candidates(rows: Sequence[Sequence[bytes]]) -> tuple[int, ...]:
    codepoints: list[int] = []
    for row in rows:
        for atom in row:
            text = _decode_utf8(atom)
            if _is_numeric_glyph(text):
                codepoints.append(ord(text))
    if not codepoints:
        raise ByteGrammarError("no private-use numeric glyph candidates")
    return tuple(range(min(codepoints), max(codepoints) + 1))


def _decode_atom(atom: bytes, numeric_zero_codepoint: int) -> Any:
    text = _decode_utf8(atom)
    if _is_numeric_glyph(text):
        value = ord(text) - numeric_zero_codepoint
        if not -64 <= value <= 64:
            raise ByteGrammarError("numeric glyph is outside the bounded codec")
        return value
    return text


def parse_byte_stream(
    raw: bytes,
    record_separator: int,
    field_separator: int,
    numeric_zero_codepoint: int,
) -> tuple[tuple[Any, ...], ...]:
    rows = _split_records(raw, record_separator, field_separator)
    return tuple(
        tuple(_decode_atom(atom, numeric_zero_codepoint) for atom in row)
        for row in rows
    )


def induce_byte_grammar(
    raw: bytes,
    *,
    minimum_support: int = 5,
    max_cost: int = 3,
) -> ByteGrammar:
    symbols = _delimiter_candidates(raw)
    tested = 0
    valid: list[
        tuple[
            tuple[int, int],
            int,
            int,
            int,
            tuple[tuple[Any, ...], ...],
            LatentPartition,
        ]
    ] = []
    for record_separator in symbols:
        for field_separator in symbols:
            if record_separator == field_separator:
                continue
            try:
                byte_rows = _split_records(raw, record_separator, field_separator)
                zero_candidates = _zero_candidates(byte_rows)
            except ByteGrammarError:
                continue
            for numeric_zero_codepoint in zero_candidates:
                tested += 1
                try:
                    sequences = tuple(
                        tuple(
                            _decode_atom(atom, numeric_zero_codepoint)
                            for atom in row
                        )
                        for row in byte_rows
                    )
                    partition = learn_from_sequences(
                        sequences,
                        max_cost=max_cost,
                        minimum_support=minimum_support,
                    )
                except ValueError:
                    continue
                score = (
                    len(partition.programs),
                    sum(program.cost for program in partition.programs),
                )
                valid.append(
                    (
                        score,
                        record_separator,
                        field_separator,
                        numeric_zero_codepoint,
                        sequences,
                        partition,
                    )
                )

    if not valid:
        raise ByteGrammarError(f"no valid byte grammar among {tested} candidates")
    best_score = min(row[0] for row in valid)
    best = [row for row in valid if row[0] == best_score]
    keys = {
        (row[1], row[2], row[3], row[5].fingerprint())
        for row in best
    }
    if len(keys) != 1:
        raise NonIdentifiableByteGrammarError(
            f"score={best_score}, optimum_byte_grammars={len(keys)}"
        )
    _, record_separator, field_separator, zero, sequences, partition = best[0]
    return ByteGrammar(
        record_separator,
        field_separator,
        zero,
        sequences,
        partition,
        tested,
        len(valid),
    )


def _decode_record(grammar: ByteGrammar, raw: bytes, *, minimum_fields: int = 2) -> tuple[Any, ...]:
    fields = raw.split(bytes((grammar.field_separator,)))
    if len(fields) < minimum_fields or any(not field for field in fields):
        raise ByteGrammarError("invalid episode record")
    return tuple(_decode_atom(field, grammar.numeric_zero_codepoint) for field in fields)


def evaluate_byte_episodes(
    grammar: ByteGrammar,
    episodes: Sequence[Mapping[str, Any]],
) -> tuple[int, int, int]:
    correct = covered = total = 0
    for episode in episodes:
        total += len(episode["queries"])
        try:
            support = (
                _decode_record(grammar, _bytes_from_hex(episode["support_hex"])),
            )
            program = route_from_sequence_support(grammar.partition, support)
        except (ByteGrammarError, NonIdentifiableRoutingError):
            continue
        covered += len(episode["queries"])
        for query in episode["queries"]:
            try:
                prefix = _decode_record(
                    grammar,
                    _bytes_from_hex(query["prefix_hex"]),
                    minimum_fields=1,
                )
                target = _decode_atom(
                    _bytes_from_hex(query["target_hex"]),
                    grammar.numeric_zero_codepoint,
                )
                prediction = program.predict(prefix_to_inputs(prefix))
            except (ByteGrammarError, EvaluationError):
                continue
            correct += canonical(prediction) == canonical(decode_value(target))
    return correct, covered, total


def _shift_private_use_glyphs(raw: bytes, offset: int) -> bytes:
    text = _decode_utf8(raw)
    shifted = "".join(
        chr(ord(character) + offset)
        if unicodedata.category(character) == "Co"
        else character
        for character in text
    )
    return shifted.encode("utf-8")


def _rename_delimiters(raw: bytes, old_record: int, old_field: int, new_record: int, new_field: int) -> bytes:
    sentinel = b"\x00"
    if sentinel in raw:
        raise ByteGrammarError("sentinel collision")
    return (
        raw.replace(bytes((old_field,)), sentinel)
        .replace(bytes((old_record,)), bytes((new_record,)))
        .replace(sentinel, bytes((new_field,)))
    )


def _encode_numeric_control(records: Sequence[Sequence[int]], zero: int = 0xE500) -> bytes:
    return "|".join(
        "~".join(chr(zero + value) for value in record)
        for record in records
    ).encode("utf-8")


def _failure_controls(payload: Mapping[str, Any], final: ByteGrammar) -> dict[str, bool]:
    controls: dict[str, bool] = {}
    try:
        induce_byte_grammar(b"\xff~a|b~c")
    except ByteGrammarError:
        controls["invalid_utf8_abstains"] = True
    else:
        controls["invalid_utf8_abstains"] = False

    try:
        induce_byte_grammar(b"a~b~c")
    except ByteGrammarError:
        controls["one_separator_kind_abstains"] = True
    else:
        controls["one_separator_kind_abstains"] = False

    translation_invariant = _encode_numeric_control(
        ((-2, 5, 5), (7, 3, 7), (-8, -1, -1), (4, 9, 9), (2, 6, 6))
    )
    try:
        induce_byte_grammar(translation_invariant)
    except NonIdentifiableByteGrammarError:
        controls["translation_invariant_codec_is_nonidentifiable"] = True
    else:
        controls["translation_invariant_codec_is_nonidentifiable"] = False

    zero_glyph = chr(final.numeric_zero_codepoint).encode("utf-8")
    ambiguous_episode = (
        {
            "support_hex": (
                zero_glyph
                + bytes((final.field_separator,))
                + zero_glyph
                + bytes((final.field_separator,))
                + zero_glyph
            ).hex(),
            "queries": [{"prefix_hex": zero_glyph.hex(), "target_hex": zero_glyph.hex()}],
        },
    )
    _, covered, total = evaluate_byte_episodes(final, ambiguous_episode)
    controls["ambiguous_support_abstains"] = covered == 0 and total == 1
    return controls


def run() -> dict[str, Any]:
    payload = load_byte_stream()
    initial_raw = _bytes_from_hex(payload["byte_stream_hex"])
    appended_raw = _bytes_from_hex(payload["post_freeze_hex"])
    initial = induce_byte_grammar(initial_raw)
    initial_correct, initial_covered, initial_total = evaluate_byte_episodes(
        initial, payload["episodes"]
    )

    combined = initial_raw + bytes((initial.record_separator,)) + appended_raw
    final = induce_byte_grammar(combined)
    all_episodes = tuple(payload["episodes"]) + tuple(payload["post_freeze_episodes"])
    final_correct, final_covered, final_total = evaluate_byte_episodes(final, all_episodes)
    old_unchanged = set(initial.partition.fingerprint()).issubset(
        set(final.partition.fingerprint())
    )

    shifted_raw = _shift_private_use_glyphs(initial_raw, 37)
    shifted = induce_byte_grammar(shifted_raw)
    renamed_raw = _rename_delimiters(
        initial_raw,
        initial.record_separator,
        initial.field_separator,
        ord("#"),
        ord("%"),
    )
    renamed = induce_byte_grammar(renamed_raw)
    controls = _failure_controls(payload, final)

    source = inspect.getsource(inspect.getmodule(run))
    audit_names = tuple(payload["audit_clusters"]) + tuple(
        payload["post_freeze_audit_clusters"]
    )
    data_path = Path(__file__).parents[2] / "data" / "phase18d6_utf8_byte_stream.json"
    raw_data = data_path.read_text(encoding="utf-8")

    checks = {
        "initial_separator_inferred": (
            initial.record_separator,
            initial.field_separator,
        ) == (ord("|"), ord("~")),
        "numeric_zero_inferred": initial.numeric_zero_codepoint == 0xE300,
        "initial_program_count": len(initial.partition.programs) == 7,
        "final_program_count": len(final.partition.programs) == 8,
        "initial_audit_partition": audit_sequence_clusters(
            initial.partition, payload["audit_clusters"]
        ),
        "final_audit_partition": audit_sequence_clusters(
            final.partition, audit_names
        ),
        "initial_accuracy": initial_correct == initial_total,
        "initial_coverage": initial_covered == initial_total,
        "final_accuracy": final_correct == final_total,
        "final_coverage": final_covered == final_total,
        "old_programs_unchanged": old_unchanged,
        "numeric_glyph_shift_invariance": (
            shifted.numeric_zero_codepoint == initial.numeric_zero_codepoint + 37
            and shifted.partition.fingerprint() == initial.partition.fingerprint()
        ),
        "delimiter_rename_invariance": (
            renamed.record_separator,
            renamed.field_separator,
            renamed.partition.fingerprint(),
        ) == (ord("#"), ord("%"), initial.partition.fingerprint()),
        "audit_names_absent_from_source": all(name not in source for name in audit_names),
        "failure_controls": all(controls.values()),
        "training_is_hex_encoded_bytes": isinstance(payload["byte_stream_hex"], str),
        "no_raw_atom_or_type_labels": all(
            token not in raw_data
            for token in ('"sequences"', '"inputs"', '"output"', '"types"', '"task_id"')
        ),
    }

    return {
        "campaign": {
            "name": "phase18d6-utf8-byte-codec-induction-c1",
            "training_input": "UTF-8 bytes encoded as hexadecimal storage",
            "record_separator_supplied": False,
            "field_separator_supplied": False,
            "numeric_symbol_values_supplied": False,
            "explicit_type_labels": False,
            "task_ids_supplied": False,
            "source_changes_for_appended_behavior": 0,
        },
        "induction": {
            "delimiter_byte_candidates": list(_delimiter_candidates(initial_raw)),
            "joint_candidates_tested": initial.candidates_tested,
            "valid_joint_candidates": initial.valid_candidates,
            "record_separator_byte": initial.record_separator,
            "field_separator_byte": initial.field_separator,
            "numeric_zero_codepoint": initial.numeric_zero_codepoint,
            "initial_records": len(initial.sequences),
            "initial_programs": len(initial.partition.programs),
            "final_records": len(final.sequences),
            "final_programs": len(final.partition.programs),
            "programs": [program.expression.render() for program in final.partition.programs],
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
            "new_behaviors_from_appended_bytes": len(final.partition.programs)
            - len(initial.partition.programs),
        },
        "controls": controls,
        "resources": {
            "final_expressions_evaluated": final.partition.stats.expressions_evaluated,
            "final_candidate_behaviors": final.partition.stats.candidate_behaviors,
            "final_exact_cover_nodes": final.partition.stats.exact_cover_nodes,
            "learned_program_bits": sum(
                program.payload_bits for program in final.partition.programs
            ),
            "codec_and_separator_bits": final.codec_payload_bits,
            "total_learned_payload_bits": sum(
                program.payload_bits for program in final.partition.programs
            )
            + final.codec_payload_bits,
            "source_bytes": len(Path(__file__).read_bytes()),
            "data_bytes": len(data_path.read_bytes()),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "utf8_bytes_to_latent_programs": all(checks.values()),
            "contiguous_private_use_numeric_codec_induced": all(checks.values()),
            "arbitrary_atom_parser": False,
            "autonomous_general_tokenization": False,
            "natural_language_pretraining": False,
            "learned_open_type_system": False,
            "llm_like_general_learning": False,
        },
        "limitations": [
            "UTF-8 validation and a private-use single-codepoint numeric codec family are human-designed.",
            "Text atoms are passed through as complete UTF-8 field spans; internal word/subword tokenization is not learned.",
            "The final field remains the prediction target and the primitive DSL remains fixed.",
            "Exact cover, minimum support, and few-shot support routing remain human-designed.",
            "This is a small symbolic byte stream, not open-domain natural language or code pretraining.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18d-6 results: UTF-8 byte codec and latent programs

- Training representation: **one UTF-8 byte stream**
- Joint grammar/codec candidates tested / valid: **{induction['joint_candidates_tested']} / {induction['valid_joint_candidates']}**
- Inferred record / field separator bytes: **{induction['record_separator_byte']} / {induction['field_separator_byte']}**
- Inferred numeric zero codepoint: **U+{induction['numeric_zero_codepoint']:04X}**
- Initial / final records: **{induction['initial_records']} / {induction['final_records']}**
- Initial / final latent programs: **{induction['initial_programs']} / {induction['final_programs']}**
- Initial masked prediction: **{evaluation['initial_correct']}/{evaluation['initial_total']}**
- Final masked prediction: **{evaluation['final_correct']}/{evaluation['final_total']}**
- Learned program / codec payload: **{resources['learned_program_bits']} / {resources['codec_and_separator_bits']} bits**
- Total learned payload: **{resources['total_learned_payload_bits']} bits**

The learner received bytes rather than typed integer/string atoms. It jointly selected delimiter roles and a contiguous private-use numeric symbol offset, then reused the existing latent-program objective. This removes explicit atom values and type labels for the controlled stream, but it is not arbitrary tokenization, open type discovery, or natural-language pretraining.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18d6.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path("results/phase18d6.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")


if __name__ == "__main__":
    main()
