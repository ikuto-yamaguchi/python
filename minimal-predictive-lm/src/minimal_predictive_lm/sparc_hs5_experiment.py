from __future__ import annotations

import json
import resource
import string
import time
from pathlib import Path

from .sparc_hs4_experiment import configured_model as configured_hs4
from .sparc_programs import SPARCHS5Model, SparseProgramBank


def configured_model() -> SPARCHS5Model:
    base = configured_hs4()
    base.model.base.language.fit(
        [
            ("こんにちは", "こんにちは。今日は何を考えましょうか？"),
            ("何ができる？", "文章から学んだ関係と計算手順を局所的に使えます。"),
            ("分からない時は？", "分からないと明示して、追加情報を求めます。"),
        ]
    )
    model = SPARCHS5Model(base)
    lessons = [
        [
            ("時速60kmで2時間進む距離は何kmですか？", 120),
            ("時速45kmで3時間進む距離は何kmですか？", 135),
            ("時速80kmで1.5時間進む距離は何kmですか？", 120),
        ],
        [
            ("800円の商品を25%引きで買うと何円ですか？", 600),
            ("1200円の商品を10%引きで買うと何円ですか？", 1080),
            ("500円の商品を20%引きで買うと何円ですか？", 400),
        ],
        [
            ("70点と80点と90点の平均は何点ですか？", 80),
            ("60点と75点と90点の平均は何点ですか？", 75),
            ("40点と50点と60点の平均は何点ですか？", 50),
        ],
        [
            ("3x+5=20のxは何ですか？", 5),
            ("4x+8=40のxは何ですか？", 8),
            ("5x+10=60のxは何ですか？", 10),
        ],
        [
            ("底辺10cm、高さ6cmの三角形の面積は何平方cmですか？", 30),
            ("底辺8cm、高さ5cmの三角形の面積は何平方cmですか？", 20),
            ("底辺12cm、高さ7cmの三角形の面積は何平方cmですか？", 42),
        ],
        [
            ("800人の25%は何人ですか？", 200),
            ("1200人の10%は何人ですか？", 120),
            ("500人の40%は何人ですか？", 200),
        ],
    ]
    for examples in lessons:
        model.teach_math(examples)
    return model


def _alpha_code(index: int) -> str:
    alphabet = string.ascii_uppercase
    output = []
    value = index
    while True:
        output.append(alphabet[value % len(alphabet)])
        value = value // len(alphabet) - 1
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
        "biology": model.reply("犬は生物に分類されますか？"),
        "science": model.reply("落雷は装置停止につながりますか？"),
        "speed": model.reply("時速72kmで2.5時間進む距離は何kmですか？"),
        "discount": model.reply("2000円の商品を15%引きで買うと何円ですか？"),
        "average": model.reply("55点と70点と85点の平均は何点ですか？"),
        "equation": model.reply("6x+12=54のxは何ですか？"),
        "triangle": model.reply("底辺14cm、高さ9cmの三角形の面積は何平方cmですか？"),
        "percentage": model.reply("900人の30%は何人ですか？"),
    }
    restored = SPARCHS5Model.from_bytes(model.to_bytes())
    persistence = restored.reply("1000円の商品を30%引きで買うと何円ですか？")

    checks = {
        "conversation": answers["conversation"].text.startswith("こんにちは"),
        "social_studies": answers["social"].text == "ローマです。",
        "biology_reasoning": answers["biology"].text.startswith("犬は生物の関係"),
        "science_reasoning": answers["science"].text.startswith("落雷は装置停止の関係"),
        "speed_program": answers["speed"].text.startswith("180です"),
        "discount_program": answers["discount"].text.startswith("1700です"),
        "average_program": answers["average"].text.startswith("70です"),
        "equation_program": answers["equation"].text.startswith("7です"),
        "geometry_program": answers["triangle"].text.startswith("63です"),
        "percentage_program": answers["percentage"].text.startswith("270です"),
        "persistence": persistence.text.startswith("700です"),
        "single_shared_model": model.report()["shared_model"] is True,
    }

    scale_start = time.perf_counter()
    bank = SparseProgramBank(max_schemas=20_000, max_candidates=32)
    schema_count = 10_000
    for index in range(schema_count):
        code = _alpha_code(index)
        bank.teach(
            [
                (f"演算{code}:3個と4個を掛けた数は？", 12),
                (f"演算{code}:5個と6個を掛けた数は？", 30),
            ]
        )

    correct = 0
    max_candidates = 0
    max_anchor_reads = 0
    max_programs = 0
    queries = 512
    for sample in range(queries):
        index = (sample * 7919) % schema_count
        code = _alpha_code(index)
        result = bank.solve(f"演算{code}:7個と8個を掛けた数は？")
        if result is not None and result.text.startswith("56です"):
            correct += 1
        max_candidates = max(max_candidates, bank.last_candidates)
        max_anchor_reads = max(max_anchor_reads, bank.last_anchor_reads)
        max_programs = max(max_programs, bank.last_programs_executed)

    scale_report = bank.report()
    scale_report.update(
        {
            "schemas": schema_count,
            "sample_queries": queries,
            "correct_queries": correct,
            "max_candidates_observed": max_candidates,
            "max_anchor_reads_observed": max_anchor_reads,
            "max_programs_executed_observed": max_programs,
            "build_and_query_seconds": time.perf_counter() - scale_start,
        }
    )

    result: dict[str, object] = {
        "capability_id": "SPARC-HS5-CURRICULUM-PROGRAMS",
        "transformer_used": False,
        "softmax_attention_used": False,
        "growing_kv_cache_used": False,
        "one_shared_model": True,
        "programs_induced_from_qa_examples": True,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "answers": {
            key: {"text": value.text, "mechanism": value.mechanism}
            for key, value in answers.items()
        },
        "compact_model": model.report(),
        "large_program_bank": scale_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS5 induces a small numeric microprogram from demonstrations and combines it "
            "with the raw relational curriculum model. The program library is still bounded "
            "and this is not unrestricted high-school mathematics or high-school-level general intelligence."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and correct == queries
        and max_candidates <= 32
        and max_anchor_reads <= 128
        and max_programs == 1
        and scale_report["serialized_bytes"] <= 10_000_000
        and result["peak_process_kib"] <= 1_000_000
        and result["elapsed_seconds"] <= 120.0
    )
    (output_dir / "sparc_hs5_curriculum_programs.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-HS5-compact.model.zlib").write_bytes(model.to_bytes())
    (output_dir / "SPARC-HS5-program-bank.model.zlib").write_bytes(bank.to_bytes())
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
