from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import time

from .sparc_narrative_world import NarrativeWorldLearner

BASE = {
    "add": (["{a}は{n}を追加した", "{a}へ{n}を補給した", "{a}が{n}を獲得した"], "{n}を{a}へ追加した"),
    "sub": (["{a}は{n}を消費した", "{a}から{n}を差し引いた", "{a}は{n}を失った"], "{a}では{n}を消費した"),
    "assign": (["{a}を{n}に設定した", "{a}の値を{n}へ変更した", "{a}を{n}で固定した"], "{n}に{a}を設定した"),
    "transfer": (["{a}から{b}へ{n}を移した", "{a}は{b}へ{n}を振り分けた", "{a}から{b}に{n}を融通した"], "{n}を{a}から{b}へ移した"),
    "multiply": (["{a}を{n}倍にした", "{a}の値を{n}倍へ拡大した", "{a}は{n}倍になった"], "{n}倍に{a}を拡大した"),
    "copy": (["{a}は{b}の値を複製した", "{a}を{b}と同じ値にした", "{a}へ{b}の値を写した"], "{a}へ{b}の値を複製した"),
}
NOVEL = {
    "swap": (["{a}と{b}の値を交換した", "{a}は{b}と中身を入れ替えた", "{a}と{b}を相互に置換した"], "{b}と{a}の値を交換した"),
    "sum": (["{a}へ{b}の値を合算した", "{a}は{b}を足し合わせた", "{a}に{b}を加えて合計した"], "{a}へ{b}を合算した"),
}
DOMAINS = [
    ("青倉庫", "赤倉庫", "在庫"),
    ("東組", "西組", "得点"),
    ("温室甲", "温室乙", "温度"),
    ("口座一", "口座二", "残高"),
    ("資源月", "資源星", "数量"),
]


def observation(entity: str, prop: str, value: int, variant: int = 0) -> str:
    endings = ("だった", "である", "です")
    return f"{entity}の{prop}は{value}{endings[variant % len(endings)]}"


def execute(name: str, left: int, right: int, amount: int) -> tuple[int, int]:
    if name == "add":
        return left + amount, right
    if name == "sub":
        return left - amount, right
    if name == "assign":
        return amount, right
    if name == "transfer":
        return left - amount, right + amount
    if name == "multiply":
        return left * amount, right
    if name == "copy":
        return right, right
    if name == "swap":
        return right, left
    if name == "sum":
        return left + right, right
    raise KeyError(name)


def training_documents(operations, seed: int, count_each: int = 96):
    rng = random.Random(seed)
    documents = []
    for name, (phrases, _heldout) in operations.items():
        for index in range(count_each):
            left_name, right_name, prop = rng.choice(DOMAINS)
            while True:
                left = rng.randint(20, 80)
                right = rng.randint(10, 60)
                amount = rng.randint(2, 7)
                if name == "sub":
                    amount = min(amount, left - 1)
                next_left, next_right = execute(name, left, right, amount)
                if name in {"copy", "swap"} and left == right:
                    continue
                if name == "transfer" and (next_left == right or next_right == left):
                    continue
                break
            event = rng.choice(phrases).format(a=left_name, b=right_name, n=amount)
            parts = [
                observation(left_name, prop, left, index),
                observation(right_name, prop, right, index + 1),
                event,
                observation(left_name, prop, next_left, index + 2),
            ]
            if next_right != right or name in {"transfer", "swap"}:
                parts.append(observation(right_name, prop, next_right, index + 3))
            documents.append("。".join(parts) + "。")
    rng.shuffle(documents)
    return documents


def session(operation_names, seed: int):
    rng = random.Random(seed)
    left_name, right_name, prop = rng.choice(DOMAINS)
    left_name = f"検証{seed % 17}{left_name}"
    right_name = f"未見{seed % 19}{right_name}"
    state = (rng.randint(25, 70), rng.randint(15, 55))
    turns = [
        observation(left_name, prop, state[0]),
        observation(right_name, prop, state[1], 1),
    ]
    all_operations = {**BASE, **NOVEL}
    for name in operation_names:
        amount = rng.randint(2, 5)
        if name == "sub":
            amount = min(amount, state[0] - 1)
        event = all_operations[name][1].format(a=left_name, b=right_name, n=amount)
        turns.append(event)
        state = execute(name, state[0], state[1], amount)
    question = f"{left_name}の{prop}はいくつですか？"
    return turns, question, state[0]


def evaluate_sessions(model, count: int, names, seed: int, width) -> tuple[int, int, int]:
    correct = 0
    max_candidates = 0
    max_reads = 0
    for index in range(count):
        operations = [names[(index * 5 + step * 3) % len(names)] for step in range(width(index))]
        turns, question, expected = session(operations, seed + index)
        model.reset_session()
        for turn in turns:
            model.observe(turn)
        answer = model.observe(question)
        correct += answer.answer == expected
        max_candidates = max(max_candidates, model.last_candidates)
        max_reads = max(max_reads, model.last_reads)
    return correct, max_candidates, max_reads


def run_gate():
    started = time.perf_counter()
    model = NarrativeWorldLearner()
    base_documents = training_documents(BASE, 3101)
    base_programs = model.learn_documents(base_documents, reset=True)
    base_correct, max_candidates, max_reads = evaluate_sessions(
        model, 160, list(BASE), 5000, lambda index: 3 + index % 3
    )

    novel_documents = training_documents(NOVEL, 4102)
    total_programs = model.learn_documents(novel_documents, reset=False)
    retained, candidates, reads = evaluate_sessions(
        model, 160, list(BASE), 7000, lambda _index: 4
    )
    max_candidates = max(max_candidates, candidates)
    max_reads = max(max_reads, reads)
    mixed, candidates, reads = evaluate_sessions(
        model, 192, list(BASE) + list(NOVEL), 9000, lambda index: 4 + index % 3
    )
    max_candidates = max(max_candidates, candidates)
    max_reads = max(max_reads, reads)

    model.reset_session()
    chat = []
    for turn in (
        "会話倉庫の在庫は30だった。",
        "会話倉庫は5を追加した。",
        "さらに3を消費した。",
        "会話倉庫の在庫はいくつですか？",
    ):
        chat.append((turn, model.respond(turn)))
    chat_ok = chat[-1][1] == "会話倉庫は32です。"

    model.reset_session()
    model.observe("保全庫の在庫は44だった。")
    before = dict(model.state)
    unknown = model.observe("保全庫は静かな夜空を眺めた。")
    unknown_ok = model.state == before
    restored = NarrativeWorldLearner.from_bytes(model.to_bytes())
    restore_ok = restored.state == model.state and restored.report()["programs"] == 8
    elapsed = time.perf_counter() - started

    checks = {
        "raw_documents_only_training_api": model.report()["explicit_state_maps_supplied_to_training_api"] is False,
        "six_base_programs_discovered": base_programs == 6,
        "base_composed_answers_at_least_95_percent": base_correct / 160 >= 0.95,
        "inventory_expands_to_eight": total_programs == 8,
        "old_answers_retained_after_expansion_at_least_95_percent": retained / 160 >= 0.95,
        "mixed_novel_compositions_at_least_90_percent": mixed / 192 >= 0.90,
        "multi_turn_chat_state_exact": chat_ok,
        "unknown_event_does_not_corrupt_state": unknown_ok,
        "save_restore_preserves_world_and_programs": restore_ok,
        "bounded_candidates_at_most_12": max_candidates <= 12,
        "bounded_reads_at_most_2500": max_reads <= 2500,
        "model_under_512_kib": len(model.to_bytes()) <= 512 * 1024,
    }
    report = {
        "capability_id": "SPARC-NARRATIVE-WORLD-001",
        "training": {
            "base_documents": len(base_documents),
            "novel_documents": len(novel_documents),
            "base_programs": base_programs,
            "total_programs": total_programs,
        },
        "evaluation": {
            "base_before_expansion": base_correct,
            "base_total": 160,
            "base_after_expansion": retained,
            "retained_total": 160,
            "mixed_correct": mixed,
            "mixed_total": 192,
            "chat": chat,
            "chat_ok": chat_ok,
            "unknown_mechanism": unknown.mechanism,
            "unknown_state_preserved": unknown_ok,
        },
        "resources": {
            "serialized_bytes": len(model.to_bytes()),
            "max_candidates": max_candidates,
            "max_reads": max_reads,
            "wall_seconds": elapsed,
        },
        "model": model.report(),
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "Generated Japanese narratives with a simple observation grammar; "
            "not unrestricted reading or Japanese high-school-level intelligence."
        ),
    }
    return report, model


def render_markdown(report):
    training = report["training"]
    evaluation = report["evaluation"]
    resources = report["resources"]
    return "\n".join(
        [
            "# SPARC narrative-world experiment 001",
            "",
            f"Passed: **{report['passed']}**",
            "",
            f"- Base programs: **{training['base_programs']}**",
            f"- Expanded programs: **{training['total_programs']}**",
            f"- Base before expansion: **{evaluation['base_before_expansion']}/{evaluation['base_total']}**",
            f"- Base retained: **{evaluation['base_after_expansion']}/{evaluation['retained_total']}**",
            f"- Mixed compositions: **{evaluation['mixed_correct']}/{evaluation['mixed_total']}**",
            f"- Multi-turn chat exact: **{evaluation['chat_ok']}**",
            f"- Model bytes: **{resources['serialized_bytes']}**",
            f"- Max candidates / reads: **{resources['max_candidates']} / {resources['max_reads']}**",
            f"- Wall seconds: **{resources['wall_seconds']:.4f}**",
            "",
            report["claim_boundary"],
        ]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    report, model = run_gate()
    (output / "sparc_narrative_world_001.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "sparc_narrative_world_001.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    (output / "SPARC-narrative-world-001.model.zlib").write_bytes(model.to_bytes())
    print(render_markdown(report))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
