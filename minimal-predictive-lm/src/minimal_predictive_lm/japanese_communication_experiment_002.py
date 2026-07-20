from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import torch

from .japanese_communication_experiment import load_mtbench, load_pairs
from .japanese_sparse_memory_model import CharVocab, Config, Pair, train_model


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


def evaluate(model, vocab, heldout, mtbench, device):
    heldout_rows = []
    for pair in heldout[:40]:
        output, tokens = model.generate(pair.prompt, vocab, device=device)
        heldout_rows.append(
            {
                "prompt": pair.prompt,
                "reference": pair.response,
                "output": output,
                "output_chars": len(tokens),
                "char_f1": char_f1(output, pair.response),
                "japanese_ratio": japanese_ratio(output),
            }
        )

    dialogues = []
    for row in mtbench[:24]:
        turn_1, turn_2 = list(row["turns"])
        response_1, tokens_1 = model.generate(str(turn_1), vocab, device=device)
        followup = (
            f"ユーザー: {turn_1}\n"
            f"アシスタント: {response_1}\n"
            f"ユーザー: {turn_2}\n"
            "アシスタント:"
        )
        response_2, tokens_2 = model.generate(followup, vocab, device=device)
        dialogues.append(
            {
                "question_id": int(row["question_id"]),
                "category": str(row["category"]),
                "turn_1": str(turn_1),
                "response_1": response_1,
                "turn_2": str(turn_2),
                "response_2": response_2,
                "response_1_chars": len(tokens_1),
                "response_2_chars": len(tokens_2),
                "followup_changed": response_1.strip() != response_2.strip(),
            }
        )

    outputs = [row["output"] for row in heldout_rows]
    dialogue_outputs = [x for row in dialogues for x in (row["response_1"], row["response_2"])]
    summary = {
        "heldout_examples": len(heldout_rows),
        "mean_char_f1": sum(row["char_f1"] for row in heldout_rows) / max(len(heldout_rows), 1),
        "mean_japanese_ratio": sum(row["japanese_ratio"] for row in heldout_rows) / max(len(heldout_rows), 1),
        "nonempty_rate": sum(int(bool(output.strip())) for output in outputs) / max(len(outputs), 1),
        "unique_rate": len(set(outputs)) / max(len(outputs), 1),
        "dialogue_count": len(dialogues),
        "followup_changed_rate": sum(int(row["followup_changed"]) for row in dialogues) / max(len(dialogues), 1),
        "dialogue_unique_rate": len(set(dialogue_outputs)) / max(len(dialogue_outputs), 1),
    }
    return {"heldout": heldout_rows, "dialogues": dialogues, "summary": summary}


def markdown(report):
    lines = [
        "# Japanese communication end-to-end 002",
        "",
        "The byte generator from experiment 001 collapsed to repeated UTF-8 fragments. This run uses Unicode characters and a fixed 16-slot source memory with top-2 retrieval.",
        "",
        f"- candidate principle supported: **{report['candidate_supported']}**",
        "- high-school intelligence: **False**",
        "",
    ]
    for name in ("sparse_plain", "sparse_cycle"):
        result = report["results"][name]
        summary = result["evaluation"]["summary"]
        lines += [
            f"## {name}",
            f"- model bytes: {result['training']['model_bytes']:,}",
            f"- validation NLL: {result['training']['valid_nll']:.4f}",
            f"- held-out character F1: {summary['mean_char_f1']:.4f}",
            f"- Japanese character ratio: {summary['mean_japanese_ratio']:.4f}",
            f"- distinct held-out outputs: {summary['unique_rate']:.4f}",
            f"- changed on follow-up: {summary['followup_changed_rate']:.4f}",
            "",
            "### Actual two-turn outputs",
            "",
        ]
        for row in result["evaluation"]["dialogues"][:10]:
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
    source_pairs = load_pairs(train_examples + valid_examples)
    pairs = [Pair(pair.prompt, pair.response) for pair in source_pairs]
    random.Random(cfg.seed).shuffle(pairs)
    train = pairs[:train_examples]
    valid = pairs[train_examples : train_examples + valid_examples]
    vocab = CharVocab.build(
        [text for pair in train for text in (pair.prompt, pair.response)], max_size=4096
    )
    mtbench = load_mtbench()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    results = {}
    for name, cycle in (("sparse_plain", False), ("sparse_cycle", True)):
        model, training = train_model(train, valid, vocab, cfg, cycle=cycle, device=device)
        evaluation = evaluate(model, vocab, valid, mtbench, device)
        checkpoint = output_dir / f"{name}.pt"
        torch.save(
            {
                "config": asdict(cfg),
                "vocab": vocab.to_dict(),
                "cycle": cycle,
                "state_dict": model.state_dict(),
            },
            checkpoint,
        )
        results[name] = {
            "training": training,
            "evaluation": evaluation,
            "checkpoint": checkpoint.name,
        }

    plain = results["sparse_plain"]["evaluation"]["summary"]
    cycle = results["sparse_cycle"]["evaluation"]["summary"]
    supported = (
        cycle["mean_char_f1"] > plain["mean_char_f1"] + 0.01
        and cycle["unique_rate"] >= plain["unique_rate"] * 0.9
        and cycle["followup_changed_rate"] >= plain["followup_changed_rate"]
        and cycle["mean_japanese_ratio"] >= 0.5
    )
    report = {
        "experiment": "japanese-communication-end-to-end-002",
        "architecture": "Unicode character recurrent generator with fixed 16-slot source memory and top-2 sparse retrieval",
        "config": asdict(cfg),
        "vocab_size": len(vocab),
        "train_pairs": len(train),
        "valid_pairs": len(valid),
        "results": results,
        "candidate_supported": supported,
        "highschool_level_passed": False,
        "claim_boundary": "The generated Japanese transcripts are the primary evidence. Fluent but irrelevant text is failure.",
    }
    (output_dir / "japanese-communication-end-to-end-002.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "japanese-communication-end-to-end-002.md").write_text(
        markdown(report), encoding="utf-8"
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--train-examples", type=int, default=5000)
    parser.add_argument("--valid-examples", type=int, default=400)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--embedding-dim", type=int, default=128)
    parser.add_argument("--hidden-dim", type=int, default=256)
    args = parser.parse_args()
    cfg = Config(
        embedding_dim=args.embedding_dim,
        hidden_dim=args.hidden_dim,
        epochs=args.epochs,
    )
    report = run(args.output_dir, cfg, args.train_examples, args.valid_examples)
    print(json.dumps({
        "supported": report["candidate_supported"],
        "highschool": report["highschool_level_passed"],
        "plain": report["results"]["sparse_plain"]["evaluation"]["summary"],
        "cycle": report["results"]["sparse_cycle"]["evaluation"]["summary"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
