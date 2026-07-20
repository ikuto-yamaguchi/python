from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import torch

from .japanese_dialogue_model import Config, Pair, train_model


def load_pairs(limit: int) -> list[Pair]:
    from datasets import load_dataset

    dataset = load_dataset("llm-jp/databricks-dolly-15k-ja", split="train")
    pairs: list[Pair] = []
    for row in dataset:
        instruction = str(row.get("instruction", "")).strip()
        context = str(row.get("context", "")).strip()
        response = str(row.get("response", "")).strip()
        prompt = f"資料:\n{context}\n\n指示:\n{instruction}" if context else instruction
        if prompt and response:
            pairs.append(Pair(prompt, response))
            if len(pairs) >= limit:
                break
    return pairs


def load_mtbench() -> list[dict]:
    from datasets import load_dataset

    return [
        dict(row)
        for row in load_dataset(
            "tokyotech-llm/swallow_japanese_mt_bench", split="train"
        )
    ]


def char_f1(candidate: str, reference: str) -> float:
    if not candidate or not reference:
        return 0.0
    overlap = sum((Counter(candidate) & Counter(reference)).values())
    if not overlap:
        return 0.0
    precision = overlap / len(candidate)
    recall = overlap / len(reference)
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


def evaluate(model, heldout, mtbench, device):
    heldout_rows = []
    for pair in heldout[:40]:
        output, valid, tokens = model.generate(pair.prompt, device=device)
        heldout_rows.append(
            {
                "prompt": pair.prompt,
                "reference": pair.response,
                "output": output,
                "utf8_valid": valid,
                "output_bytes": len(tokens),
                "char_f1": char_f1(output, pair.response),
                "japanese_ratio": japanese_ratio(output),
            }
        )

    dialogues = []
    for row in mtbench[:24]:
        turn_1, turn_2 = list(row["turns"])
        response_1, valid_1, tokens_1 = model.generate(str(turn_1), device=device)
        followup = (
            f"ユーザー: {turn_1}\n"
            f"アシスタント: {response_1}\n"
            f"ユーザー: {turn_2}\n"
            "アシスタント:"
        )
        response_2, valid_2, tokens_2 = model.generate(followup, device=device)
        dialogues.append(
            {
                "question_id": int(row["question_id"]),
                "category": str(row["category"]),
                "turn_1": str(turn_1),
                "response_1": response_1,
                "turn_2": str(turn_2),
                "response_2": response_2,
                "utf8_valid": valid_1 and valid_2,
                "response_1_bytes": len(tokens_1),
                "response_2_bytes": len(tokens_2),
                "followup_changed": response_1.strip() != response_2.strip(),
            }
        )

    outputs = [row["output"] for row in heldout_rows]
    dialogue_outputs = [x for row in dialogues for x in (row["response_1"], row["response_2"])]
    summary = {
        "heldout_examples": len(heldout_rows),
        "mean_char_f1": sum(row["char_f1"] for row in heldout_rows) / max(len(heldout_rows), 1),
        "mean_japanese_ratio": sum(row["japanese_ratio"] for row in heldout_rows) / max(len(heldout_rows), 1),
        "utf8_valid_rate": sum(int(row["utf8_valid"]) for row in heldout_rows) / max(len(heldout_rows), 1),
        "nonempty_rate": sum(int(bool(x.strip())) for x in outputs) / max(len(outputs), 1),
        "unique_rate": len(set(outputs)) / max(len(outputs), 1),
        "dialogue_count": len(dialogues),
        "dialogue_utf8_valid_rate": sum(int(row["utf8_valid"]) for row in dialogues) / max(len(dialogues), 1),
        "followup_changed_rate": sum(int(row["followup_changed"]) for row in dialogues) / max(len(dialogues), 1),
        "dialogue_unique_rate": len(set(dialogue_outputs)) / max(len(dialogue_outputs), 1),
    }
    return {"heldout": heldout_rows, "dialogues": dialogues, "summary": summary}


def render_markdown(report: dict) -> str:
    lines = [
        "# Japanese communication end-to-end 001",
        "",
        "Primary evidence is the generated Japanese transcript below, not a structured-state score.",
        "",
        f"- dialogue-cycle supported: **{report['dialogue_cycle_principle_supported']}**",
        "- high-school intelligence: **False**",
        "",
    ]
    for name in ("plain_seq2seq", "dialogue_cycle"):
        result = report["results"][name]
        summary = result["evaluation"]["summary"]
        lines += [
            f"## {name}",
            f"- model bytes: {result['training']['model_bytes']:,}",
            f"- validation NLL: {result['training']['valid_answer_nll']:.4f}",
            f"- held-out character F1: {summary['mean_char_f1']:.4f}",
            f"- UTF-8 valid: {summary['utf8_valid_rate']:.4f}",
            f"- distinct outputs: {summary['unique_rate']:.4f}",
            f"- changed on follow-up: {summary['followup_changed_rate']:.4f}",
            "",
            "### Actual two-turn outputs",
            "",
        ]
        for row in result["evaluation"]["dialogues"][:8]:
            lines += [
                f"**User 1:** {row['turn_1']}",
                "",
                f"**Model 1:** {row['response_1']}",
                "",
                f"**User 2:** {row['turn_2']}",
                "",
                f"**Model 2:** {row['response_2']}",
                "",
            ]
    return "\n".join(lines)


def run(output_dir: Path, cfg: Config, train_examples: int, valid_examples: int):
    output_dir.mkdir(parents=True, exist_ok=True)
    pairs = load_pairs(train_examples + valid_examples)
    random.Random(cfg.seed).shuffle(pairs)
    train_pairs = pairs[:train_examples]
    valid_pairs = pairs[train_examples : train_examples + valid_examples]
    mtbench = load_mtbench()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    results = {}
    for name, cycle in (("plain_seq2seq", False), ("dialogue_cycle", True)):
        model, training = train_model(
            train_pairs, valid_pairs, cfg, cycle=cycle, device=device
        )
        evaluation = evaluate(model, valid_pairs, mtbench, device)
        checkpoint = output_dir / f"{name}.pt"
        torch.save(
            {"config": asdict(cfg), "cycle": cycle, "state_dict": model.state_dict()},
            checkpoint,
        )
        results[name] = {
            "training": training,
            "evaluation": evaluation,
            "checkpoint": checkpoint.name,
        }

    plain = results["plain_seq2seq"]["evaluation"]["summary"]
    cycle = results["dialogue_cycle"]["evaluation"]["summary"]
    supported = (
        cycle["mean_char_f1"] > plain["mean_char_f1"] + 0.01
        and cycle["unique_rate"] >= max(0.5, plain["unique_rate"] * 0.9)
        and cycle["utf8_valid_rate"] >= 0.95
        and cycle["followup_changed_rate"] >= plain["followup_changed_rate"]
    )
    report = {
        "experiment": "japanese-communication-end-to-end-001",
        "architecture": "fixed-memory recurrent byte generator with shared bidirectional dialogue-cycle training",
        "config": asdict(cfg),
        "train_pairs": len(train_pairs),
        "valid_pairs": len(valid_pairs),
        "mtbench_dialogues": 24,
        "results": results,
        "dialogue_cycle_principle_supported": supported,
        "highschool_level_passed": False,
        "claim_boundary": "Generated Japanese transcripts are primary. Automatic metrics are diagnostics and cannot establish intelligence.",
    }
    (output_dir / "japanese-communication-end-to-end-001.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "japanese-communication-end-to-end-001.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--train-examples", type=int, default=3000)
    parser.add_argument("--valid-examples", type=int, default=300)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--embedding-dim", type=int, default=96)
    parser.add_argument("--hidden-dim", type=int, default=192)
    args = parser.parse_args()
    cfg = Config(
        embedding_dim=args.embedding_dim,
        hidden_dim=args.hidden_dim,
        batch_size=args.batch_size,
        epochs=args.epochs,
    )
    report = run(args.output_dir, cfg, args.train_examples, args.valid_examples)
    print(
        json.dumps(
            {
                "supported": report["dialogue_cycle_principle_supported"],
                "highschool": report["highschool_level_passed"],
                "plain": report["results"]["plain_seq2seq"]["evaluation"]["summary"],
                "cycle": report["results"]["dialogue_cycle"]["evaluation"]["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
