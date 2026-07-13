from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Mapping

from .phase18d14_byte_codec_core import (
    NoJointModelError,
    PrefixedPairCodec,
    TaggedByteCodec,
    encode_records,
    joint_infer,
    metrics,
    primitive_signature,
    shift_private_use,
)


def _data_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "phase18d14_joint_byte_stream.json"
    )


def load_dataset() -> Mapping[str, Any]:
    return json.loads(_data_path().read_text(encoding="utf-8"))


def _future_accuracy(result, labels) -> tuple[int, int]:
    correct = total = 0
    records = result.selected.grammar.records
    for position, label in enumerate(labels):
        if not label.endswith("_FUTURE"):
            continue
        total += 1
        source, target = records[position]
        if any(primitive.apply(source) == target for primitive in result.selected.library):
            correct += 1
    return correct, total


def _tagged_metamorphic(result) -> bool:
    shifted = shift_private_use(result.selected.grammar.records, 17)
    transformed = encode_records(
        shifted,
        TaggedByteCodec(0xF6),
        0xF4,
        0xF5,
    )
    recovered = joint_infer(transformed)
    return (
        recovered.selected.grammar.codec.kind == "tagged_mixed_width"
        and recovered.selected.grammar.record_separator == 0xF4
        and recovered.selected.grammar.field_separator == 0xF5
        and primitive_signature(recovered) == primitive_signature(result)
    )


def _pair_metamorphic(result) -> bool:
    transformed = encode_records(
        result.selected.grammar.records,
        PrefixedPairCodec(0xF6, 0xF7),
        0xF4,
        0xF5,
    )
    recovered = joint_infer(transformed)
    return (
        recovered.selected.grammar.codec.kind == "prefixed_fixed_width_2"
        and recovered.selected.grammar.record_separator == 0xF4
        and recovered.selected.grammar.field_separator == 0xF5
        and primitive_signature(recovered) == primitive_signature(result)
    )


def negative_controls() -> Mapping[str, bool]:
    ascii_only = (
        b"abcde\xfa" b"bcdea\xfb"
        b"klmno\xfa" b"lmnok\xfb"
        b"pqrst\xfa" b"qrstp"
    )
    checks = {}
    for name, stream in (
        ("single_alphabet_stream_rejected", ascii_only.hex()),
        ("truncated_tag_rejected", bytes((0xFC,)).hex()),
        ("malformed_hex_rejected", "0g"),
    ):
        try:
            joint_infer(stream)
        except NoJointModelError:
            checks[name] = True
        else:
            checks[name] = False
    return checks


def run() -> Mapping[str, Any]:
    payload = load_dataset()
    stream_hex = payload["stream_hex"]
    labels = tuple(payload["audit_labels"])
    result = joint_infer(stream_hex)
    selected = result.selected
    future_correct, future_total = _future_accuracy(result, labels)
    controls = negative_controls()
    prequential = metrics(selected)

    try:
        bytes.fromhex(stream_hex).decode("utf-8")
    except UnicodeDecodeError:
        utf8_rejected = True
    else:
        utf8_rejected = False

    signature = primitive_signature(result)
    checks = {
        "raw_hex_only": set(payload) == {
            "campaign",
            "stream_hex",
            "audit_labels",
        },
        "fixed_utf8_decoder_not_applicable": utf8_rejected,
        "joint_model_unique": (
            result.grammar_candidates >= 2
            and result.eligible_candidates == 1
            and result.positive_candidates == 1
        ),
        "tagged_codec_recovered": (
            selected.grammar.codec.kind == "tagged_mixed_width"
        ),
        "record_count_recovered": (
            len(selected.grammar.records) == len(labels) == 48
        ),
        "two_distinct_primitives": signature == (
            ("index", 1, 1),
            ("element", 1, 1),
        ),
        "promotion_positions": tuple(
            promotion.position for promotion in selected.promotions
        )
        == (15, 20),
        "cross_alphabet_support": all(
            set(promotion.support_alphabets)
            == {"ascii_letters", "private_use"}
            for promotion in selected.promotions
        ),
        "positive_mdl": (
            selected.compression_gain_bits > 0
            and all(promotion.mdl_gain_bits > 0 for promotion in selected.promotions)
        ),
        "future_hidden_accuracy": (
            future_total == 21 and future_correct == future_total
        ),
        "three_noise_residuals": len(selected.unresolved) == 3,
        "tagged_codec_metamorphic": _tagged_metamorphic(result),
        "different_codec_family_metamorphic": _pair_metamorphic(result),
        "negative_controls": all(controls.values()),
    }

    source = inspect.getsource(inspect.getmodule(joint_infer))
    source_audit = {
        "audit_labels_not_learner_argument": (
            "audit_labels" not in inspect.signature(joint_infer).parameters
        ),
        "specific_codec_bytes_not_in_joint_infer": all(
            token not in inspect.getsource(joint_infer).lower()
            for token in ("0xfa", "0xfb", "0xfc")
        ),
        "task_dispatch_absent": ("match " + "task") not in source.lower(),
    }
    checks["source_audit"] = all(source_audit.values())

    return {
        "campaign": {
            "name": payload["campaign"]["name"],
            "raw_bytes": len(bytes.fromhex(stream_hex)),
            "record_count_supplied": False,
            "input_output_fields_supplied": False,
            "utf8_decoder_used": False,
            "task_ids_supplied": False,
        },
        "joint_codec": {
            "grammar_candidates": result.grammar_candidates,
            "eligible_candidates": result.eligible_candidates,
            "positive_candidates": result.positive_candidates,
            "record_separator": selected.grammar.record_separator,
            "field_separator": selected.grammar.field_separator,
            "codec": selected.grammar.codec.render(),
            "records_recovered": len(selected.grammar.records),
            "codec_payload_bits": selected.grammar.codec.payload_bits,
            "joint_compression_gain_bits": selected.compression_gain_bits,
        },
        "primitive_library": {
            "count": len(selected.library),
            "signature": [list(row) for row in signature],
            "promotion_positions": [
                promotion.position for promotion in selected.promotions
            ],
            "support_positions": [
                list(promotion.support_positions)
                for promotion in selected.promotions
            ],
            "support_alphabets": [
                list(promotion.support_alphabets)
                for promotion in selected.promotions
            ],
            "mdl_gains_bits": [
                promotion.mdl_gain_bits for promotion in selected.promotions
            ],
            "payload_bits": sum(
                primitive.payload_bits for primitive in selected.library
            ),
            "candidates_evaluated": selected.candidates_evaluated,
        },
        "evaluation": {
            **prequential,
            "future_hidden_correct": future_correct,
            "future_hidden_total": future_total,
            "unresolved_positions": [
                row.position for row in selected.unresolved
            ],
        },
        "negative_controls": controls,
        "source_audit": source_audit,
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "joint_byte_chunking_and_primitive_invention": all(checks.values()),
            "utf8_fixed": False,
            "codec_meta_grammar_human_designed": True,
            "arbitrary_codec_learning": False,
            "natural_language_learning": False,
            "llm_like_general_learning": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "Codec candidates are human-designed: single-byte, tagged mixed-width, and prefixed fixed-width pairs.",
            "Two-field records and control-byte candidates above 0xEF are still assumed.",
            "The primitive meta-grammar remains restricted to affine index and element transforms.",
            "Codec selection is batch over the full stream; primitive promotions are causal after decoding.",
            "No natural-language semantics, unrestricted tokenization, or open-domain learning is claimed.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    codec = payload["joint_codec"]
    library = payload["primitive_library"]
    evaluation = payload["evaluation"]
    return f"""# Phase 18d-14 results: joint byte codec and primitive invention

- Raw stream: **{payload['campaign']['raw_bytes']} bytes**
- Grammar / eligible / positive candidates: **{codec['grammar_candidates']} / {codec['eligible_candidates']} / {codec['positive_candidates']}**
- Selected codec: **{codec['codec']['kind']}**
- Recovered records: **{codec['records_recovered']}**
- Joint compression gain: **{codec['joint_compression_gain_bits']} bits**
- Invented primitives: **{library['count']}**
- Promotion positions: **{library['promotion_positions']}**
- Primitive MDL gains: **{library['mdl_gains_bits']} bits**
- Future hidden transfer: **{evaluation['future_hidden_correct']}/{evaluation['future_hidden_total']}**
- Prequential covered accuracy / coverage: **{100*evaluation['covered_accuracy']:.2f}% / {100*evaluation['coverage']:.2f}%**
- Unresolved noise: **{len(evaluation['unresolved_positions'])}**
- Library payload: **{library['payload_bits']} bits**

The source bytes are not valid UTF-8. The learner jointly selects byte chunking, separator roles, and a reusable primitive library. A human-designed codec and primitive meta-grammar remains, so this is controlled representation learning rather than unrestricted language-model training.
"""


def main() -> None:
    payload = run()
    results = Path("results")
    results.mkdir(exist_ok=True)
    (results / "phase18d14.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (results / "phase18d14.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")
    if not payload["all_theorem_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
