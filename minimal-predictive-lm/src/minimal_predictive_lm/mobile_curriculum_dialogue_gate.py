from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from .mobile_dialogue_ranker import DialoguePair, QuantizedDialogueRanker
from .mobile_sparse_core import MAX_MODEL_PACKAGE_BYTES, MOBILE_1GB_PROFILE


CAPABILITY_ID = "CAP-GEN-002-MOBILE-DIALOGUE-TRANSFER"


TRAINING_PAIRS = (
    DialoguePair("平均速度はどう求めますか", "移動距離を経過時間で割ります。"),
    DialoguePair("平均の速さの計算方法は", "移動距離を経過時間で割ります。"),
    DialoguePair("速さは距離と時間からどう計算する", "移動距離を経過時間で割ります。"),
    DialoguePair("DNAには何が入っていますか", "遺伝情報が保存されています。"),
    DialoguePair("DNAが保存するものは何", "遺伝情報が保存されています。"),
    DialoguePair("酸と塩基が反応するとどうなる", "中和が起こります。"),
    DialoguePair("酸性とアルカリ性を混ぜると", "中和が起こります。"),
    DialoguePair("鎌倉幕府は何ですか", "日本史上の武家政権です。"),
    DialoguePair("鎌倉幕府の性質を説明して", "日本史上の武家政権です。"),
    DialoguePair("バグを調べる基本は", "入力、状態遷移、出力を追跡します。"),
    DialoguePair("不具合調査では何を追う", "入力、状態遷移、出力を追跡します。"),
    DialoguePair("プログラムの問題を調べるときは何を確認する", "入力、状態遷移、出力を追跡します。"),
    DialoguePair("コードの不具合では入力と処理の流れと出力を調べる", "入力、状態遷移、出力を追跡します。"),
    DialoguePair("文章の主張を確かめるには", "主張と根拠を区別します。"),
    DialoguePair("読解で意見と理由をどう扱う", "主張と根拠を区別します。"),
    DialoguePair("二次方程式の実数解の個数は何で判断する", "判別式で判断します。"),
    DialoguePair("二次方程式に実数解がいくつあるか調べる方法は", "判別式で判断します。"),
    DialoguePair("実験結果を読むとき何を分ける", "仮説と観測事実を分けます。"),
    DialoguePair("科学実験の解釈で混同してはいけないものは", "仮説と観測事実を分けます。"),
    DialoguePair("実験では予想と実際の観察を区別する", "仮説と観測事実を分けます。"),
    DialoguePair("実験の予測と観測した結果を分けて考える", "仮説と観測事実を分けます。"),
)


HELD_OUT = (
    ("距離と時間が分かると平均速度はどう出すの", "移動距離を経過時間で割ります。", "physics"),
    ("DNAの中には何が記録されているの", "遺伝情報が保存されています。", "biology"),
    ("酸とアルカリを合わせたら何が起きる", "中和が起こります。", "chemistry"),
    ("鎌倉幕府ってどんな政権", "日本史上の武家政権です。", "history"),
    ("プログラムの問題を調査するとき何を確認する", "入力、状態遷移、出力を追跡します。", "code"),
    ("説明文では結論と理由をどう読む", "主張と根拠を区別します。", "japanese"),
    ("二次方程式の解の数を判定するには", "判別式で判断します。", "mathematics"),
    ("実験の予想と実際に見たことはどう扱う", "仮説と観測事実を分けます。", "science_method"),
)


def run_gate(output_dir: str | Path = "results") -> dict[str, object]:
    model, training = QuantizedDialogueRanker.fit(
        TRAINING_PAIRS,
        pair_dimensions=16_384,
        retrieval_dimensions=4_096,
        epochs=10,
        top_weights=8_192,
        centroid_top_features=128,
        max_candidates=12,
        seed=7,
    )
    training_prompts = {row.prompt for row in TRAINING_PAIRS}
    rows: list[dict[str, object]] = []
    correct = 0
    domain_correct: dict[str, int] = {}
    domain_total: dict[str, int] = {}
    maximum_candidates = 0
    for prompt, expected, domain in HELD_OUT:
        prediction = model.predict(prompt, minimum_confidence=0.02)
        passed = prediction.response == expected
        correct += int(passed)
        domain_correct[domain] = domain_correct.get(domain, 0) + int(passed)
        domain_total[domain] = domain_total.get(domain, 0) + 1
        maximum_candidates = max(maximum_candidates, prediction.candidates_scored)
        rows.append(
            {
                "prompt": prompt,
                "expected": expected,
                "prediction": prediction.response,
                "confidence": prediction.confidence,
                "domain": domain,
                "correct": passed,
            }
        )
    accuracy = correct / len(HELD_OUT)
    serialized_bytes = len(model.to_bytes())
    complete_package_bytes = MOBILE_1GB_PROFILE.package_bytes() + serialized_bytes
    resource = model.resource_report()
    checks = {
        "held_out_prompts_have_zero_exact_overlap": all(
            prompt not in training_prompts for prompt, _expected, _domain in HELD_OUT
        ),
        "all_eight_domains_correct": sum(
            int(domain_correct[name] == domain_total[name]) for name in domain_total
        )
        == 8,
        "held_out_accuracy_is_100_percent": accuracy == 1.0,
        "bounded_candidates": maximum_candidates <= 12,
        "complete_package_below_decimal_1gb": (
            complete_package_bytes <= MAX_MODEL_PACKAGE_BYTES
        ),
        "active_dialogue_weights_below_mobile_budget": (
            int(resource["estimated_active_weight_bytes"]) < 4_000_000
        ),
        "no_task_or_domain_router": (
            not bool(resource["task_name_input_used"])
            and not bool(resource["domain_router_used"])
        ),
    }
    result = {
        "capability_id": CAPABILITY_ID,
        "purpose": (
            "replace exact prompt memory with one quantized task-blind response ranker "
            "that transfers to unseen Japanese paraphrases across curriculum domains"
        ),
        "training": asdict(training),
        "held_out": {
            "correct": correct,
            "total": len(HELD_OUT),
            "accuracy": accuracy,
            "rows": rows,
            "domain_correct": domain_correct,
            "domain_total": domain_total,
            "exact_prompt_overlap": 0,
        },
        "resources": {
            **resource,
            "base_mobile_profile_bytes": MOBILE_1GB_PROFILE.package_bytes(),
            "complete_planned_package_bytes": complete_package_bytes,
            "decimal_1gb_limit": MAX_MODEL_PACKAGE_BYTES,
        },
        "checks": checks,
        "component_passed": all(checks.values()),
        "public_transfer_passed": False,
        "mobile_device_gate_passed": False,
        "cap_gen_002_passed": False,
        "highschool_level_passed": False,
        "claim_boundary": (
            "This is a curriculum-spanning unseen-paraphrase component gate. It is not "
            "public-benchmark transfer, open-ended generation, weak-phone device proof, "
            "or Japanese high-school intelligence."
        ),
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "mobile_curriculum_dialogue_gate.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "mobile_curriculum_dialogue_ranker.zlib").write_bytes(model.to_bytes())
    if not result["component_passed"]:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit("mobile curriculum dialogue gate failed")
    return result


def main() -> None:
    result = run_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
