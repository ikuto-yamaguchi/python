from __future__ import annotations

import json
import resource
import statistics
import time
from pathlib import Path

from sparc_hs16.generative_interaction_grammar import DialogueExample, GenerativeInteractionGrammar, exact_or_semantic_anchor


TRAIN = [
    DialogueExample(("今日は仕事でかなり疲れた。", "上司に帰る直前で急な仕事を頼まれた。"), "それは負担が大きかったね。期限と優先順位を確認して、難しければ翌日に回せるか相談するとよさそう。"),
    DialogueExample(("友達と喧嘩した。",), "まず相手の言い分を聞いて、自分の気持ちは責めずに伝えると関係を戻しやすい。"),
    DialogueExample(("10キロ走ると後半に脚が重くなる。息は平気。",), "前半のペースを少し落とし、補給と脚の疲労を分けて試すと原因を絞りやすい。"),
    DialogueExample(("赤い箱にりんごが3個ある。青い箱へ2個移した。", "今どうなっている？"), "赤い箱に1個、青い箱に2個ある。"),
    DialogueExample(("会議は木曜の15時。", "金曜の16時に変更して。"), "会議を金曜16時へ変更する。"),
    DialogueExample(("雨が降ったので道が滑った。", "雨が降らなかったら？"), "道が滑る可能性は下がるが、別の原因があれば滑ることはある。"),
    DialogueExample(("二つの案がある。Aは速いが高い。Bは遅いが安い。", "予算を優先して計画して。"), "まずBを採用し、期限に余裕を持たせた工程を組む。遅延リスクが高ければ一部だけAを使う。"),
    DialogueExample(("資料には、植物は光を使って二酸化炭素と水から養分を作るとある。", "要点を説明して。"), "植物は光合成によって光のエネルギーを使い、二酸化炭素と水から養分を作る。"),
    DialogueExample(("名前は郁斗。", "茨城県に住んでいる。", "名前を覚えてる？"), "名前は郁斗。"),
    DialogueExample(("旅行は彼女と行く。", "訂正、妹と行く。", "誰と行く予定？"), "妹と行く予定。"),
]

# Same model, no task identifiers. Required anchors only diagnose whether the generated text
# actually closes the requested interaction; they are never provided to training or inference.
GATE = [
    ("free_dialogue", ("今日は失敗続きで落ち込んでる。",), ("失敗",)),
    ("instruction", ("メモに『牛乳を買う』と追加して。",), ("牛乳",)),
    ("reading", ("文章: 水は0度で凍り、100度で沸騰する。", "沸騰する温度は？"), ("100",)),
    ("reasoning", ("太郎は花子より速い。花子は次郎より速い。", "一番速いのは？"), ("太郎",)),
    ("planning", ("明日までに報告書と買い物を終えたい。報告書は2時間、買い物は30分。", "順番を決めて。"), ("報告書", "買い物")),
    ("causal_counterfactual", ("窓を開けたので部屋が寒くなった。", "開けなかったら？"), ("寒",)),
    ("free_description", ("静かな海辺の朝を描写して。",), ("海",)),
    ("long_dialogue", ("私は京都へ行く予定。", "土曜に出る。", "やっぱり大阪に変更。", "日曜に変更。", "どこへいつ行く？"), ("大阪", "日曜")),
    ("continual_learning", ("合言葉は銀河。覚えて。", "別の話をしよう。", "合言葉は？"), ("銀河",)),
]


def run_one(size: int, seed: int) -> dict:
    examples = (TRAIN * ((size + len(TRAIN) - 1) // len(TRAIN)))[:size]
    model = GenerativeInteractionGrammar(max_order=8, state_buckets=4096, max_edges=250_000)
    start = time.perf_counter()
    model.fit(examples, seed=seed)
    train_ms = (time.perf_counter() - start) * 1000
    outputs = []
    latencies = []
    reads = []
    passed = {}
    for index, (name, context, anchors) in enumerate(GATE):
        before = model.reads
        t0 = time.perf_counter()
        text = model.generate(context, seed=seed + index, max_chars=160)
        latencies.append((time.perf_counter() - t0) * 1000)
        reads.append(model.reads - before)
        ok = bool(text) and exact_or_semantic_anchor(text, anchors)
        passed[name] = ok
        outputs.append({"capability": name, "context": list(context), "output": text, "required_anchors": list(anchors), "passed": ok})
    return {
        "size": size,
        "seed": seed,
        "train_ms": train_ms,
        "model_bytes": model.serialized_bytes(),
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "mean_inference_ms": statistics.mean(latencies),
        "p95_inference_ms": sorted(latencies)[max(0, int(len(latencies) * .95) - 1)],
        "candidate_count": 1,
        "mean_reads": statistics.mean(reads),
        "max_reads": max(reads),
        "gate_pass_rate": sum(passed.values()) / len(passed),
        "gate": passed,
        "outputs": outputs,
    }


def main() -> None:
    sizes = (10, 30, 100, 300)
    seeds = (1, 7, 19)
    started = time.perf_counter()
    runs = [run_one(size, seed) for size in sizes for seed in seeds]
    largest = [row for row in runs if row["size"] == max(sizes)]
    report = {
        "experiment": "generative interaction grammar 001",
        "hypothesis": "raw dialogue can be compressed into reusable bounded interaction continuations that directly generate unseen Japanese responses without candidates or labels",
        "architecture": {
            "transformer": False,
            "neural_network": False,
            "backpropagation": False,
            "retrieval_augmented_generation": False,
            "external_llm": False,
            "task_branching": False,
            "answer_candidates": False,
            "variable_order_character_grammar": True,
            "bounded_dialogue_state_hash": True,
        },
        "runs": runs,
        "largest_summary": {
            "mean_gate_pass_rate": statistics.mean(row["gate_pass_rate"] for row in largest),
            "min_gate_pass_rate": min(row["gate_pass_rate"] for row in largest),
            "max_model_bytes": max(row["model_bytes"] for row in largest),
            "max_peak_rss_kib": max(row["peak_rss_kib"] for row in largest),
            "mean_train_ms": statistics.mean(row["train_ms"] for row in largest),
            "mean_inference_ms": statistics.mean(row["mean_inference_ms"] for row in largest),
            "max_reads": max(row["max_reads"] for row in largest),
            "candidate_count": 1,
        },
        "integrated_gate_passed": all(all(row["gate"].values()) for row in largest),
        "under_1gb": max(row["model_bytes"] for row in runs) < 1_000_000_000,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "total_wall_seconds": time.perf_counter() - started,
    }
    Path("generative_interaction_grammar_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Generative Interaction Grammar 実測", ""]
    for row in largest:
        lines += [f"## seed {row['seed']}", "", f"gate={row['gate_pass_rate']:.3f}, bytes={row['model_bytes']}, rss={row['peak_rss_kib']} KiB", ""]
        for item in row["outputs"]:
            lines += [f"### {item['capability']} {'PASS' if item['passed'] else 'FAIL'}", f"- 入力: {' / '.join(item['context'])}", f"- 出力: {item['output']}", ""]
    Path("generative_interaction_grammar_transcript.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
