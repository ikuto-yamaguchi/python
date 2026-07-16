from __future__ import annotations

import json
import resource
import string
import time
from pathlib import Path

from .sparc_hs6_experiment import configured_model as configured_hs6
from .sparc_units import (
    LENGTH,
    TIME,
    SPARCHS7Model,
    SparseTypedPlanBank,
    synthesize_typed_expression,
)


def configured_model() -> SPARCHS7Model:
    model = SPARCHS7Model(configured_hs6())
    distance = model.teach_units(
        [
            ("時速60kmで2時間進む距離は何kmですか？", "120km"),
            ("時速45kmで3時間進む距離は何kmですか？", "135km"),
            ("時速80kmで1.5時間進む距離は何kmですか？", "120km"),
        ]
    )
    model.typed_plans.link_surface(
        "秒速1mで2秒進む距離は何mですか？", distance, support=3
    )
    model.teach_units(
        [
            ("距離120kmを2時間で進む平均速度は時速何kmですか？", "60km/h"),
            ("距離150kmを3時間で進む平均速度は時速何kmですか？", "50km/h"),
            ("距離90kmを1.5時間で進む平均速度は時速何kmですか？", "60km/h"),
        ]
    )
    model.teach_units(
        [
            ("底辺100cm、高さ2mの長方形の面積は何m²ですか？", "2m²"),
            ("底辺50cm、高さ4mの長方形の面積は何m²ですか？", "2m²"),
            ("底辺250cm、高さ3mの長方形の面積は何m²ですか？", "7.5m²"),
        ]
    )
    model.teach_units(
        [
            ("1000mは何kmですか？", "1km"),
            ("2500mは何kmですか？", "2.5km"),
            ("3200mは何kmですか？", "3.2km"),
        ]
    )
    return model


def _alpha_code(index: int) -> str:
    alphabet = string.ascii_uppercase
    output: list[str] = []
    value = index
    while True:
        output.append(alphabet[value % 26])
        value = value // 26 - 1
        if value < 0:
            break
    return "".join(reversed(output))


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = configured_model()

    answers = {
        "conversation": model.reply("こんにちは"),
        "social": model.reply("イタリアの首都は何ですか？"),
        "hs6": model.reply(
            "原価1200円に25%の利益を加え送料150円を足した価格は何円ですか？"
        ),
        "distance_minutes": model.reply(
            "時速90kmで40分進む距離は何kmですか？"
        ),
        "distance_ms": model.reply(
            "秒速12mで25秒進む距離は何mですか？"
        ),
        "speed": model.reply(
            "距離175kmを2.5時間で進む平均速度は時速何kmですか？"
        ),
        "area": model.reply(
            "底辺120cm、高さ2.5mの長方形の面積は何m²ですか？"
        ),
        "conversion": model.reply("750mは何kmですか？"),
    }

    invalid_dimension_rejected = False
    try:
        synthesize_typed_expression(
            [
                ((1.0, 2.0), (LENGTH, TIME), 3.0, LENGTH),
                ((2.0, 5.0), (LENGTH, TIME), 7.0, LENGTH),
                ((4.0, 1.0), (LENGTH, TIME), 5.0, LENGTH),
            ],
            max_cost=7,
        )
    except ValueError:
        invalid_dimension_rejected = True

    restored = SPARCHS7Model.from_bytes(model.to_bytes())
    persistence = restored.reply(
        "時速36kmで30分進む距離は何kmですか？"
    )

    checks = {
        "conversation": answers["conversation"].text.startswith("こんにちは"),
        "social": answers["social"].text == "ローマです。",
        "hs6_retained": answers["hs6"].text.startswith("1650です"),
        "hour_minute_conversion": answers["distance_minutes"].text.startswith(
            "60kmです"
        ),
        "speed_surface_transfer": answers["distance_ms"].text.startswith(
            "300mです"
        ),
        "derived_speed": answers["speed"].text.startswith("70km/hです"),
        "mixed_length_area": answers["area"].text.startswith("3m²です"),
        "identity_conversion": answers["conversion"].text.startswith(
            "0.75kmです"
        ),
        "invalid_dimension_rejected": invalid_dimension_rejected,
        "persistence": persistence.text.startswith("18kmです"),
    }

    scale_start = time.perf_counter()
    bank = SparseTypedPlanBank(max_schemas=20_000, max_candidates=32)
    expression = bank.teach(
        [
            ("時速60kmで2時間進む距離は何kmですか？", "120km"),
            ("時速45kmで3時間進む距離は何kmですか？", "135km"),
            ("時速80kmで1.5時間進む距離は何kmですか？", "120km"),
        ]
    )
    schema_count = 10_000
    for index in range(schema_count):
        code = _alpha_code(index)
        bank.link_surface(
            f"形式{code}:時速1kmで2時間進む距離は何kmですか？",
            expression,
            support=3,
        )

    correct = 0
    max_candidates = 0
    max_anchor_reads = 0
    sample_queries = 512
    for sample in range(sample_queries):
        index = (sample * 7919) % schema_count
        code = _alpha_code(index)
        reply = bank.solve(
            f"形式{code}:時速72kmで2.5時間進む距離は何kmですか？"
        )
        if reply is not None and reply.text.startswith("180kmです"):
            correct += 1
        max_candidates = max(max_candidates, bank.last_candidates)
        max_anchor_reads = max(max_anchor_reads, bank.last_anchor_reads)

    scale_report = bank.report()
    scale_report.update(
        {
            "linked_surface_schemas": schema_count + 1,
            "sample_queries": sample_queries,
            "correct_queries": correct,
            "max_candidates_observed": max_candidates,
            "max_anchor_reads_observed": max_anchor_reads,
            "build_and_query_seconds": time.perf_counter() - scale_start,
            "expression_states": expression.semantic_states,
        }
    )

    result: dict[str, object] = {
        "capability_id": "SPARC-HS7-UNIT-TYPED-PLANS",
        "transformer_used": False,
        "softmax_attention_used": False,
        "growing_kv_cache_used": False,
        "unit_dimensional_checking": True,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "answers": {
            key: {"text": value.text, "mechanism": value.mechanism}
            for key, value in answers.items()
        },
        "compact_model": model.report(),
        "large_typed_plan_bank": scale_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS7 adds dimensionally typed unit planning and conversion. It still does "
            "not pass the complete integrated Japanese high-school readiness gate."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and correct == sample_queries
        and max_candidates <= 32
        and max_anchor_reads <= 128
        and scale_report["unique_typed_plans"] == 1
        and expression.semantic_states <= 64
        and scale_report["serialized_bytes"] <= 1_000_000
        and result["peak_process_kib"] <= 1_000_000
        and result["elapsed_seconds"] <= 120.0
    )
    (output_dir / "sparc_hs7_units.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-HS7-compact.model.zlib").write_bytes(model.to_bytes())
    (output_dir / "SPARC-HS7-unit-bank.model.zlib").write_bytes(bank.to_bytes())
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
