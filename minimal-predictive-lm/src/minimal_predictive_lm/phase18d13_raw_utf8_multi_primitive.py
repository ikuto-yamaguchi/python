from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .phase18d10_primitive_core import IndexAffinePrimitive
from .phase18d12_multi_primitive_core import ElementAffinePrimitive
from .phase18d13_raw_utf8_core import (
    NoGrammarError,
    RawLookupPrimitive,
    RawOnlineResult,
    decode_hex,
    infer_grammar,
    learn_raw_stream,
    metrics,
)


def _data_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "phase18d13_raw_utf8_stream.json"


def load_dataset() -> Mapping[str, Any]:
    return json.loads(_data_path().read_text(encoding="utf-8"))


def canonical(value: str) -> tuple[int, ...]:
    return tuple(map(ord, value))


def future_hidden_accuracy(result: RawOnlineResult,
                           labels: Sequence[str]) -> tuple[int, int]:
    correct = total = 0
    for (source, target), label in zip(result.grammar.records, labels):
        if not label.endswith("_FUTURE"):
            continue
        matches = 0
        for primitive in result.library:
            try:
                matches += canonical(primitive.apply(source)) == canonical(target)
            except (TypeError, ValueError):
                pass
        total += 1
        correct += matches == 1
    return correct, total


def _shift_private_use(text: str, delta: int) -> str:
    return "".join(chr(ord(ch) + delta) if 0xE000 <= ord(ch) <= 0xF8FF else ch
                   for ch in text)


def controls(payload: Mapping[str, Any]) -> Mapping[str, bool]:
    stream_hex = str(payload["stream_hex"])
    text = decode_hex(stream_hex)
    reference = learn_raw_stream(stream_hex)
    grammar = reference.grammar
    replacement = text.replace(grammar.field_separator, "^").replace(
        grammar.record_separator, ";")
    changed = learn_raw_stream(replacement.encode("utf-8").hex())
    delimiter_recovered = (
        changed.grammar.field_separator == "^"
        and changed.grammar.record_separator == ";"
        and tuple(p.primitive.render() for p in changed.promotions)
        == tuple(p.primitive.render() for p in reference.promotions)
    )
    shifted = learn_raw_stream(_shift_private_use(text, 37).encode("utf-8").hex())
    glyph_invariant = tuple(p.primitive.render() for p in shifted.promotions) == tuple(
        p.primitive.render() for p in reference.promotions)
    try:
        infer_grammar("ff")
    except NoGrammarError:
        invalid_rejected = True
    else:
        invalid_rejected = False
    try:
        infer_grammar("ab~bc~cd".encode().hex())
    except NoGrammarError:
        incomplete_rejected = True
    else:
        incomplete_rejected = False
    return {
        "delimiter_symbols_relearned": delimiter_recovered,
        "private_use_glyph_shift_invariant": glyph_invariant,
        "invalid_utf8_rejected": invalid_rejected,
        "incomplete_separator_grammar_rejected": incomplete_rejected,
    }


def run() -> Mapping[str, Any]:
    payload = load_dataset()
    result = learn_raw_stream(str(payload["stream_hex"]))
    labels = tuple(payload["audit_labels"])
    score = metrics(result)
    future_correct, future_total = future_hidden_accuracy(result, labels)
    control_results = controls(payload)
    recovered = set()
    for primitive in result.library:
        if isinstance(primitive, IndexAffinePrimitive):
            recovered.add(("index_affine", primitive.multiplier, primitive.offset))
        elif isinstance(primitive, ElementAffinePrimitive):
            recovered.add(("element_affine", primitive.scale, primitive.offset))
    promoted = {position for promotion in result.promotions
                for position in promotion.support_positions}
    checks = {
        "raw_file_has_no_records_or_fields": all(
            token not in payload for token in ("stream", "input", "output")),
        "separator_grammar_unique": (
            result.grammar.valid_grammars == 1
            and result.grammar.record_separator == "|"
            and result.grammar.field_separator == "~"),
        "record_count_recovered": len(result.grammar.records) == 48,
        "two_heterogeneous_primitives_recovered": recovered == {
            ("index_affine", 1, 1), ("element_affine", 1, 1)},
        "promotion_positions": tuple(p.position for p in result.promotions) == (15, 20),
        "cross_alphabet_support": all(
            set(p.support_alphabets) == {"ascii_letters", "private_use"}
            for p in result.promotions),
        "positive_mdl_gain": all(p.mdl_gain_bits > 0 for p in result.promotions),
        "noise_not_promoted": all(labels[position].startswith("HIDDEN")
                                  for position in promoted),
        "future_hidden_accuracy": future_total == 21 and future_correct == future_total,
        "controls": all(control_results.values()),
    }
    learner_source = inspect.getsource(learn_raw_stream)
    source_audit = {
        "audit_labels_not_accepted": "audit_labels" not in inspect.signature(
            learn_raw_stream).parameters,
        "hidden_labels_not_in_learner": (
            ("HIDDEN_" + "INDEX") not in learner_source
            and ("HIDDEN_" + "ELEMENT") not in learner_source),
        "target_parameters_not_in_data": all(
            token not in json.dumps(payload) for token in ("multiplier", "scale", "offset")),
    }
    checks["source_audit"] = all(source_audit.values())
    return {
        "campaign": {
            "name": payload["campaign"]["name"],
            "raw_stream_bytes": len(bytes.fromhex(str(payload["stream_hex"]))),
            "typed_records_supplied": False,
            "input_output_fields_supplied": False,
        },
        "grammar": {
            "separator_candidates": result.grammar.separator_candidates,
            "valid_grammars": result.grammar.valid_grammars,
            "record_separator_codepoint": ord(result.grammar.record_separator),
            "field_separator_codepoint": ord(result.grammar.field_separator),
            "records": len(result.grammar.records),
        },
        "online_invention": {
            "promotions": len(result.promotions),
            "promotion_positions": [p.position for p in result.promotions],
            "selected_primitives": [p.primitive.render() for p in result.promotions],
            "support_alphabets": [list(p.support_alphabets) for p in result.promotions],
            "candidate_counts": [p.candidates_evaluated for p in result.promotions],
            "mdl_gain_bits": [p.mdl_gain_bits for p in result.promotions],
            "unresolved_positions": list(result.unresolved_positions),
        },
        "prequential": score,
        "future_hidden": {"correct": future_correct, "total": future_total,
                          "accuracy": future_correct / future_total},
        "controls": control_results,
        "source_audit": source_audit,
        "resources": {
            "library_payload_bits": sum(p.payload_bits for p in result.library),
            "candidates_evaluated_total": result.candidates_evaluated,
            "python_runtime_included": False,
            "grammar_and_meta_grammar_source_included_in_payload": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "raw_utf8_multi_primitive_invention": all(checks.values()),
            "unicode_codepoints_not_raw_bytes_are_atoms": True,
            "candidate_meta_grammar_human_designed": True,
            "arbitrary_computation_invented": False,
            "llm_like_general_learning": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "UTF-8 decoding and the two-field grammar family are human-designed.",
            "Alphabet diversity and primitive candidate families are human-designed.",
            "The learner operates on Unicode codepoints, not raw byte atoms.",
            "No natural-language semantics or unrestricted algorithm invention is claimed.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    grammar = payload["grammar"]
    invention = payload["online_invention"]
    future = payload["future_hidden"]
    score = payload["prequential"]
    return f"""# Phase 18d-13 results: raw UTF-8 multi-primitive invention

- Raw stream bytes: **{payload['campaign']['raw_stream_bytes']}**
- Typed records / input-output fields supplied: **no / no**
- Separator candidates / valid grammars: **{grammar['separator_candidates']} / {grammar['valid_grammars']}**
- Recovered records: **{grammar['records']}**
- Promotions / positions: **{invention['promotions']} / {invention['promotion_positions']}**
- Selected primitives: **{invention['selected_primitives']}**
- Candidate counts: **{invention['candidate_counts']}**
- MDL gains: **{invention['mdl_gain_bits']} bits**
- Future hidden accuracy: **{future['correct']}/{future['total']} = {100 * future['accuracy']:.1f}%**
- Prequential correct / wrong / abstain: **{score['correct']} / {score['wrong']} / {score['abstained']}**
- Covered accuracy / coverage: **{100 * score['covered_accuracy']:.2f}% / {100 * score['coverage']:.2f}%**
- Remaining unresolved positions: **{invention['unresolved_positions']}**

A single UTF-8 stream is decoded, segmented, and used to invent two heterogeneous primitives. UTF-8 decoding, alphabet gates, grammar family, and primitive meta-grammar remain human-designed.
"""


def main() -> None:
    payload = run()
    results = Path("results")
    results.mkdir(exist_ok=True)
    (results / "phase18d13.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (results / "phase18d13.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")
    if not payload["all_theorem_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
