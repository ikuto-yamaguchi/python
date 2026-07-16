from __future__ import annotations

import json
import resource
import string
import time
from pathlib import Path

from .sparc_expression import SPARCHS6Model, SparseExpressionBank
from .sparc_hs5_experiment import configured_model as configured_hs5


def configured_model() -> SPARCHS6Model:
    model = SPARCHS6Model(configured_hs5())
    lessons = [
        [
            ("1箱に8個入りの品を5箱と予備3個用意すると全部で何個ですか？", 43),
            ("1箱に6個入りの品を4箱と予備2個用意すると全部で何個ですか？", 26),
            ("1箱に7個入りの品を3箱と予備5個用意すると全部で何個ですか？", 26),
        ],
        [
            ("1200円から送料200円を引き4人で分けると1人何円ですか？", 250),
            ("900円から送料100円を引き4人で分けると1人何円ですか？", 200),
            ("1500円から送料300円を引き6人で分けると1人何円ですか？", 200),
        ],
        [
            ("縦5cm横8cmの長方形の周囲は何cmですか？", 26),
            ("縦4cm横7cmの長方形の周囲は何cmですか？", 22),
            ("縦6cm横9cmの長方形の周囲は何cmですか？", 30),
        ],
        [
            ("原価800円に20%の利益を加え送料100円を足した価格は何円ですか？", 1060),
            ("原価1000円に10%の利益を加え送料200円を足した価格は何円ですか？", 1300),
            ("原価500円に40%の利益を加え送料50円を足した価格は何円ですか？", 750),
        ],
    ]
    for examples in lessons:
        model.teach_expression(examples, max_cost=9)
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


def compound_examples(prefix: str = "") -> list[tuple[str, int]]:
    return [
        (f"{prefix}原価800円に20%の利益を加え送料100円を足した価格は何円ですか？", 1060),
        (f"{prefix}原価1000円に10%の利益を加え送料200円を足した価格は何円ですか？", 1300),
        (f"{prefix}原価500円に40%の利益を加え送料50円を足した価格は何円ですか？", 750),
    ]


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = configured_model()

    answers = {
        "conversation": model.reply("こんにちは"),
        "social": model.reply("イタリアの首都は何ですか？"),
        "hs5_equation": model.reply("6x+12=54のxは何ですか？"),
        "boxes": model.reply("1箱に9個入りの品を6箱と予備4個用意すると全部で何個ですか？"),
        "sharing": model.reply("1800円から送料300円を引き5人で分けると1人何円ですか？"),
        "perimeter": model.reply("縦7cm横10cmの長方形の周囲は何cmですか？"),
        "compound": model.reply("原価1200円に25%の利益を加え送料150円を足した価格は何円ですか？"),
    }
    restored = SPARCHS6Model.from_bytes(model.to_bytes())
    persistence = restored.reply("縦8cm横12cmの長方形の周囲は何cmですか？")

    checks = {
        "conversation_retained": answers["conversation"].text.startswith("こんにちは"),
        "raw_curriculum_retained": answers["social"].text == "ローマです。",
        "hs5_program_retained": answers["hs5_equation"].text.startswith("7です"),
        "novel_mul_add_tree": answers["boxes"].text.startswith("58です"),
        "novel_sub_div_tree": answers["sharing"].text.startswith("300です"),
        "novel_perimeter_tree": answers["perimeter"].text.startswith("34です"),
        "cost9_compound_tree": answers["compound"].text.startswith("1650です"),
        "expression_explanation": "式は" in answers["compound"].text,
        "persistence": persistence.text.startswith("40です"),
        "not_named_program_fallback": (
            answers["boxes"].mechanism == "synthesized-expression-tree"
        ),
    }

    scale_start = time.perf_counter()
    bank = SparseExpressionBank(max_schemas=20_000, max_candidates=32)
    expression = bank.teach(compound_examples(), max_cost=9)
    schema_count = 10_000
    for index in range(schema_count):
        code = _alpha_code(index)
        bank.link_surface(
            f"形式{code}:原価1円に2%の利益を加え送料3円を足した価格は何円ですか？",
            expression,
            support=3,
        )

    correct = 0
    max_candidates = 0
    max_anchor_reads = 0
    max_cost = 0
    queries = 512
    for sample in range(queries):
        index = (sample * 7919) % schema_count
        code = _alpha_code(index)
        answer = bank.solve(
            f"形式{code}:原価1200円に25%の利益を加え送料150円を足した価格は何円ですか？"
        )
        if answer is not None and answer.text.startswith("1650です"):
            correct += 1
        max_candidates = max(max_candidates, bank.last_candidates)
        max_anchor_reads = max(max_anchor_reads, bank.last_anchor_reads)
        max_cost = max(max_cost, bank.last_expression_cost)

    scale_report = bank.report()
    scale_report.update(
        {
            "linked_surface_schemas": schema_count + 1,
            "sample_queries": queries,
            "correct_queries": correct,
            "max_candidates_observed": max_candidates,
            "max_anchor_reads_observed": max_anchor_reads,
            "max_expression_cost_observed": max_cost,
            "synthesis_candidates_generated": expression.candidates_generated,
            "synthesis_semantic_states": expression.semantic_states,
            "build_and_query_seconds": time.perf_counter() - scale_start,
        }
    )

    result: dict[str, object] = {
        "capability_id": "SPARC-HS6-EXPRESSION-SYNTHESIS",
        "transformer_used": False,
        "softmax_attention_used": False,
        "growing_kv_cache_used": False,
        "dynamic_expression_synthesis": True,
        "backward_relevance_search": True,
        "shared_expression_tree": True,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "answers": {
            key: {"text": value.text, "mechanism": value.mechanism}
            for key, value in answers.items()
        },
        "compact_model": model.report(),
        "large_expression_bank": scale_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS6 synthesizes bounded arithmetic expression trees from demonstrations "
            "using answer-directed relevance search. It does not yet induce unrestricted "
            "algorithms, proofs, units or high-school-level general intelligence."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and expression.cost == 9
        and expression.semantic_states <= 2_000
        and correct == queries
        and max_candidates <= 32
        and max_anchor_reads <= 128
        and scale_report["unique_expression_trees"] == 1
        and scale_report["serialized_bytes"] <= 1_000_000
        and result["peak_process_kib"] <= 1_000_000
        and result["elapsed_seconds"] <= 120.0
    )
    (output_dir / "sparc_hs6_expression.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-HS6-compact.model.zlib").write_bytes(model.to_bytes())
    (output_dir / "SPARC-HS6-expression-bank.model.zlib").write_bytes(bank.to_bytes())
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
