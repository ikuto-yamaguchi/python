from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import asdict
from pathlib import Path

import torch

from .close_obligation_energy import (
    CloseConfig,
    MambaSanRuntime,
    ObligationSettlementEnergy,
    select_by_closure,
    train_closure_head,
)


def load_jaquad(count: int, seed: int) -> list[dict]:
    from datasets import load_dataset

    dataset = load_dataset("SkelterLabsInc/JaQuAD", split="train")
    rows = []
    for row in dataset:
        context = str(row.get("context", "")).strip()
        question = str(row.get("question", "")).strip()
        answers = row.get("answers", {})
        texts = answers.get("text", []) if isinstance(answers, dict) else []
        answer = str(texts[0]).strip() if texts else ""
        if context and question and answer and len(context) <= 1800:
            rows.append({"context": context, "question": question, "answer": answer})
    random.Random(seed).shuffle(rows)
    return rows[:count]


def qa_prompt(row: dict) -> str:
    return f"文脈：{row['context']}\n質問：{row['question']}"


def closure_open(row: dict) -> str:
    return f"{qa_prompt(row)}\n回答："


def char_f1(candidate: str, reference: str) -> float:
    from collections import Counter

    a = Counter(re.sub(r"\s+", "", candidate))
    b = Counter(re.sub(r"\s+", "", reference))
    if not a or not b:
        return 0.0
    overlap = sum((a & b).values())
    if overlap == 0:
        return 0.0
    precision = overlap / sum(a.values())
    recall = overlap / sum(b.values())
    return 2 * precision * recall / (precision + recall)


def japanese_ratio(text: str) -> float:
    if not text:
        return 0.0
    count = sum(
        1
        for char in text
        if "\u3040" <= char <= "\u30ff" or "\u3400" <= char <= "\u9fff"
    )
    return count / len(text)


def generate_and_select(
    runtime: MambaSanRuntime,
    head: ObligationSettlementEnergy,
    prompt: str,
) -> dict:
    candidates = runtime.generate_candidates(prompt)
    baseline = candidates[0]["text"] if candidates else ""
    selected, scored = select_by_closure(runtime, head, prompt, candidates)
    return {
        "baseline": baseline,
        "close": selected,
        "candidates": scored,
    }


def evaluate_reading(
    runtime: MambaSanRuntime,
    head: ObligationSettlementEnergy,
    rows: list[dict],
) -> dict:
    outputs = []
    for row in rows:
        prompt = qa_prompt(row)
        generated = generate_and_select(runtime, head, prompt)
        outputs.append(
            row
            | generated
            | {
                "baseline_contains_answer": row["answer"] in generated["baseline"],
                "close_contains_answer": row["answer"] in generated["close"],
                "baseline_char_f1": char_f1(generated["baseline"], row["answer"]),
                "close_char_f1": char_f1(generated["close"], row["answer"]),
            }
        )
    return {
        "rows": outputs,
        "summary": {
            "examples": len(outputs),
            "baseline_exact": sum(row["baseline_contains_answer"] for row in outputs)
            / max(1, len(outputs)),
            "close_exact": sum(row["close_contains_answer"] for row in outputs)
            / max(1, len(outputs)),
            "baseline_char_f1": sum(row["baseline_char_f1"] for row in outputs)
            / max(1, len(outputs)),
            "close_char_f1": sum(row["close_char_f1"] for row in outputs)
            / max(1, len(outputs)),
        },
    }


def probes() -> list[dict]:
    return [
        {
            "name": "reading_and_followup",
            "turns": [
                "文脈：ミナは午前に図書館へ行き、午後に公園で友人と会った。質問：ミナが友人と会った場所はどこですか。",
                "その前に行った場所も答えてください。",
            ],
            "required": [["公園"], ["図書館"]],
        },
        {
            "name": "correction",
            "turns": [
                "答えを17ではなく23に訂正してください。",
                "さらに23ではなく31に訂正してください。",
            ],
            "required": [["23"], ["31"]],
        },
        {
            "name": "explanation",
            "turns": [
                "雨の日に道路が滑りやすくなる理由を、中学生にも分かる日本語で説明してください。",
                "要点を一文にまとめてください。",
            ],
            "required": [[], []],
        },
        {
            "name": "instruction_and_format",
            "turns": [
                "安全なパスワードの条件を、箇条書きで三つ説明してください。",
                "二つ目だけを短い一文で言い換えてください。",
            ],
            "required": [[], []],
        },
    ]


def evaluate_probes(runtime: MambaSanRuntime, head: ObligationSettlementEnergy) -> dict:
    outputs = []
    for probe in probes():
        history = ""
        turns = []
        for index, user_text in enumerate(probe["turns"]):
            prompt = user_text if not history else f"{history}\nユーザー：{user_text}"
            generated = generate_and_select(runtime, head, prompt)
            required = probe["required"][index]
            baseline_pass = all(token in generated["baseline"] for token in required)
            close_pass = all(token in generated["close"] for token in required)
            turns.append(
                {
                    "user": user_text,
                    "required": required,
                    "baseline": generated["baseline"],
                    "close": generated["close"],
                    "baseline_pass": baseline_pass,
                    "close_pass": close_pass,
                    "candidates": generated["candidates"],
                }
            )
            history = f"{prompt}\nアシスタント：{generated['close']}"
        outputs.append({"name": probe["name"], "turns": turns})
    flat = [turn for probe in outputs for turn in probe["turns"]]
    return {
        "rows": outputs,
        "summary": {
            "turns": len(flat),
            "baseline_required_pass": sum(turn["baseline_pass"] for turn in flat)
            / max(1, len(flat)),
            "close_required_pass": sum(turn["close_pass"] for turn in flat)
            / max(1, len(flat)),
            "baseline_japanese_ratio": sum(japanese_ratio(turn["baseline"]) for turn in flat)
            / max(1, len(flat)),
            "close_japanese_ratio": sum(japanese_ratio(turn["close"]) for turn in flat)
            / max(1, len(flat)),
            "changed_rate": sum(turn["baseline"] != turn["close"] for turn in flat)
            / max(1, len(flat)),
        },
    }


def load_mtbench_categories(limit: int = 2) -> list[dict]:
    from datasets import load_dataset

    rows = load_dataset("tokyotech-llm/swallow_japanese_mt_bench", split="train")
    selected = []
    seen = set()
    for row in rows:
        category = str(row["category"])
        if category in seen:
            continue
        seen.add(category)
        selected.append(dict(row))
        if len(selected) >= limit:
            break
    return selected


def evaluate_mtbench(runtime: MambaSanRuntime, head: ObligationSettlementEnergy) -> dict:
    outputs = []
    for row in load_mtbench_categories():
        turn_1, turn_2 = [str(value) for value in row["turns"]]
        first = generate_and_select(runtime, head, turn_1)
        second_prompt = (
            f"ユーザー：{turn_1}\nアシスタント：{first['close']}\nユーザー：{turn_2}"
        )
        second = generate_and_select(runtime, head, second_prompt)
        outputs.append(
            {
                "question_id": int(row["question_id"]),
                "category": str(row["category"]),
                "turn_1": turn_1,
                "baseline_1": first["baseline"],
                "close_1": first["close"],
                "turn_2": turn_2,
                "baseline_2": second["baseline"],
                "close_2": second["close"],
            }
        )
    return {"rows": outputs, "summary": {"dialogues": len(outputs)}}


def render_markdown(report: dict) -> str:
    lines = [
        "# CLOSE obligation settlement energy 001",
        "",
        "CLOSE treats the recurrent state after a user utterance as an unresolved obligation. A candidate answer is accepted when its recurrent state transition settles that obligation with low learned energy. The frozen Japanese Mamba is used only as a linguistic substrate.",
        "",
        f"- automatic candidate supported: **{report['candidate_supported']}**",
        "- high-school intelligence: **False**",
        f"- package bytes: {report['package_bytes']:,}",
        f"- closure ranking accuracy: {report['closure_training']['final']['ranking_accuracy']:.4f}",
        f"- reading baseline exact: {report['reading']['summary']['baseline_exact']:.4f}",
        f"- reading CLOSE exact: {report['reading']['summary']['close_exact']:.4f}",
        "",
        "## Communication probes",
        "",
    ]
    for probe in report["probes"]["rows"]:
        lines.append(f"### {probe['name']}")
        for turn in probe["turns"]:
            lines.extend(
                [
                    f"**User:** {turn['user']}",
                    "",
                    f"**Baseline:** {turn['baseline']}",
                    "",
                    f"**CLOSE:** {turn['close']}",
                    "",
                ]
            )
    lines.extend(["## Japanese reading comprehension", ""])
    for row in report["reading"]["rows"]:
        lines.extend(
            [
                f"**Question:** {row['question']}",
                "",
                f"**Gold:** {row['answer']}",
                "",
                f"**Baseline:** {row['baseline']}",
                "",
                f"**CLOSE:** {row['close']}",
                "",
            ]
        )
    lines.extend(["## Japanese MT-Bench transcripts", ""])
    for row in report["mtbench"]["rows"]:
        lines.extend(
            [
                f"### {row['question_id']} / {row['category']}",
                f"**User 1:** {row['turn_1']}",
                "",
                f"**Baseline 1:** {row['baseline_1']}",
                "",
                f"**CLOSE 1:** {row['close_1']}",
                "",
                f"**User 2:** {row['turn_2']}",
                "",
                f"**Baseline 2:** {row['baseline_2']}",
                "",
                f"**CLOSE 2:** {row['close_2']}",
                "",
            ]
        )
    return "\n".join(lines)


def run(output_dir: Path, cfg: CloseConfig, closure_examples: int, reading_examples: int) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime = MambaSanRuntime(cfg, output_dir / "hf-cache")
    model_info = runtime.load()
    rows = load_jaquad(closure_examples + reading_examples, cfg.seed)
    train_rows = rows[:closure_examples]
    reading_rows = rows[closure_examples : closure_examples + reading_examples]

    open_texts = [closure_open(row) for row in train_rows]
    positive_texts = [f"{closure_open(row)}{row['answer']}" for row in train_rows]
    wrong_answers = [train_rows[(index + 1) % len(train_rows)]["answer"] for index in range(len(train_rows))]
    negative_texts = [
        f"{closure_open(row)}{wrong}"
        for row, wrong in zip(train_rows, wrong_answers)
    ]
    open_states = runtime.encode_states(open_texts)
    positive_states = runtime.encode_states(positive_texts)
    negative_states = runtime.encode_states(negative_texts)
    head = ObligationSettlementEnergy(model_info["hidden_size"], cfg.closure_dim)
    closure_training = train_closure_head(
        head,
        open_states,
        positive_states,
        negative_states,
        cfg,
    )
    head.eval()

    reading = evaluate_reading(runtime, head, reading_rows)
    probe_results = evaluate_probes(runtime, head)
    mtbench = evaluate_mtbench(runtime, head)

    head_path = output_dir / "close-obligation-energy-head.pt"
    torch.save({"config": asdict(cfg), "head": head.state_dict()}, head_path)
    package_dir = output_dir / "model-package" / "mambasan"
    base_bytes = runtime.copy_package(package_dir)
    shutil_target = output_dir / "model-package" / head_path.name
    shutil_target.parent.mkdir(parents=True, exist_ok=True)
    shutil_target.write_bytes(head_path.read_bytes())
    package_bytes = base_bytes + shutil_target.stat().st_size

    reading_summary = reading["summary"]
    probe_summary = probe_results["summary"]
    supported = (
        closure_training["final"]["ranking_accuracy"] >= 0.70
        and reading_summary["close_char_f1"] > reading_summary["baseline_char_f1"]
        and probe_summary["close_required_pass"] >= probe_summary["baseline_required_pass"]
        and probe_summary["close_japanese_ratio"] >= 0.40
    )
    report = {
        "experiment": "close-obligation-energy-001",
        "principle": "Commitment-Latent Obligation Settlement Energy",
        "config": asdict(cfg),
        "model_info": model_info,
        "closure_training": closure_training,
        "reading": reading,
        "probes": probe_results,
        "mtbench": mtbench,
        "package_bytes": package_bytes,
        "candidate_supported": supported,
        "highschool_level_passed": False,
        "claim_boundary": "Actual Japanese transcripts override automatic metrics. The frozen Mamba is a linguistic substrate; only obligation-settlement energy is the new candidate principle.",
    }
    (output_dir / "close-obligation-energy-001.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "close-obligation-energy-001.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "candidate_supported": supported,
                "package_bytes": package_bytes,
                "closure": closure_training["final"],
                "reading": reading_summary,
                "probes": probe_summary,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--closure-examples", type=int, default=96)
    parser.add_argument("--reading-examples", type=int, default=6)
    parser.add_argument("--max-new-tokens", type=int, default=48)
    args = parser.parse_args()
    cfg = CloseConfig(max_new_tokens=args.max_new_tokens)
    run(args.output_dir, cfg, args.closure_examples, args.reading_examples)


if __name__ == "__main__":
    main()
